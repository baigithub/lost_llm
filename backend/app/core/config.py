from __future__ import annotations
from pathlib import Path
import secrets
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# 固定为 backend/.env，避免从仓库根目录启动 uvicorn 时 cwd 不对、读不到 .env 而退回默认 LLM_MODE=local
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _BACKEND_ROOT / ".env"


def read_llm_mode_from_dotenv_file() -> str | None:
    """只解析 backend/.env 里的 LLM_MODE，不读系统环境变量。"""
    if not _ENV_FILE.is_file():
        return None
    try:
        text = _ENV_FILE.read_text(encoding="utf-8")
    except OSError:
        return None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        if key.strip().upper() != "LLM_MODE":
            continue
        v = val.strip().strip('"').strip("'")
        if not v:
            return None
        return v.strip().lower()
    return None


def resolve_llm_mode() -> str:
    """图像识别用：.env 里的 LLM_MODE 优先于系统环境变量。

    pydantic-settings 默认「环境变量覆盖 .env」，易导致本机 export 了 LLM_MODE=local 时，
    即使 .env 写了 remote 仍走 Ollama。
    """
    from_file = read_llm_mode_from_dotenv_file()
    if from_file in ("local", "remote"):
        return from_file
    return Settings().LLM_MODE.strip().lower()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "智能校园失物招领系统"
    API_V1_PREFIX: str = "/api/v1"

    # MySQL：Docker 中容器名为 gfms 时，若后端在宿主机运行请用 127.0.0.1 + 映射端口；
    # 若后端也在同一 Docker 网络中运行，可将 MYSQL_HOST 设为 gfms
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DATABASE: str = "lost_found"

    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALGORITHM: str = "HS256"

    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = 10
    PUBLIC_BASE_URL: str = "http://127.0.0.1:8000"

    # 图像识别用大模型：local=本机 Ollama；remote=OpenAI 兼容 Chat Completions（需视觉能力）
    LLM_MODE: str = "local"
    OLLAMA_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen2.5-vl:7b"
    REMOTE_LLM_BASE_URL: str = ""
    REMOTE_LLM_API_KEY: str = ""
    REMOTE_LLM_MODEL: str = ""

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"
        )


def get_settings() -> Settings:
    """读取环境变量与 backend/.env（路径与进程 cwd 无关）。

    每次后端进程启动都会生成新的 SECRET_KEY，使历史 JWT 立即失效。
    """
    s = Settings()
    s.SECRET_KEY = secrets.token_urlsafe(48)
    return s


# 进程首次 import 时的快照；数据库等仍用此对象。图像识别改为每次单独 Settings()，避免改 .env 仍走 Ollama。
settings = get_settings()
