<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { admin } from '@/api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(15)
const pageSizes = [10, 15, 20, 50]
const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
const kw = ref('')
const statusFilter = ref<number | undefined>(undefined)
const roles = ref<any[]>([])

const dlgCreate = ref(false)
const formCreate = ref({
  username: '',
  password: '123456',
  real_name: '',
  phone: '',
  email: '',
  role_ids: [] as number[],
})

const dlgEdit = ref(false)
const formEdit = ref({
  id: 0,
  real_name: '',
  phone: '',
  email: '',
  status: 1,
})

const dlgRoles = ref(false)
const roleUserId = ref(0)
const roleIds = ref<number[]>([])

async function load() {
  const data = (await admin.users({
    page: page.value,
    page_size: pageSize.value,
    username: kw.value || undefined,
    status: statusFilter.value,
  })) as { total: number; items: any[] }
  total.value = data.total
  rows.value = data.items
}

async function loadRoles() {
  roles.value = (await admin.roles()) as any[]
}

onMounted(async () => {
  await loadRoles()
  await load()
})

function openCreate() {
  formCreate.value = {
    username: '',
    password: '123456',
    real_name: '',
    phone: '',
    email: '',
    role_ids: [],
  }
  dlgCreate.value = true
}

async function saveCreate() {
  await admin.createUser({
    username: formCreate.value.username,
    password: formCreate.value.password,
    real_name: formCreate.value.real_name || undefined,
    phone: formCreate.value.phone || undefined,
    email: formCreate.value.email || undefined,
    role_ids: formCreate.value.role_ids,
  })
  ElMessage.success('已创建')
  dlgCreate.value = false
  load()
}

function openEdit(row: any) {
  formEdit.value = {
    id: row.id,
    real_name: row.real_name || '',
    phone: row.phone || '',
    email: row.email || '',
    status: row.status,
  }
  dlgEdit.value = true
}

async function saveEdit() {
  await admin.updateUser(formEdit.value.id, {
    real_name: formEdit.value.real_name || undefined,
    phone: formEdit.value.phone || undefined,
    email: formEdit.value.email || undefined,
    status: formEdit.value.status,
  })
  ElMessage.success('已保存')
  dlgEdit.value = false
  load()
}

function openRoles(row: any) {
  roleUserId.value = row.id
  roleIds.value = (row.roles || []).map((r: any) => r.id)
  dlgRoles.value = true
}

async function saveRoles() {
  await admin.setUserRoles(roleUserId.value, roleIds.value)
  ElMessage.success('角色已更新')
  dlgRoles.value = false
  load()
}

async function resetPwd(id: number) {
  await ElMessageBox.confirm('将密码重置为 123456', '确认')
  await admin.resetPassword(id)
  ElMessage.success('已重置')
}

async function toggleStatus(row: any) {
  const next = row.status === 1 ? 0 : 1
  const tip = next === 0 ? '禁用后该用户无法登录，是否继续？' : '确定启用该用户？'
  await ElMessageBox.confirm(tip, '确认')
  await admin.updateUser(row.id, { status: next })
  ElMessage.success('已更新')
  load()
}

function onSizeChange(size: number) {
  pageSize.value = size
  page.value = 1
  load()
}
</script>

<template>
  <div class="sys-page">
    <div class="page-head">
      <h2>用户管理</h2>
      <p class="sub">管理系统账号、状态与角色分配</p>
    </div>

    <el-card shadow="never" class="toolbar-card">
      <el-form :inline="true" @submit.prevent="load">
        <el-form-item label="用户名">
          <el-input v-model="kw" placeholder="模糊查询" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="statusFilter" clearable placeholder="全部" style="width: 120px">
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">查询</el-button>
          <el-button type="primary" plain @click="openCreate">新增用户</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="rows" border stripe>
        <el-table-column prop="id" label="ID" width="72" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="real_name" label="姓名" width="100" />
        <el-table-column prop="phone" label="手机" width="130" />
        <el-table-column prop="email" label="邮箱" min-width="160" show-overflow-tooltip />
        <el-table-column label="状态" width="88">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="角色" min-width="160">
          <template #default="{ row }">
            <el-tag v-for="r in row.roles" :key="r.code" size="small" class="tag-role">{{ r.name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="primary" @click="openRoles(row)">分配角色</el-button>
            <el-button link @click="toggleStatus(row)">{{ row.status === 1 ? '禁用' : '启用' }}</el-button>
            <el-button link @click="resetPwd(row.id)">重置密码</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager-wrap">
        <span class="pager-info">当前第 {{ page }} 页，共 {{ pageCount }} 页，共 {{ total }} 条</span>
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="pageSizes"
          layout="sizes, prev, pager, next, jumper"
          @current-change="load"
          @size-change="onSizeChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="dlgCreate" title="新增用户" width="480px" destroy-on-close>
      <el-form label-width="90px">
        <el-form-item label="用户名" required><el-input v-model="formCreate.username" /></el-form-item>
        <el-form-item label="初始密码" required><el-input v-model="formCreate.password" show-password /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="formCreate.real_name" /></el-form-item>
        <el-form-item label="手机"><el-input v-model="formCreate.phone" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="formCreate.email" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="formCreate.role_ids" multiple filterable style="width: 100%">
            <el-option v-for="r in roles" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlgCreate = false">取消</el-button>
        <el-button type="primary" @click="saveCreate">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="dlgEdit" title="编辑用户" width="480px" destroy-on-close>
      <el-form label-width="90px">
        <el-form-item label="姓名"><el-input v-model="formEdit.real_name" /></el-form-item>
        <el-form-item label="手机"><el-input v-model="formEdit.phone" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="formEdit.email" /></el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="formEdit.status">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlgEdit = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="dlgRoles" title="分配角色" width="480px" destroy-on-close>
      <el-select v-model="roleIds" multiple filterable style="width: 100%">
        <el-option v-for="r in roles" :key="r.id" :label="`${r.name} (${r.code})`" :value="r.id" />
      </el-select>
      <template #footer>
        <el-button @click="dlgRoles = false">取消</el-button>
        <el-button type="primary" @click="saveRoles">保存</el-button>
      </template>
    </el-dialog>
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
.toolbar-card {
  margin-bottom: 16px;
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
.tag-role {
  margin-right: 4px;
}
</style>
