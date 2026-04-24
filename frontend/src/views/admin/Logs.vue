<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { admin } from '@/api/admin'
import { getToken } from '@/api/http'

const tab = ref('login')
const loginRows = ref<any[]>([])
const opRows = ref<any[]>([])
const exRows = ref<any[]>([])
const totalL = ref(0)
const totalO = ref(0)
const totalE = ref(0)
const pageL = ref(1)
const pageO = ref(1)
const pageE = ref(1)
const pageSizeL = ref(15)
const pageSizeO = ref(15)
const pageSizeE = ref(15)
const pageSizes = [10, 15, 20, 50]
const pageCountL = computed(() => Math.max(1, Math.ceil(totalL.value / pageSizeL.value)))
const pageCountO = computed(() => Math.max(1, Math.ceil(totalO.value / pageSizeO.value)))
const pageCountE = computed(() => Math.max(1, Math.ceil(totalE.value / pageSizeE.value)))

const qLogin = ref({ username: '', status: undefined as number | undefined })
const qOp = ref({ username: '', module: '' })
const qEx = ref({ username: '' })

const exDrawer = ref(false)
const exDetail = ref<any>(null)

async function loadLogin() {
  const data = (await admin.loginLogs({
    page: pageL.value,
    page_size: pageSizeL.value,
    username: qLogin.value.username || undefined,
    status: qLogin.value.status,
  })) as { total: number; items: any[] }
  totalL.value = data.total
  loginRows.value = data.items
}

async function loadOp() {
  const data = (await admin.operationLogs({
    page: pageO.value,
    page_size: pageSizeO.value,
    username: qOp.value.username || undefined,
    module: qOp.value.module || undefined,
  })) as { total: number; items: any[] }
  totalO.value = data.total
  opRows.value = data.items
}

async function loadEx() {
  const data = (await admin.exceptionLogs({
    page: pageE.value,
    page_size: pageSizeE.value,
    username: qEx.value.username || undefined,
  })) as { total: number; items: any[] }
  totalE.value = data.total
  exRows.value = data.items
}

onMounted(() => loadLogin())

watch(tab, (t) => {
  if (t === 'login') loadLogin()
  else if (t === 'op') loadOp()
  else loadEx()
})

function exportUrl(base: string, q: Record<string, string | number | undefined>) {
  const p = new URLSearchParams()
  Object.entries(q).forEach(([k, v]) => {
    if (v !== undefined && v !== '') p.set(k, String(v))
  })
  const qs = p.toString()
  return qs ? `${base}?${qs}` : base
}

async function download(path: string, filename: string) {
  const token = getToken()
  const res = await fetch(path, { headers: { Authorization: `Bearer ${token}` } })
  const blob = await res.blob()
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename
  a.click()
  URL.revokeObjectURL(a.href)
}

function exportLoginCsv() {
  download(
    exportUrl('/api/v1/admin/logs/login/export', {
      username: qLogin.value.username || undefined,
      status: qLogin.value.status,
    }),
    'login_logs.csv',
  )
}

function exportOpCsv() {
  download(
    exportUrl('/api/v1/admin/logs/operation/export', {
      username: qOp.value.username || undefined,
      module: qOp.value.module || undefined,
    }),
    'operation_logs.csv',
  )
}

function exportExCsv() {
  download(exportUrl('/api/v1/admin/logs/exception/export', { username: qEx.value.username || undefined }), 'exception_logs.csv')
}

async function openExDetail(id: number) {
  exDetail.value = await admin.exceptionDetail(id)
  exDrawer.value = true
}

function onSizeChangeL(size: number) {
  pageSizeL.value = size
  pageL.value = 1
  loadLogin()
}
function onSizeChangeO(size: number) {
  pageSizeO.value = size
  pageO.value = 1
  loadOp()
}
function onSizeChangeE(size: number) {
  pageSizeE.value = size
  pageE.value = 1
  loadEx()
}
</script>

<template>
  <div class="sys-page">
    <div class="page-head">
      <h2>日志管理</h2>
      <p class="sub">登录审计、管理端操作记录与系统异常；支持筛选与 CSV 导出</p>
    </div>

    <el-card shadow="never">
      <el-tabs v-model="tab">
        <el-tab-pane label="登录日志" name="login">
          <el-form :inline="true" class="filter-form">
            <el-form-item label="用户名">
              <el-input v-model="qLogin.username" clearable placeholder="模糊" style="width: 160px" />
            </el-form-item>
            <el-form-item label="结果">
              <el-select v-model="qLogin.status" clearable placeholder="全部" style="width: 110px">
                <el-option label="成功" :value="1" />
                <el-option label="失败" :value="0" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="() => { pageL = 1; loadLogin() }">查询</el-button>
              <el-button @click="exportLoginCsv">导出 CSV</el-button>
            </el-form-item>
          </el-form>
          <el-table :data="loginRows" border stripe size="small">
            <el-table-column prop="username" label="用户" width="120" />
            <el-table-column prop="ip" label="IP" width="130" />
            <el-table-column label="结果" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
                  {{ row.status === 1 ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="msg" label="说明" min-width="160" show-overflow-tooltip />
            <el-table-column prop="user_agent" label="UA" min-width="200" show-overflow-tooltip />
            <el-table-column prop="login_time" label="时间" width="170" />
          </el-table>
          <div class="pager-wrap">
            <span class="pager-info">当前第 {{ pageL }} 页，共 {{ pageCountL }} 页，共 {{ totalL }} 条</span>
            <el-pagination
              v-model:current-page="pageL"
              v-model:page-size="pageSizeL"
              :total="totalL"
              :page-sizes="pageSizes"
              layout="sizes, prev, pager, next, jumper"
              @current-change="loadLogin"
              @size-change="onSizeChangeL"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="操作日志" name="op">
          <el-form :inline="true" class="filter-form">
            <el-form-item label="用户名">
              <el-input v-model="qOp.username" clearable style="width: 140px" />
            </el-form-item>
            <el-form-item label="模块">
              <el-input v-model="qOp.module" clearable placeholder="如 admin" style="width: 120px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="() => { pageO = 1; loadOp() }">查询</el-button>
              <el-button @click="exportOpCsv">导出 CSV</el-button>
            </el-form-item>
          </el-form>
          <el-table :data="opRows" border stripe size="small">
            <el-table-column prop="username" label="用户" width="100" />
            <el-table-column prop="module" label="模块" width="90" />
            <el-table-column prop="operation" label="操作" width="90" />
            <el-table-column label="菜单" min-width="120" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.menu_name || '—' }}
              </template>
            </el-table-column>
            <el-table-column prop="url" label="URL" min-width="200" show-overflow-tooltip />
            <el-table-column prop="method" label="方法" width="70" />
            <el-table-column prop="result" label="结果" width="80" />
            <el-table-column prop="duration" label="耗时ms" width="88" />
            <el-table-column prop="create_time" label="时间" width="170" />
          </el-table>
          <div class="pager-wrap">
            <span class="pager-info">当前第 {{ pageO }} 页，共 {{ pageCountO }} 页，共 {{ totalO }} 条</span>
            <el-pagination
              v-model:current-page="pageO"
              v-model:page-size="pageSizeO"
              :total="totalO"
              :page-sizes="pageSizes"
              layout="sizes, prev, pager, next, jumper"
              @current-change="loadOp"
              @size-change="onSizeChangeO"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="异常日志" name="ex">
          <el-form :inline="true" class="filter-form">
            <el-form-item label="用户名">
              <el-input v-model="qEx.username" clearable style="width: 160px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="() => { pageE = 1; loadEx() }">查询</el-button>
              <el-button @click="exportExCsv">导出 CSV</el-button>
            </el-form-item>
          </el-form>
          <el-table :data="exRows" border stripe size="small">
            <el-table-column prop="exception_type" label="类型" width="180" show-overflow-tooltip />
            <el-table-column prop="message" label="消息" min-width="200" show-overflow-tooltip />
            <el-table-column prop="url" label="URL" width="160" show-overflow-tooltip />
            <el-table-column prop="create_time" label="时间" width="170" />
            <el-table-column label="操作" width="88" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openExDetail(row.id)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="pager-wrap">
            <span class="pager-info">当前第 {{ pageE }} 页，共 {{ pageCountE }} 页，共 {{ totalE }} 条</span>
            <el-pagination
              v-model:current-page="pageE"
              v-model:page-size="pageSizeE"
              :total="totalE"
              :page-sizes="pageSizes"
              layout="sizes, prev, pager, next, jumper"
              @current-change="loadEx"
              @size-change="onSizeChangeE"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-drawer v-model="exDrawer" title="异常详情" size="50%">
      <template v-if="exDetail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="类型">{{ exDetail.exception_type }}</el-descriptions-item>
          <el-descriptions-item label="消息">{{ exDetail.message }}</el-descriptions-item>
          <el-descriptions-item label="URL">{{ exDetail.url }}</el-descriptions-item>
          <el-descriptions-item label="参数">{{ exDetail.params || '—' }}</el-descriptions-item>
          <el-descriptions-item label="时间">{{ exDetail.create_time }}</el-descriptions-item>
        </el-descriptions>
        <el-divider />
        <pre class="stack">{{ exDetail.stack_trace }}</pre>
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.sys-page {
  padding: 0 4px;
}
.page-head h2 {
  margin: 0 0 4px;
  font-size: 20px;
}
.sub {
  margin: 0 0 16px;
  color: #909399;
  font-size: 13px;
}
.filter-form {
  margin-bottom: 12px;
}
.pager-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
}
.pager-info {
  color: #64748b;
  font-size: 14px;
}
.stack {
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 12px;
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 8px;
  max-height: 60vh;
  overflow: auto;
}
</style>
