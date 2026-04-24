<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { admin } from '@/api/admin'
import { ElMessage } from 'element-plus'

const pageSize = ref(20)
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const data = (await admin.getHomeListPageSize()) as { page_size: number }
    pageSize.value = data.page_size ?? 20
  } finally {
    loading.value = false
  }
})

async function save() {
  loading.value = true
  try {
    const data = (await admin.setHomeListPageSize(pageSize.value)) as { page_size: number }
    pageSize.value = data.page_size
    ElMessage.success('已保存，前台首页下次加载列表时会使用新条数')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="sys-page">
    <h2>分页管理</h2>
    <p class="hint">配置门户首页「信息流」每次加载（含向下滑动加载更多）的条数，范围 5～100，默认 20。</p>
    <el-card v-loading="loading" class="card">
      <el-form label-width="160px" style="max-width: 520px">
        <el-form-item label="首页每页条数">
          <el-input-number v-model="pageSize" :min="5" :max="100" :step="1" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="save">保存</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.sys-page {
  padding: 8px 0;
}
.hint {
  color: #64748b;
  font-size: 14px;
  margin: 0 0 20px;
  line-height: 1.6;
}
.card {
  border-radius: 12px;
}
h2 {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
}
</style>
