from __future__ import annotations
import base64
import json
import re
from pathlib import Path
from typing import Any

import aiohttp

from app.core.config import Settings, resolve_llm_mode

_RECOG_PROMPT = """请分析这张校园失物图片，只返回一个 JSON 对象，不要其他文字：
{"category":"物品类别","features":"特征描述","text":"图中文字或空字符串","confidence":0.0到1.0的小数}
"""


def _mime_for_path(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    return "image/jpeg"


class RecognitionService:
    async def recognize(self, image_path: str) -> dict[str, Any]:
        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(image_path)
        img_b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
        # 每次请求拉取密钥等；模式以 backend/.env 为准，避免系统环境变量覆盖 .env 仍走 Ollama
        cfg = Settings()
        mode = resolve_llm_mode()
        if mode == "remote":
            return await self._recognize_remote(cfg, path, img_b64)
        if mode == "local":
            return await self._recognize_local(cfg, img_b64)
        return self._fallback(f"LLM_MODE 无效: {mode}，请使用 local 或 remote")

    async def _recognize_local(self, cfg: Settings, img_b64: str) -> dict[str, Any]:
        ollama_url = cfg.OLLAMA_URL.rstrip("/")
        model = cfg.OLLAMA_MODEL
        payload: dict[str, Any] = {
            "model": model,
            "prompt": _RECOG_PROMPT,
            "images": [img_b64],
            "stream": False,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{ollama_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        return self._fallback(f"Ollama HTTP {resp.status}: {text[:200]}")
                    raw = await resp.json()
        except Exception as e:
            return self._fallback(str(e))

        text = raw.get("response", "") or ""
        return self._parse_text(text)

    async def _recognize_remote(self, cfg: Settings, path: Path, img_b64: str) -> dict[str, Any]:
        base = (cfg.REMOTE_LLM_BASE_URL or "").strip().rstrip("/")
        key = (cfg.REMOTE_LLM_API_KEY or "").strip()
        model = (cfg.REMOTE_LLM_MODEL or "").strip()
        if not base or not key or not model:
            return self._fallback(
                "远程模型未配置完整：请在 .env 中设置 REMOTE_LLM_BASE_URL、REMOTE_LLM_API_KEY、REMOTE_LLM_MODEL"
            )

        data_url = f"data:{_mime_for_path(path)};base64,{img_b64}"
        url = f"{base}/chat/completions"
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        body: dict[str, Any] = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _RECOG_PROMPT},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            "temperature": 0.2,
            "max_tokens": 1024,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=body, headers=headers, timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    raw_text = await resp.text()
                    if resp.status != 200:
                        return self._fallback(f"远程模型 HTTP {resp.status}: {raw_text[:300]}")
                    try:
                        raw = json.loads(raw_text)
                    except json.JSONDecodeError:
                        return self._fallback("远程模型返回非 JSON", raw_text=raw_text[:500])
        except Exception as e:
            return self._fallback(str(e))

        choices = raw.get("choices") or []
        if not choices:
            return self._fallback("远程模型无 choices", raw_text=str(raw)[:500])
        msg = choices[0].get("message") or {}
        content = msg.get("content") or ""
        if isinstance(content, list):
            parts: list[str] = []
            for p in content:
                if isinstance(p, dict) and p.get("type") == "text":
                    parts.append(str(p.get("text") or ""))
                elif isinstance(p, str):
                    parts.append(p)
            content = "".join(parts)
        return self._parse_text(str(content))

    def _parse_text(self, text: str) -> dict[str, Any]:
        text = text.strip()
        try:
            obj = json.loads(text)
            return self._normalize(obj)
        except json.JSONDecodeError:
            pass
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                obj = json.loads(m.group())
                return self._normalize(obj)
            except json.JSONDecodeError:
                pass
        return self._fallback("无法解析模型输出", raw_text=text[:500])

    def _normalize(self, obj: dict[str, Any]) -> dict[str, Any]:
        conf = obj.get("confidence", 0.5)
        try:
            conf = float(conf)
        except (TypeError, ValueError):
            conf = 0.5
        return {
            "category": str(obj.get("category", "未知")),
            "features": str(obj.get("features", "")),
            "text": str(obj.get("text", "")),
            "confidence": max(0.0, min(1.0, conf)),
        }

    def _fallback(self, reason: str, raw_text: str = "") -> dict[str, Any]:
        return {
            "category": "未知",
            "features": "",
            "text": "",
            "confidence": 0.0,
            "error": reason,
            "raw": raw_text,
        }


recognition_service = RecognitionService()
