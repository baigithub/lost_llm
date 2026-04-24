<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { admin } from '@/api/admin'
import { itemStatusLabel } from '@/utils/itemStatus'
import { ElMessageBox, ElMessage } from 'element-plus'

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const pageSizes = [10, 20, 50, 100]
const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

async function load() {
  const data = (await admin.items({ page: page.value, page_size: pageSize.value })) as { total: number; items: any[] }
  total.value = data.total
  rows.value = data.items
}

onMounted(load)

async function remove(id: number) {
  await ElMessageBox.confirm('确定删除该物品？', '确认')
  await admin.deleteItem(id)
  ElMessage.success('已删除')
  load()
}

function onSizeChange(size: number) {
  pageSize.value = size
  page.value = 1
  load()
}

function displayAccount(name?: string | null) {
  if (!name) return '—'
  return name
}
</script>

<template>
  <div>
    <h2>物品管理</h2>
    <el-table :data="rows" border style="margin-top: 16px">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
      <el-table-column prop="type" label="类型" width="100" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          {{ row.status || itemStatusLabel(row.status_code || row.status) }}
        </template>
      </el-table-column>
      <el-table-column label="发布者账号" width="140" show-overflow-tooltip>
        <template #default="{ row }">
          {{ displayAccount(row.publisher_username) }}
        </template>
      </el-table-column>
      <el-table-column label="审核员账号" width="140" show-overflow-tooltip>
        <template #default="{ row }">
          {{ displayAccount(row.reviewer_username) }}
        </template>
      </el-table-column>
      <el-table-column label="领取人员账号" width="140" show-overflow-tooltip>
        <template #default="{ row }">
          {{ displayAccount(row.claimer_username) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button link type="danger" @click="remove(row.id)">删除</el-button>
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
  </div>
</template>

<style scoped>
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
</style>
