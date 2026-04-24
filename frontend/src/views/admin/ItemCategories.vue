<script setup lang="ts">
import CategoryDictPanel from '@/components/admin/CategoryDictPanel.vue'
</script>

<template>
  <div class="sys-page">
    <h2>物品分类管理</h2>
    <p class="hint">维护前台发布使用的物品分类字典。</p>
    <el-card class="card" shadow="never">
      <CategoryDictPanel />
    </el-card>
  </div>
</template>

<style scoped>
.sys-page {
  padding: 8px 0;
}
h2 {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
}
.hint {
  margin: 0 0 20px;
  font-size: 14px;
  color: #64748b;
  line-height: 1.6;
}
.card {
  border-radius: 12px;
  border: 1px solid rgba(77, 126, 255, 0.18);
}
</style>
