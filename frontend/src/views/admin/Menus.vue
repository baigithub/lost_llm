<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { admin } from '@/api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'

const tree = ref<any[]>([])
const dlg = ref(false)
const form = ref<any>({})

async function load() {
  tree.value = (await admin.menuTree()) as any[]
}

onMounted(load)

function openCreate(parent_id = 0) {
  form.value = {
    parent_id,
    name: '',
    path: '',
    component: '',
    icon: '',
    permission: '',
    sort: 0,
    visible: 1,
  }
  dlg.value = true
}

function openEdit(row: any) {
  form.value = {
    id: row.id,
    parent_id: row.parent_id,
    name: row.name,
    path: row.path,
    component: row.component,
    icon: row.icon,
    permission: row.permission,
    sort: row.sort,
    visible: row.visible,
  }
  dlg.value = true
}

async function save() {
  const payload = { ...form.value }
  if (form.value.id) await admin.updateMenu(form.value.id, payload)
  else await admin.createMenu(payload)
  ElMessage.success('已保存')
  dlg.value = false
  load()
}

async function del(node: any) {
  await ElMessageBox.confirm('删除后不可恢复；若有子菜单请先删除子项。', '确认删除')
  await admin.deleteMenu(node.id)
  ElMessage.success('已删除')
  load()
}
</script>

<template>
  <div class="sys-page">
    <div class="page-head">
      <h2>菜单管理</h2>
      <p class="sub">配置侧栏路由路径、权限标识与显示；支持多级（父子 parent_id）</p>
    </div>

    <el-card shadow="never">
      <el-button type="primary" class="mb" @click="openCreate(0)">新增顶级菜单</el-button>
      <el-table :data="tree" row-key="id" border stripe default-expand-all :tree-props="{ children: 'children' }">
        <el-table-column prop="name" label="名称" min-width="140" />
        <el-table-column prop="path" label="路由路径" min-width="160" />
        <el-table-column prop="component" label="组件路径" min-width="140" show-overflow-tooltip />
        <el-table-column prop="permission" label="权限标识" min-width="140" />
        <el-table-column prop="icon" label="图标" width="100" />
        <el-table-column prop="sort" label="排序" width="72" />
        <el-table-column label="显示" width="80">
          <template #default="{ row }">
            <el-tag :type="row.visible === 1 ? 'success' : 'info'" size="small">{{ row.visible === 1 ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openCreate(row.id)">子菜单</el-button>
            <el-button link @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="del(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dlg" :title="form.id ? '编辑菜单' : '新增菜单'" width="580px" destroy-on-close>
      <el-form label-width="100px">
        <el-form-item label="父级 ID"><el-input-number v-model="form.parent_id" :min="0" style="width: 100%" /></el-form-item>
        <el-form-item label="名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="路由路径"><el-input v-model="form.path" placeholder="如 /admin/users" /></el-form-item>
        <el-form-item label="组件路径"><el-input v-model="form.component" placeholder="Vue 组件路径，可选" /></el-form-item>
        <el-form-item label="图标"><el-input v-model="form.icon" placeholder="Element Plus 图标名" /></el-form-item>
        <el-form-item label="权限标识"><el-input v-model="form.permission" placeholder="如 sys:user:list" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort" :min="0" /></el-form-item>
        <el-form-item label="侧栏显示">
          <el-switch v-model="form.visible" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
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
</style>
