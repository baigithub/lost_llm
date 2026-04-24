<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { Key, Monitor } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const u = useUserStore()
const username = ref('')
const password = ref('')
const loading = ref(false)

async function submit() {
  loading.value = true
  try {
    await u.login(username.value, password.value)
    const red = (route.query.redirect as string) || '/home'
    router.push(red)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="grid-bg" aria-hidden="true" />
    <div class="glow glow-a" aria-hidden="true" />
    <div class="glow glow-b" aria-hidden="true" />
    <div class="scan-line" aria-hidden="true" />

    <div class="shell">
      <aside class="hero">
        <div class="hero-badge">
          <el-icon><Monitor /></el-icon>
          <span>Smart Campus · Lost & Found</span>
        </div>
        <h1 class="hero-title">
          <span class="gradient-text">智能失物招领</span>
          <br />
          <span class="sub">图像识别 · 安全认领 · 一站管理</span>
        </h1>
        <p class="hero-desc">
          基于多模态识别与 Web 技术，为校园提供低门槛发布、可追溯认领与统一数据看板。
        </p>
        <div class="hero-stats">
          <div class="stat">
            <span class="num font-mono">AI</span>
            <span class="lbl">本地识别</span>
          </div>
          <div class="stat">
            <span class="num font-mono">JWT</span>
            <span class="lbl">安全会话</span>
          </div>
          <div class="stat">
            <span class="num font-mono">RBAC</span>
            <span class="lbl">权限体系</span>
          </div>
        </div>
      </aside>

      <section class="panel">
        <div class="card-glass">
          <div class="card-head">
            <div class="logo-ring">
              <el-icon :size="26"><Key /></el-icon>
            </div>
            <h2>账户登录</h2>
            <p class="muted">使用学号 / 工号与密码进入系统</p>
          </div>

          <el-form class="form" label-position="top" size="large" @submit.prevent="submit">
            <el-form-item label="学号 / 用户名">
              <el-input
                v-model="username"
                autocomplete="username"
                placeholder="请输入账号"
                class="input-tech"
              />
            </el-form-item>
            <el-form-item label="密码">
              <el-input
                v-model="password"
                type="password"
                autocomplete="current-password"
                placeholder="请输入密码"
                show-password
                class="input-tech"
                @keyup.enter="submit"
              />
            </el-form-item>
            <el-button
              class="btn-primary-tech"
              native-type="submit"
              :loading="loading"
            >
              {{ loading ? '验证中…' : '进入系统' }}
            </el-button>
          </el-form>

          <div class="links">
            <router-link to="/register">注册账号</router-link>
            <span class="dot">·</span>
            <router-link to="/home">返回门户首页</router-link>
          </div>
        </div>
        <p class="foot-note">© 校园失物招领平台 · 数据本地可控</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.font-mono {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
}

.login-page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  background: radial-gradient(ellipse 120% 80% at 50% -20%, rgba(56, 189, 248, 0.12), transparent),
    linear-gradient(165deg, #070b14 0%, #0c1222 45%, #0a1628 100%);
  color: #e2e8f0;
}

.grid-bg {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(56, 189, 248, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.06) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse 70% 60% at 50% 40%, black 20%, transparent 70%);
  pointer-events: none;
}

.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.45;
  pointer-events: none;
}
.glow-a {
  width: 420px;
  height: 420px;
  top: -120px;
  right: -80px;
  background: #0891b2;
}
.glow-b {
  width: 360px;
  height: 360px;
  bottom: -100px;
  left: -60px;
  background: #4f46e5;
}

.scan-line {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    transparent 0%,
    rgba(34, 211, 238, 0.03) 48%,
    rgba(34, 211, 238, 0.06) 50%,
    rgba(34, 211, 238, 0.03) 52%,
    transparent 100%
  );
  background-size: 100% 220%;
  animation: scan 11s linear infinite;
  pointer-events: none;
  opacity: 0.7;
}

@keyframes scan {
  0% {
    background-position: 0 -80%;
  }
  100% {
    background-position: 0 180%;
  }
}

.shell {
  position: relative;
  z-index: 1;
  max-width: 1080px;
  margin: 0 auto;
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 48px;
  align-items: center;
  padding: 48px 28px;
  box-sizing: border-box;
}

@media (max-width: 900px) {
  .shell {
    grid-template-columns: 1fr;
    padding: 32px 20px 48px;
  }
  .hero {
    text-align: center;
  }
  .hero-stats {
    justify-content: center;
  }
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #67e8f9;
  border: 1px solid rgba(34, 211, 238, 0.35);
  background: rgba(8, 145, 178, 0.12);
  margin-bottom: 24px;
}

.hero-title {
  margin: 0 0 16px;
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.gradient-text {
  background: linear-gradient(120deg, #67e8f9 0%, #a5b4fc 45%, #f0abfc 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hero .sub {
  font-size: 15px;
  font-weight: 500;
  color: #94a3b8;
  letter-spacing: 0.12em;
}

.hero-desc {
  margin: 20px 0 28px;
  max-width: 420px;
  font-size: 14px;
  line-height: 1.75;
  color: #94a3b8;
}

.hero-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.stat {
  padding: 12px 18px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.15);
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(8px);
}
.stat .num {
  display: block;
  font-size: 15px;
  font-weight: 600;
  color: #22d3ee;
  letter-spacing: 0.06em;
}
.stat .lbl {
  font-size: 12px;
  color: #64748b;
}

.panel {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.card-glass {
  width: 100%;
  max-width: 520px;
  padding: 42px 36px 32px;
  border-radius: 20px;
  background: linear-gradient(145deg, rgba(30, 41, 59, 0.75) 0%, rgba(15, 23, 42, 0.85) 100%);
  border: 1px solid rgba(56, 189, 248, 0.18);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.04) inset, 0 24px 48px -12px rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(16px);
}

.card-head {
  text-align: center;
  margin-bottom: 28px;
}

.logo-ring {
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.2), rgba(99, 102, 241, 0.25));
  border: 1px solid rgba(34, 211, 238, 0.35);
  color: #67e8f9;
}

.card-head h2 {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 600;
  color: #f1f5f9;
}

.muted {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}

.form :deep(.el-form-item__label) {
  color: #94a3b8;
  font-weight: 500;
}

.input-tech :deep(.el-input__wrapper) {
  background: #eef2f6 !important;
  box-shadow: 0 0 0 1px rgba(15, 23, 42, 0.12) inset !important;
  border-radius: 14px !important;
  min-height: 46px;
  padding: 0 14px !important;
}
.input-tech :deep(.el-input__inner) {
  color: #0f172a;
  background: transparent !important;
}
.input-tech :deep(.el-input__inner::placeholder) {
  color: #64748b;
}
.input-tech :deep(.el-input__prefix),
.input-tech :deep(.el-input__suffix) {
  color: #64748b;
}
.input-tech :deep(.el-input__wrapper:hover),
.input-tech :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px rgba(15, 23, 42, 0.35) inset, 0 0 0 4px rgba(148, 163, 184, 0.18) !important;
}

.btn-primary-tech {
  width: 100%;
  height: 46px;
  margin-top: 8px;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.06em;
  background: linear-gradient(180deg, #1f2937 0%, #111827 100%) !important;
  color: #f8fafc !important;
  box-shadow: 0 10px 26px -12px rgba(0, 0, 0, 0.55);
  transition: transform 0.15s ease, box-shadow 0.2s ease;
}
.btn-primary-tech:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 34px -14px rgba(0, 0, 0, 0.65);
}
.btn-primary-tech:active {
  transform: translateY(0px);
}
.btn-primary-tech :deep(.el-icon),
.btn-primary-tech :deep(.el-loading-spinner),
.btn-primary-tech :deep(.el-loading-spinner .circular) {
  color: #f8fafc !important;
}

.links {
  margin-top: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 13px;
}
.links a {
  color: #67e8f9;
  text-decoration: none;
  transition: opacity 0.15s;
}
.links a:hover {
  opacity: 0.85;
  text-decoration: underline;
}
.dot {
  color: #475569;
}

.foot-note {
  margin-top: 28px;
  font-size: 12px;
  color: #475569;
  text-align: center;
}
</style>
