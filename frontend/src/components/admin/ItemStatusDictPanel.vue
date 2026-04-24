<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { admin } from '@/api/admin'

const rows = ref<any[]>([])
const dlg = ref(false)
const edit = ref<any>({})

async function load() {
  rows.value = (await admin.itemStatusDict()) as any[]
}

onMounted(load)

function openCreate() {
  edit.value = { code: 'pending', label: '招领中', sort_order: 0, status: 1, remark: '' }
  dlg.value = true
}

function openEdit(row: any) {
  edit.value = {
    id: row.id,
    code: row.code,
    label: row.label,
    sort_order: row.sort_order,
    status: row.status,
    remark: row.remark || '',
  }
  dlg.value = true
}

async function save() {
  const payload = {
    code: edit.value.code,
    label: edit.value.label,
    sort_order: edit.value.sort_order || 0,
    status: edit.value.status ? 1 : 0,
    remark: edit.value.remark || undefined,
  }
  if (edit.value.id) await admin.updateItemStatusDict(edit.value.id, payload)
  else await admin.createItemStatusDict(payload)
  ElMessage.success('已保存')
  dlg.value = false
  load()
}

async function del(id: number) {
  await ElMessageBox.confirm('确定删除该状态字典项？', '确认')
  await admin.deleteItemStatusDict(id)
  ElMessage.success('已删除')
  load()
}
</script>

<template>
  <div class="panel">
    <el-button type="primary" style="margin-bottom: 16px" @click="openCreate">新增状态字典项</el-button>
    <el-table :data="rows" border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="code" label="编码" width="140" />
      <el-table-column prop="label" label="显示名称" width="140" />
      <el-table-column prop="sort_order" label="排序" width="90" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">{{ row.status === 1 ? '启用' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="usage_count" label="使用中物品数" width="120" />
      <el-table-column prop="remark" label="备注" min-width="160" show-overflow-tooltip />
      <el-table-column label="操作" width="170">
        <template #default="{ row }">
          <el-button link @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="del(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg" title="物品状态字典项" width="520px">
      <el-form label-width="110px">
        <el-form-item label="编码">
          <el-select v-model="edit.code" placeholder="请选择编码">
            <el-option label="pending（招领中）" value="pending" />
            <el-option label="matched（匹配中）" value="matched" />
            <el-option label="claimed（已认领）" value="claimed" />
            <el-option label="expired（已过期）" value="expired" />
            <el-option label="offline（已下架）" value="offline" />
          </el-select>
        </el-form-item>
        <el-form-item label="显示名称"><el-input v-model="edit.label" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="edit.sort_order" /></el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="edit.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="edit.remark" /></el-form-item>
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
