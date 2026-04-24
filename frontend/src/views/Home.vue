<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchItems, fetchHomeListPageSize, onlineItem } from '@/api/items'
import { getToken } from '@/api/http'
import { useUserStore } from '@/stores/user'
import {
  Search,
  Location,
  PictureFilled,
  Upload,
  User,
  Setting,
  Right,
  SwitchButton,
} from '@element-plus/icons-vue'

const router = useRouter()
const user = useUserStore()
const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const kw = ref('')
const type = ref<string>('found')
const loading = ref(false)
const loadingMore = ref(false)
const sentinel = ref<HTMLElement | null>(null)
let scrollObserver: IntersectionObserver | null = null

const noMore = computed(() => total.value > 0 && list.value.length >= total.value)

function imgUrl(u: string) {
  if (!u) return ''
  if (u.startsWith('http')) return u
  return u
}

function isPartialBlur(it: any) {
  return it?.image_mask_mode === 'partial'
}

function isFullBlur(it: any) {
  return it?.image_mask_mode === 'full' || (it?.privacy_masked === true && !it?.image_mask_mode)
}

const clearWindowPositions = [
  'circle(18% at 50% 54%)', // 中间
  'circle(18% at 28% 30%)', // 左上
  'circle(18% at 72% 30%)', // 右上
  'circle(18% at 28% 74%)', // 左下
  'circle(18% at 72% 74%)', // 右下
]

function hashKey(s: string) {
  let h = 0
  for (let i = 0; i < s.length; i += 1) {
    h = (h * 31 + s.charCodeAt(i)) >>> 0
  }
  return h
}

function partialWindowStyle(it: any) {
  const seed = `${it?.id ?? ''}|${it?.images?.[0]?.image_url ?? ''}`
  const idx = hashKey(seed) % clearWindowPositions.length
  return { clipPath: clearWindowPositions[idx] }
}

function logout() {
  user.logout()
  router.push('/login')
}

async function relistItem(itemId: number) {
  await onlineItem(itemId)
  await loadFirst()
}

async function fetchPageSize() {
  try {
    const data = (await fetchHomeListPageSize()) as { page_size: number }
    if (data?.page_size) pageSize.value = data.page_size
  } catch {
    pageSize.value = 20
  }
}

async function loadFirst() {
  if (loading.value) return
  loading.value = true
  page.value = 1
  try {
    const data = (await fetchItems({
      page: 1,
      page_size: pageSize.value,
      keyword: kw.value || undefined,
      type: type.value,
    })) as { total: number; items: any[] }
    total.value = data.total
    list.value = data.items
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (noMore.value || loadingMore.value || loading.value) return
  const next = page.value + 1
  loadingMore.value = true
  try {
    const data = (await fetchItems({
      page: next,
      page_size: pageSize.value,
      keyword: kw.value || undefined,
      type: type.value,
    })) as { total: number; items: any[] }
    total.value = data.total
    if (data.items.length) {
      list.value = [...list.value, ...data.items]
      page.value = next
    }
  } finally {
    loadingMore.value = false
  }
}

function bindScrollObserver() {
  scrollObserver?.disconnect()
  scrollObserver = null
  if (!sentinel.value) return
  scrollObserver = new IntersectionObserver(
    (entries) => {
      if (entries[0]?.isIntersecting) void loadMore()
    },
    { root: null, rootMargin: '120px', threshold: 0 },
  )
  scrollObserver.observe(sentinel.value)
}

onMounted(async () => {
  await fetchPageSize()
  await loadFirst()
  await nextTick()
  bindScrollObserver()
})

onUnmounted(() => scrollObserver?.disconnect())
</script>

<template>
  <div class="home-page">
    <div class="ambient" aria-hidden="true" />
    <header class="top-nav">
      <div class="nav-inner">
        <div class="brand" @click="router.push('/home')">
          <span class="brand-icon" />
          <div class="brand-text">
            <span class="name">LostLink</span>
            <span class="tag">智能失物招领</span>
          </div>
        </div>
        <div class="nav-actions">
          <el-input
            v-model="kw"
            class="search-input"
            placeholder="搜索标题、描述关键词…"
            clearable
            @keyup.enter="loadFirst"
          >
            <template #prefix>
              <el-icon class="search-ico"><Search /></el-icon>
            </template>
          </el-input>
          <el-select v-model="type" class="type-select" placeholder="类型" @change="loadFirst">
            <el-option label="失物招领" value="found" />
            <el-option label="失物求助" value="lost" />
          </el-select>
          <el-button class="btn-glow" type="primary" @click="loadFirst">
            <el-icon><Search /></el-icon>
            检索
          </el-button>
          <el-button v-if="getToken()" class="btn-ghost" @click="router.push('/publish')">
            <el-icon><Upload /></el-icon>
            发布
          </el-button>
          <el-button v-if="getToken()" class="btn-ghost" @click="router.push('/user')">
            <el-icon><User /></el-icon>
            我的
          </el-button>
          <el-button v-if="getToken()" class="btn-ghost" @click="logout">
            <el-icon><SwitchButton /></el-icon>
            注销
          </el-button>
          <el-button
            v-if="getToken()"
            class="btn-admin"
            @click="router.push('/review-center')"
          >
            <el-icon><Setting /></el-icon>
            审核中心
          </el-button>
          <el-button
            v-if="getToken() && user.isAdmin"
            class="btn-admin"
            @click="router.push('/admin')"
          >
            <el-icon><Setting /></el-icon>
            工作台
          </el-button>
          <el-button v-if="!getToken()" class="btn-glow" type="primary" @click="router.push('/login')">
            登录
          </el-button>
        </div>
      </div>
    </header>

    <section class="hero">
      <div class="hero-inner">
        <p class="eyebrow">Campus Intelligence Network</p>
        <h1>
          发现与归还<br />
          <span class="grad">每一件失物</span>
        </h1>
        <p class="lead">
          图像智能识别辅助发布 · 认领验证防冒领 · 数据可追溯
        </p>
        <div class="hero-search">
          <el-input
            v-model="kw"
            size="large"
            class="hero-input"
            placeholder="输入关键词，快速匹配校园失物 / 招领信息"
            clearable
            @keyup.enter="loadFirst"
          >
            <template #append>
              <el-button type="primary" class="hero-go" @click="loadFirst">
                搜索
              </el-button>
            </template>
          </el-input>
        </div>
      </div>
    </section>

    <main class="main-area">
      <div class="section-head">
        <h2>{{ type === 'lost' ? '失物求助' : '失物招领' }}</h2>
        <span class="count font-mono">共 {{ total }} 条</span>
      </div>

      <div v-if="loading && !list.length" class="empty">
        <p class="loading-hint font-mono">加载中…</p>
      </div>

      <div v-else-if="!list.length" class="empty">
        <el-icon :size="48"><PictureFilled /></el-icon>
        <p>暂无数据，试试更换关键词或类型</p>
      </div>

      <div v-else class="card-grid">
        <article
          v-for="it in list"
          :key="it.id"
          class="item-card"
          @click="router.push(`/item/${it.id}`)"
        >
          <div class="card-visual">
            <template v-if="it.images?.length">
              <img
                :src="imgUrl(it.images[0].image_url)"
                alt=""
                :class="{ 'privacy-blur': isFullBlur(it), 'partial-base-blur': isPartialBlur(it) }"
              />
              <img
                v-if="isPartialBlur(it)"
                :src="imgUrl(it.images[0].image_url)"
                alt=""
                class="partial-clear-window"
                :style="partialWindowStyle(it)"
              />
            </template>
            <div v-else class="no-img">
              <el-icon :size="40"><PictureFilled /></el-icon>
            </div>
            <div class="card-shine" aria-hidden="true" />
            <span class="pill" :class="it.type === 'lost' ? 'lost' : 'found'">
              {{ it.type === 'lost' ? '失物' : '招领' }}
            </span>
          </div>
          <div class="card-body">
            <h3>{{ it.title }}</h3>
            <p class="desc">{{ it.description || '暂无描述' }}</p>
            <div class="status-row">
              <span class="status-text">状态：{{ it.status }}</span>
              <el-button
                v-if="it.is_owner && it.status_code === 'offline'"
                size="small"
                type="primary"
                class="relist-btn"
                @click.stop="relistItem(it.id)"
              >
                重新上架
              </el-button>
            </div>
            <div class="card-foot">
              <span class="loc">
                <el-icon><Location /></el-icon>
                {{ it.location || '地点未填' }}
              </span>
              <span class="go">
                详情
                <el-icon><Right /></el-icon>
              </span>
            </div>
          </div>
        </article>
      </div>

      <div ref="sentinel" class="scroll-sentinel" aria-hidden="true" />
      <p v-if="loadingMore" class="infinite-hint font-mono">加载更多…</p>
      <p v-else-if="list.length && noMore" class="infinite-hint muted font-mono">已加载全部 {{ total }} 条</p>
    </main>
  </div>
</template>

<style scoped>
.font-mono {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
}

.home-page {
  min-height: 100vh;
  position: relative;
  background: linear-gradient(180deg, #060a12 0%, #0b1220 35%, #0d1526 100%);
  color: #e2e8f0;
}

.ambient {
  position: fixed;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(ellipse 80% 50% at 50% -10%, rgba(56, 189, 248, 0.14), transparent),
    radial-gradient(ellipse 60% 40% at 100% 30%, rgba(99, 102, 241, 0.08), transparent);
  z-index: 0;
}

.top-nav {
  position: sticky;
  top: 0;
  z-index: 50;
  border-bottom: 1px solid rgba(56, 189, 248, 0.12);
  background: rgba(6, 10, 18, 0.75);
  backdrop-filter: blur(14px);
}

.nav-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.brand-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, #22d3ee, #6366f1);
  box-shadow: 0 0 24px rgba(34, 211, 238, 0.35);
}

.brand-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.brand-text .name {
  font-weight: 700;
  font-size: 18px;
  letter-spacing: 0.04em;
  background: linear-gradient(90deg, #f1f5f9, #94a3b8);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.brand-text .tag {
  font-size: 11px;
  color: #64748b;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.search-input {
  width: 220px;
}
.search-input :deep(.el-input__wrapper) {
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.85);
  box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.15);
}
.search-input :deep(.el-input__inner) {
  color: #e2e8f0;
}
.search-ico {
  color: #64748b;
}

.type-select {
  width: 130px;
}
.type-select :deep(.el-select__wrapper) {
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.85);
  box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.15);
}

.btn-glow {
  border-radius: 10px !important;
  background: linear-gradient(105deg, #0891b2, #2563eb) !important;
  border: none !important;
  font-weight: 600;
}
.btn-ghost {
  border-radius: 10px !important;
  background: rgba(30, 41, 59, 0.6) !important;
  border: 1px solid rgba(148, 163, 184, 0.2) !important;
  color: #e2e8f0 !important;
}
.btn-admin {
  border-radius: 10px !important;
  background: rgba(99, 102, 241, 0.2) !important;
  border: 1px solid rgba(129, 140, 248, 0.45) !important;
  color: #c7d2fe !important;
}

.hero {
  position: relative;
  z-index: 1;
  padding: 48px 24px 32px;
  max-width: 1280px;
  margin: 0 auto;
}

.hero-inner {
  text-align: center;
}

.eyebrow {
  margin: 0 0 12px;
  font-size: 12px;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: #22d3ee;
}

.hero h1 {
  margin: 0 0 16px;
  font-size: clamp(32px, 5vw, 48px);
  font-weight: 700;
  line-height: 1.15;
  color: #f8fafc;
}

.grad {
  background: linear-gradient(120deg, #22d3ee, #a78bfa, #f472b6);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.lead {
  margin: 0 auto 32px;
  max-width: 520px;
  font-size: 15px;
  color: #94a3b8;
  line-height: 1.65;
}

.hero-search {
  max-width: 640px;
  margin: 0 auto;
}

.hero-input :deep(.el-input__wrapper) {
  border-radius: 14px 0 0 14px !important;
  background: rgba(15, 23, 42, 0.9) !important;
  box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.2) !important;
  padding-left: 16px;
}
.hero-input :deep(.el-input-group__append) {
  padding: 0;
  background: transparent;
  border: none;
  box-shadow: none;
}
.hero-go {
  height: 100%;
  border-radius: 0 14px 14px 0 !important;
  padding: 0 28px !important;
  background: linear-gradient(105deg, #06b6d4, #4f46e5) !important;
  border: none !important;
  font-weight: 600;
}

.main-area {
  position: relative;
  z-index: 1;
  max-width: 1280px;
  margin: 0 auto;
  padding: 8px 24px 56px;
}

.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(56, 189, 248, 0.1);
}

.section-head h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #f1f5f9;
}

.count {
  font-size: 13px;
  color: #64748b;
}

.empty {
  text-align: center;
  padding: 64px 20px;
  color: #64748b;
}
.empty p {
  margin-top: 12px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.item-card {
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  background: linear-gradient(160deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.95) 100%);
  border: 1px solid rgba(56, 189, 248, 0.12);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);
  transition: transform 0.2s ease, box-shadow 0.25s ease, border-color 0.2s ease;
}

.item-card:hover {
  transform: translateY(-4px);
  border-color: rgba(34, 211, 238, 0.35);
  box-shadow: 0 12px 40px -8px rgba(34, 211, 238, 0.15);
}

.card-visual {
  position: relative;
  height: 168px;
  background: #0f172a;
  overflow: hidden;
}

.card-visual img.privacy-blur {
  filter: blur(12px);
  transform: scale(1.08);
}

.card-visual img.partial-base-blur {
  filter: blur(13px);
  transform: scale(1.04);
}

.card-visual .partial-clear-window {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  pointer-events: none;
}

.card-visual img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.35s ease;
}

.item-card:hover .card-visual img {
  transform: scale(1.05);
}

.no-img {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #334155;
  background: linear-gradient(145deg, #1e293b, #0f172a);
}

.card-shine {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    125deg,
    transparent 40%,
    rgba(255, 255, 255, 0.06) 50%,
    transparent 60%
  );
  pointer-events: none;
}

.pill {
  position: absolute;
  top: 12px;
  left: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.06em;
}
.pill.lost {
  background: rgba(239, 68, 68, 0.85);
  color: #fff;
}
.pill.found {
  background: rgba(16, 185, 129, 0.9);
  color: #fff;
}

.card-body {
  padding: 16px 16px 18px;
}

.card-body h3 {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: #f1f5f9;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.desc {
  margin: 0 0 12px;
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 40px;
}

.card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #64748b;
}

.status-row {
  margin: 0 0 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.status-text {
  font-size: 12px;
  color: #67e8f9;
}

.relist-btn {
  border-radius: 8px !important;
  padding: 4px 10px !important;
}

.loc {
  display: flex;
  align-items: center;
  gap: 4px;
}

.go {
  display: flex;
  align-items: center;
  gap: 2px;
  color: #22d3ee;
  font-weight: 500;
}

.scroll-sentinel {
  height: 1px;
  margin-top: 24px;
}

.infinite-hint {
  text-align: center;
  margin: 16px 0 8px;
  font-size: 13px;
  color: #22d3ee;
}
.infinite-hint.muted {
  color: #64748b;
}

.loading-hint {
  color: #94a3b8;
  font-size: 15px;
}
</style>
