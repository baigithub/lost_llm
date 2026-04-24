<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { myClaims } from '@/api/items'
import { admin } from '@/api/admin'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { House, Setting } from '@element-plus/icons-vue'

const router = useRouter()
const u = useUserStore()

const loading = ref(false)
const rows = ref<any[]>([])
const activeMenu = ref<'todo' | 'reviewed' | 'mine'>('mine')

const isStaff = computed(() => u.isAdmin)
const menuItems = computed(() =>
  isStaff.value
    ? [
        { key: 'todo', label: '我的待办' },
        { key: 'reviewed', label: '我的审核' },
        { key: 'mine', label: '我的认领' },
      ]
    : [{ key: 'mine', label: '我的认领' }],
)
const tableTitle = computed(() => menuItems.value.find((m) => m.key === activeMenu.value)?.label || '我的认领')

function statusText(row: any) {
  return row.item_status || '—'
}

function tagType(row: any) {
  const s = row.item_status_code
  if (s === 'claimed') return 'success'
  if (s === 'expired') return 'danger'
  if (s === 'offline') return 'info'
  return 'warning'
}

async function load() {
  loading.value = true
  try {
    let data: any
    if (activeMenu.value === 'todo') {
      data = await admin.pendingClaims({ page: 1, page_size: 100 })
    } else if (activeMenu.value === 'reviewed') {
      data = await admin.myReviewedClaims({ page: 1, page_size: 100 })
    } else {
      data = await myClaims()
    }
    rows.value = Array.isArray(data) ? data : (data as any)?.items || []
  } catch (e: any) {
    ElMessage.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function approve(id: number) {
  await ElMessageBox.confirm('确认通过该认领申请？', '审核通过', { type: 'warning' })
  await admin.adminApproveClaim(id)
  ElMessage.success('已通过')
  load()
}

async function reject(id: number) {
  const { value } = await ElMessageBox.prompt('请输入驳回意见', '驳回申请', {
    inputPattern: /^.{2,500}$/,
    inputErrorMessage: '长度需 2-500 字',
    confirmButtonText: '确认驳回',
    cancelButtonText: '取消',
    type: 'warning',
  })
  await admin.adminRejectClaim(id, value)
  ElMessage.success('已驳回')
  load()
}

function goItem(row: any) {
  if (activeMenu.value === 'mine') {
    router.push(`/item/${row.item_id}?claim_id=${row.id}`)
    return
  }
  router.push(`/item/${row.item_id}`)
}

function switchMenu(key: string) {
  activeMenu.value = key as 'todo' | 'reviewed' | 'mine'
  load()
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="head">
      <el-page-header @back="router.push('/home')" content="审核中心" />
      <div class="actions">
        <el-button :icon="House" @click="router.push('/home')">前台首页</el-button>
        <el-button v-if="isStaff" type="primary" plain :icon="Setting" @click="router.push('/admin/claims')">
          进入审核后台
        </el-button>
      </div>
    </div>

    <el-card shadow="never">
      <template #header>
        <div class="card-head">
          <div class="title">{{ tableTitle }}</div>
          <el-button text @click="load">刷新</el-button>
        </div>
      </template>
      <div class="main">
        <aside class="sidebar">
          <el-menu :default-active="activeMenu" @select="switchMenu">
            <el-menu-item v-for="m in menuItems" :key="m.key" :index="m.key">{{ m.label }}</el-menu-item>
          </el-menu>
        </aside>
        <section class="content">
          <el-table v-loading="loading" :data="rows" border stripe>
            <el-table-column prop="id" label="申请ID" width="90" />
            <el-table-column prop="item_id" label="物品ID" width="90" />
            <el-table-column prop="item_title" label="物品标题" min-width="160" show-overflow-tooltip />
            <el-table-column label="物品状态" width="110">
              <template #default="{ row }">
                <el-tag :type="tagType(row)" size="small">{{ statusText(row) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="认领状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'approved' ? 'success' : row.status === 'rejected' ? 'danger' : 'warning'" size="small">
                  {{
                    row.status === 'pending'
                      ? '待审核'
                      : row.status === 'approved'
                        ? '已通过'
                        : row.status === 'rejected'
                          ? '已驳回'
                          : row.status
                  }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column v-if="activeMenu !== 'todo'" prop="reviewer_username" label="审批人员" width="130" />
            <el-table-column v-if="activeMenu !== 'todo'" prop="reject_reason" label="审批意见" min-width="160" show-overflow-tooltip />
            <el-table-column prop="verification_proof" label="认领说明" min-width="180" show-overflow-tooltip />
            <el-table-column label="操作" :width="activeMenu === 'todo' ? 180 : 100" fixed="right">
              <template #default="{ row }">
                <template v-if="activeMenu === 'todo'">
                  <el-button link type="primary" @click="approve(row.id)">通过</el-button>
                  <el-button link type="danger" @click="reject(row.id)">驳回</el-button>
                </template>
                <el-button v-else link type="primary" @click="goItem(row)">查看物品</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!loading && rows.length === 0" description="暂无记录" />
        </section>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px;
}
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}
.actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.title {
  font-weight: 700;
}
.main {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 12px;
}
.sidebar {
  border-right: 1px solid #ebeef5;
  padding-right: 8px;
}
.content {
  min-width: 0;
}
</style>

