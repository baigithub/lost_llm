<script setup lang="ts">
import { ref, watch } from 'vue'
import CategoryDictPanel from '@/components/admin/CategoryDictPanel.vue'
import ItemStatusDictPanel from '@/components/admin/ItemStatusDictPanel.vue'

const props = withDefaults(defineProps<{ initialTab?: 'item_status' | 'category' }>(), {
  initialTab: 'item_status',
})
const activeTab = ref(props.initialTab)

watch(
  () => props.initialTab,
  (v) => {
    activeTab.value = v
  },
)
</script>

<template>
  <div class="sys-page">
    <h2>数据字典管理</h2>
    <p class="hint">维护系统业务字典。当前支持：<strong>物品状态</strong>、<strong>物品分类</strong>。</p>

    <el-card class="card" shadow="never">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="物品状态" name="item_status">
          <ItemStatusDictPanel />
        </el-tab-pane>
        <el-tab-pane label="物品分类" name="category">
          <CategoryDictPanel />
        </el-tab-pane>
      </el-tabs>
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
.card :deep(.el-tabs__header) {
  margin-bottom: 8px;
}
</style>
