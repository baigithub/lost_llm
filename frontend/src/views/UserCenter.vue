<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { myPublished, myClaims } from '@/api/items'
import { itemStatusLabel } from '@/utils/itemStatus'
import { useUserStore } from '@/stores/user'
import { Bell, Files, House, Setting, SwitchButton } from '@element-plus/icons-vue'

const router = useRouter()
const u = useUserStore()
const pub = ref<any[]>([])
const clm = ref<any[]>([])
const loading = ref(true)

const publishCount = computed(() => pub.value.length)
const claimCount = computed(() => clm.value.length)

const pubPage = ref(1)
const pubPageSize = ref(10)
const clmPage = ref(1)
const clmPageSize = ref(10)
const pageSizes = [10, 20, 50, 100]

const pubPaged = computed(() => {
  const start = (pubPage.value - 1) * pubPageSize.value
  return pub.value.slice(start, start + pubPageSize.value)
})

const clmPaged = computed(() => {
  const start = (clmPage.value - 1) * clmPageSize.value
  return clm.value.slice(start, start + clmPageSize.value)
})

function statusTagType(status?: string) {
  if (!status) return 'info'
  if (status === 'pending' || status === 'matched') return 'warning'
  if (status === 'claimed') return 'success'
  if (status === 'offline') return 'info'
  if (status === 'expired') return 'danger'
  return 'info'
}

function logout() {
  u.logout()
  router.push('/login')
}

onMounted(async () => {
  loading.value = true
  try {
    const p = (await myPublished()) as { id: number; title: string; status: string }[]
    pub.value = Array.isArray(p) ? p : (p as any)?.items || []
    const c = await myClaims()
    clm.value = Array.isArray(c) ? c : (c as any)?.items || []
    pubPage.value = 1
    clmPage.value = 1
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page">
    <div class="bg" aria-hidden="true" />
    <div class="hero">
      <el-card class="hero-left" shadow="never">
        <template #header>
          <div class="head-row">
            <el-page-header @back="router.push('/home')" content="个人中心" />
            <div class="head-actions">
              <el-button :icon="House" @click="router.push('/home')">前台首页</el-button>
              <el-button :icon="SwitchButton" @click="logout">注销</el-button>
              <el-button v-if="u.isAdmin" type="primary" plain :icon="Setting" @click="router.push('/admin/dashboard')">
                管理端
              </el-button>
            </div>
          </div>
        </template>

        <el-skeleton :loading="loading" animated>
          <template #template>
            <div class="profile">
              <div class="avatar">
                <div class="avatar-fallback">U</div>
              </div>
              <div class="who sk">
                <div class="sk-line a" />
                <div class="sk-line b" />
              </div>
            </div>
          </template>
          <template #default>
            <div class="profile">
              <div class="avatar">
                <img
                  v-if="(u.profile as any)?.avatar_url"
                  :src="(u.profile as any).avatar_url"
                  alt="avatar"
                  class="avatar-img"
                />
                <div v-else class="avatar-fallback">
                  {{
                    ((u.profile as any)?.real_name || (u.profile as any)?.username || '我').slice(0, 1)
                  }}
                </div>
              </div>
              <div class="who">
                <div class="name">
                  <span class="name-text">{{
                    (u.profile as any)?.real_name || (u.profile as any)?.username || '用户'
                  }}</span>
                  <el-tag v-if="u.isAdmin" size="small" type="primary" effect="light">管理权限</el-tag>
                </div>

                <el-descriptions :column="2" size="small" class="desc" border>
                  <el-descriptions-item label="账号">
                    {{ (u.profile as any)?.username || '—' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="学号">
                    {{ (u.profile as any)?.student_id || '—' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="手机">
                    {{ (u.profile as any)?.phone || '—' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="邮箱">
                    {{ (u.profile as any)?.email || '—' }}
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>
          </template>
        </el-skeleton>
      </el-card>

      <div class="hero-right">
        <el-card class="stat-wrap" shadow="never">
          <template #header>
            <div class="stat-head">数据概览</div>
          </template>
          <div class="stat-grid">
            <div class="stat">
              <div class="stat-icon"><el-icon><Files /></el-icon></div>
              <div class="stat-main">
                <div class="stat-num font-mono">{{ publishCount }}</div>
                <div class="stat-lbl">我的发布</div>
              </div>
            </div>
            <div class="stat">
              <div class="stat-icon"><el-icon><Bell /></el-icon></div>
              <div class="stat-main">
                <div class="stat-num font-mono">{{ claimCount }}</div>
                <div class="stat-lbl">我的认领</div>
              </div>
            </div>
          </div>
          <div class="quick">
            <el-button type="primary" @click="router.push('/publish')">去发布</el-button>
            <el-button plain @click="router.push('/home')">去首页浏览</el-button>
          </div>
        </el-card>
      </div>
    </div>

    <el-card class="card" shadow="never">
      <el-tabs class="tabs" type="border-card">
        <el-tab-pane>
          <template #label>
            <span class="tab-label"><el-icon><Files /></el-icon>我的发布</span>
          </template>
          <div class="pane-content">
            <div class="table-top">
              <div class="table-title">发布记录</div>
              <div class="table-actions">
                <el-button type="primary" plain size="small" @click="router.push('/publish')">新增发布</el-button>
              </div>
            </div>

            <div class="table-shell">
              <el-table v-loading="loading" :data="pubPaged" border stripe class="table">
                <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
                <el-table-column label="状态" width="120">
                  <template #default="{ row }">
                    <el-tag :type="statusTagType(row.status_code || row.status)" size="small">
                      {{ row.status || itemStatusLabel(row.status_code || row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="200" fixed="right">
                  <template #default="{ row }">
                    <el-button link type="primary" @click="router.push(`/item/${row.id}`)">查看 / 审核认领</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="pub.length === 0" description="你还没有发布过物品">
                <el-button type="primary" @click="router.push('/publish')">立即发布</el-button>
              </el-empty>
            </div>
            <div class="pager">
              <el-pagination
                v-if="pub.length > 0"
                v-model:current-page="pubPage"
                v-model:page-size="pubPageSize"
                :page-sizes="pageSizes"
                :total="pub.length"
                layout="total, sizes, prev, pager, next, jumper"
              />
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane>
          <template #label>
            <span class="tab-label"><el-icon><Bell /></el-icon>我的认领</span>
          </template>
          <div class="pane-content">
            <div class="table-top">
              <div class="table-title">认领记录</div>
            </div>

            <div class="table-shell">
              <el-table v-loading="loading" :data="clmPaged" border stripe class="table">
                <el-table-column prop="item_id" label="物品ID" width="110" />
                <el-table-column prop="item_title" label="物品标题" min-width="180" show-overflow-tooltip />
                <el-table-column label="状态" width="140">
                  <template #default="{ row }">
                    <el-tag :type="row.status === 'approved' ? 'success' : row.status === 'rejected' ? 'danger' : 'warning'" size="small">
                      {{ row.status === 'pending' ? '待审核' : row.status === 'approved' ? '已通过' : row.status === 'rejected' ? '已驳回' : row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="reviewer_username" label="审批人员" width="140" />
                <el-table-column prop="reject_reason" label="审批意见" min-width="180" show-overflow-tooltip />
                <el-table-column prop="verification_proof" label="说明" min-width="240" show-overflow-tooltip />
                <el-table-column label="操作" width="160" fixed="right">
                  <template #default="{ row }">
                    <el-button link type="primary" @click="router.push(`/item/${row.item_id}`)">查看物品</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="clm.length === 0" description="暂无认领记录" />
            </div>
            <div class="pager">
              <el-pagination
                v-if="clm.length > 0"
                v-model:current-page="clmPage"
                v-model:page-size="clmPageSize"
                :page-sizes="pageSizes"
                :total="clm.length"
                layout="total, sizes, prev, pager, next, jumper"
              />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.page {
  max-width: 1320px;
  margin: 0 auto;
  padding: 32px 24px 56px;
  position: relative;
  overflow: hidden;
  min-height: calc(100vh - 64px);
  font-size: 130%;
  line-height: 1.55;
  /* page tokens (与管理端风格一致) */
  --uc-radius: 16px;
  --uc-border: 1px solid rgba(77, 126, 255, 0.18);
  --uc-shadow: 0 10px 24px rgba(37, 99, 235, 0.08);
  --uc-glass: rgba(255, 255, 255, 0.88);
  --uc-title: #0f172a;
  --uc-sub: #475569;
  --uc-muted: #64748b;
  --uc-header-bg: rgba(255, 255, 255, 0.86);
  --uc-header-border: 1px solid rgba(77, 126, 255, 0.2);
  background:
    radial-gradient(circle at 12% 15%, rgba(56, 189, 248, 0.12), transparent 36%),
    radial-gradient(circle at 88% 8%, rgba(99, 102, 241, 0.1), transparent 30%),
    linear-gradient(180deg, #f7fbff 0%, #eff5ff 100%);
}

.bg {
  position: absolute;
  inset: -120px -120px auto;
  height: 420px;
  pointer-events: none;
  background:
    radial-gradient(circle at 18% 30%, rgba(56, 189, 248, 0.18), transparent 52%),
    radial-gradient(circle at 82% 18%, rgba(99, 102, 241, 0.16), transparent 46%),
    radial-gradient(circle at 52% 70%, rgba(34, 197, 94, 0.08), transparent 50%);
  filter: blur(0.2px);
}

.font-mono {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
}

.hero {
  display: grid;
  grid-template-columns: 1.25fr 0.75fr;
  gap: 16px;
  align-items: stretch;
  position: relative;
}

@media (max-width: 980px) {
  .hero {
    grid-template-columns: 1fr;
  }
}

.hero-left {
  border-radius: var(--uc-radius);
  border: var(--uc-header-border);
  background: var(--uc-header-bg);
  box-shadow: var(--uc-shadow);
  backdrop-filter: blur(12px);
}

.head-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.head-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.profile {
  margin-top: 14px;
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.avatar {
  width: 54px;
  height: 54px;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(77, 126, 255, 0.25);
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.18), rgba(99, 102, 241, 0.18));
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-fallback {
  font-weight: 700;
  color: var(--uc-title);
  font-size: 20px;
}

.who {
  min-width: 0;
  flex: 1;
}

.name {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.name-text {
  font-size: 1.3em;
  font-weight: 800;
  color: var(--uc-title);
}

.desc {
  --el-descriptions-item-bordered-label-background: #f2f7ff;
  --el-text-color-regular: var(--uc-sub);
  font-size: 2em;
}

.sk {
  padding-top: 6px;
}
.sk-line {
  height: 12px;
  border-radius: 10px;
  background: linear-gradient(90deg, #eef2ff, #e0e7ff, #eef2ff);
  background-size: 240% 100%;
  animation: shimmer 1.6s ease infinite;
}
.sk-line.a {
  width: 55%;
  margin-bottom: 10px;
}
.sk-line.b {
  width: 85%;
}
@keyframes shimmer {
  0% {
    background-position: 0% 50%;
  }
  100% {
    background-position: 100% 50%;
  }
}

.hero-right {
  display: flex;
  height: 100%;
}

.stat-wrap {
  width: 100%;
  border-radius: var(--uc-radius);
  border: var(--uc-header-border);
  background: var(--uc-header-bg);
  box-shadow: var(--uc-shadow);
  backdrop-filter: blur(12px);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.stat-head {
  font-weight: 700;
  color: var(--uc-title);
}

.stat-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 12px;
  border-radius: 14px;
  border: 1px solid rgba(77, 126, 255, 0.16);
  background: linear-gradient(150deg, rgba(236, 246, 255, 0.95) 0%, rgba(228, 241, 255, 0.98) 100%);
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(37, 99, 235, 0.12);
  color: #2563eb;
  flex: 0 0 auto;
}

.stat-main {
  min-width: 0;
}

.stat-num {
  font-size: 24px;
  font-weight: 900;
  color: var(--uc-title);
  line-height: 1;
}

.stat-lbl {
  margin-top: 6px;
  font-size: 12px;
  color: var(--uc-sub);
}

.quick {
  margin-top: auto;
  padding-top: 14px;
  display: flex;
  gap: 10px;
  flex-wrap: nowrap;
  align-items: center;
}

.quick :deep(.el-button) {
  min-width: 120px;
}

.card {
  margin-top: 16px;
  border-radius: var(--uc-radius);
  border: var(--uc-border);
  background: var(--uc-glass);
  backdrop-filter: blur(12px);
  box-shadow: var(--uc-shadow);
}

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.table-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 10px 0 12px;
}

.table-title {
  font-weight: 700;
  color: var(--uc-title);
}

.table-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.table {
  border-radius: 12px;
  overflow: hidden;
  height: 100%;
}

.pane-content {
  min-height: 560px;
  display: flex;
  flex-direction: column;
}

.table-shell {
  flex: 1;
  min-height: 460px;
}

.table-shell :deep(.el-empty) {
  height: 100%;
}

.table-shell :deep(.el-empty__description) {
  margin-top: 10px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
  min-height: 36px;
}

:deep(.el-tabs--border-card) {
  border: none;
  background: transparent;
  box-shadow: none;
}

:deep(.el-tabs--border-card > .el-tabs__header) {
  background: transparent;
  border-bottom: 1px solid rgba(77, 126, 255, 0.16);
}

:deep(.el-table) {
  --el-table-header-bg-color: #edf4ff;
  --el-table-row-hover-bg-color: #f5f9ff;
}

:deep(.el-card__header) {
  border-bottom: 1px solid rgba(77, 126, 255, 0.16);
}

:deep(.el-button.is-plain) {
  border-color: rgba(77, 126, 255, 0.35);
}
</style>
