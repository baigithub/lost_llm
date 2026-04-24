<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { admin } from '@/api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'

const rows = ref<any[]>([])
const dlg = ref(false)
const edit = ref<any>({})

async function load() {
  rows.value = (await admin.categories()) as any[]
}

onMounted(load)

function openCreate() {
  edit.value = { category_name: '', parent_id: null, sort_order: 0 }
  dlg.value = true
}

function openEdit(row: any) {
  edit.value = {
    id: row.id,
    category_name: row.name,
    parent_id: row.parent_id,
    sort_order: row.sort_order,
  }
  dlg.value = true
}

async function save() {
  if (edit.value.id)
    await admin.updateCategory(edit.value.id, {
      category_name: edit.value.category_name,
      sort_order: edit.value.sort_order,
    })
  else
    await admin.createCategory({
      category_name: edit.value.category_name,
      parent_id: edit.value.parent_id,
      sort_order: edit.value.sort_order,
    })
  ElMessage.success('已保存')
  dlg.value = false
  load()
}

async function del(id: number) {
  await ElMessageBox.confirm('确定删除？', '确认')
  await admin.deleteCategory(id)
  ElMessage.success('已删除')
  load()
}
</script>

<template>
  <div class="panel">
    <el-button type="primary" style="margin-bottom: 16px" @click="openCreate">新增分类</el-button>
    <el-table :data="rows" border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="parent_id" label="父级" />
      <el-table-column prop="sort_order" label="排序" width="100" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button link @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="del(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg" title="物品分类" width="480px">
      <el-form label-width="100px">
        <el-form-item label="名称"><el-input v-model="edit.category_name" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="edit.sort_order" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.panel {
  padding-top: 4px;
}
</style>
