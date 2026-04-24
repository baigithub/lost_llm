<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { admin } from '@/api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'

const rows = ref<any[]>([])
const dlg = ref(false)
const menuDlg = ref(false)
const form = ref<any>({})
const menuIds = ref<number[]>([])
const tree = ref<any[]>([])
const currentRoleId = ref(0)

async function load() {
  rows.value = (await admin.roles()) as any[]
}

async function loadTree() {
  tree.value = (await admin.menuTree()) as any[]
}

onMounted(async () => {
  await load()
  await loadTree()
})

function openCreate() {
  form.value = { name: '', code: '', sort: 0, remark: '', status: 1 }
  dlg.value = true
}

async function save() {
  const payload = { ...form.value }
  if (form.value.id) await admin.updateRole(form.value.id, payload)
  else await admin.createRole(payload)
  ElMessage.success('已保存')
  dlg.value = false
  load()
}

async function edit(row: any) {
  form.value = { ...row }
  dlg.value = true
}

async function del(row: any) {
  if (['super_admin', 'user'].includes(row.code)) {
    ElMessage.warning('系统预置角色不可删除')
    return
  }
  await ElMessageBox.confirm('确定删除该角色？', '确认')
  await admin.deleteRole(row.id)
  ElMessage.success('已删除')
  load()
}

async function openMenus(row: any) {
  currentRoleId.value = row.id
  const data = (await admin.roleMenus(row.id)) as { menu_ids: number[] }
  menuIds.value = data.menu_ids || []
  menuDlg.value = true
}

async function saveMenus() {
  await admin.setRoleMenus(currentRoleId.value, menuIds.value)
  ElMessage.success('菜单权限已更新')
  menuDlg.value = false
}

const flatMenuOptions = computed(() => {
  const o: { id: number; name: string }[] = []
  const w = (nodes: any[]) => {
    for (const n of nodes) {
      o.push({ id: n.id, name: n.name })
      if (n.children?.length) w(n.children)
    }
  }
  w(tree.value)
  return o
})
</script>

<template>
  <div class="sys-page">
    <div class="page-head">
      <h2>角色管理</h2>
      <p class="sub">定义角色标识，并为角色分配可访问的菜单（RBAC）</p>
    </div>

    <el-card shadow="never">
      <el-button type="primary" class="mb" @click="openCreate">新增角色</el-button>
      <el-table :data="rows" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="code" label="标识" min-width="120" />
        <el-table-column prop="sort" label="排序" width="80" />
        <el-table-column label="状态" width="88">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="140" show-overflow-tooltip />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="edit(row)">编辑</el-button>
            <el-button link type="primary" @click="openMenus(row)">分配菜单</el-button>
            <el-button link type="danger" @click="del(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dlg" :title="form.id ? '编辑角色' : '新增角色'" width="520px" destroy-on-close>
      <el-form label-width="90px">
        <el-form-item label="名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="标识" required>
          <el-input v-model="form.code" :disabled="['super_admin', 'user'].includes(form.code)" />
        </el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort" :min="0" /></el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="menuDlg" title="分配菜单权限" width="640px" destroy-on-close>
      <p class="hint">勾选该角色登录后可见的侧栏菜单（需重新登录或刷新菜单接口后生效）。</p>
      <el-select v-model="menuIds" multiple filterable style="width: 100%; margin-top: 8px" placeholder="选择菜单">
        <el-option v-for="o in flatMenuOptions" :key="o.id" :label="`${o.name} (#${o.id})`" :value="o.id" />
      </el-select>
      <template #footer>
        <el-button @click="menuDlg = false">取消</el-button>
        <el-button type="primary" @click="saveMenus">保存</el-button>
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
.mb {
  margin-bottom: 12px;
}
.hint {
  color: #909399;
  font-size: 13px;
  margin: 0;
}
</style>
