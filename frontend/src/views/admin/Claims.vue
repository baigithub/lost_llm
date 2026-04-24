<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { admin } from '@/api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const pageSizes = [10, 20, 50, 100]
const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
const tab = ref<'pending' | 'mine'>('pending')
const dlgDetail = ref(false)
const detail = ref<any>(null)

async function load() {
  const loader = tab.value === 'pending' ? admin.pendingClaims : admin.myReviewedClaims
  const data = (await loader({ page: page.value, page_size: pageSize.value })) as {
    total: number
    items: any[]
  }
  total.value = data.total
  rows.value = data.items
}

onMounted(load)

async function approve(id: number) {
  await ElMessageBox.confirm('确认通过该认领申请？通过后该物品将标记为已认领，同物品其他待审申请将被驳回。', '审核通过', {
    type: 'warning',
  })
  await admin.adminApproveClaim(id)
  ElMessage.success('已通过')
  load()
}

async function reject(id: number) {
  const { value } = await ElMessageBox.prompt('请输入驳回意见（申请人可见）', '驳回申请', {
    confirmButtonText: '确认驳回',
    cancelButtonText: '取消',
    inputPattern: /^.{2,500}$/,
    inputErrorMessage: '驳回意见长度需在 2-500 字',
    type: 'warning',
  })
  await admin.adminRejectClaim(id, value)
  ElMessage.success('已驳回')
  load()
}

async function openDetail(id: number) {
  detail.value = await admin.claimDetail(id)
  dlgDetail.value = true
}

function statusText(s: string) {
  if (s === 'pending') return '待审核'
  if (s === 'approved') return '已通过'
  if (s === 'rejected') return '已驳回'
  return s
}

function onSizeChange(size: number) {
  pageSize.value = size
  page.value = 1
  load()
}

function onTabChange() {
  page.value = 1
  load()
}
</script>

<template>
  <div>
    <h2>认领审核</h2>
    <p class="hint">「所有待审核」显示当前全部待审核的认领申请；「我审核的」显示本人已审核记录。</p>
    <el-tabs v-model="tab" @tab-change="onTabChange">
      <el-tab-pane label="所有待审核" name="pending" />
      <el-tab-pane label="我审核的" name="mine" />
    </el-tabs>
    <el-table :data="rows" border style="margin-top: 16px">
      <el-table-column prop="id" label="申请ID" width="90" />
      <el-table-column prop="item_id" label="物品ID" width="90" />
      <el-table-column prop="item_title" label="物品标题" min-width="160" show-overflow-tooltip />
      <el-table-column prop="publisher_username" label="发布者" width="120" />
      <el-table-column prop="claimant_username" label="认领人" width="120" />
      <el-table-column prop="verification_proof" label="验证说明" min-width="200" show-overflow-tooltip />
      <el-table-column prop="contact_info" label="联系方式" width="140" show-overflow-tooltip />
      <el-table-column v-if="tab === 'mine'" label="结果" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 'approved' ? 'success' : 'danger'" size="small">
            {{ statusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="tab === 'mine'" prop="reject_reason" label="审批意见" min-width="180" show-overflow-tooltip />
      <el-table-column v-if="tab === 'mine'" prop="reviewed_at" label="审批时间" width="170" />
      <el-table-column prop="create_time" label="申请时间" width="170" />
      <el-table-column label="操作" :width="tab === 'pending' ? 220 : 100" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row.id)">详情</el-button>
          <template v-if="tab === 'pending'">
            <el-button link type="primary" @click="approve(row.id)">通过</el-button>
            <el-button link type="danger" @click="reject(row.id)">驳回</el-button>
          </template>
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
        layout="total, sizes, prev, pager, next"
        @current-change="load"
        @size-change="onSizeChange"
      />
    </div>

    <el-dialog v-model="dlgDetail" title="认领审核详情" width="820px" destroy-on-close>
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="物品">{{ detail.item?.title }}</el-descriptions-item>
          <el-descriptions-item label="发布者">{{ detail.item?.publisher_username || '—' }}</el-descriptions-item>
          <el-descriptions-item label="认领人">{{ detail.claim?.claimant_username || '—' }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ statusText(detail.claim?.status) }}</el-descriptions-item>
          <el-descriptions-item label="认领验证">{{ detail.claim?.verification_proof || '—' }}</el-descriptions-item>
          <el-descriptions-item label="联系方式">{{ detail.claim?.contact_info || '—' }}</el-descriptions-item>
          <el-descriptions-item label="物品地点">{{ detail.item?.location || '—' }}</el-descriptions-item>
          <el-descriptions-item label="审批意见">{{ detail.claim?.reject_reason || '—' }}</el-descriptions-item>
          <el-descriptions-item label="物品描述" :span="2">
            <div class="desc">{{ detail.item?.description || '—' }}</div>
          </el-descriptions-item>
        </el-descriptions>
        <el-carousel v-if="detail.item?.images?.length" height="320px" style="margin-top: 16px">
          <el-carousel-item v-for="(im, i) in detail.item.images" :key="i">
            <img :src="im.image_url" class="slide" />
          </el-carousel-item>
        </el-carousel>
      </template>
      <template #footer>
        <el-button @click="dlgDetail = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.hint {
  margin: 8px 0 0;
  font-size: 13px;
  color: #64748b;
}
.pager-wrap {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  justify-content: space-between;
}
.pager-info {
  font-size: 13px;
  color: #64748b;
}
.slide {
  width: 100%;
  height: 320px;
  object-fit: contain;
}
.desc {
  white-space: pre-wrap;
  line-height: 1.5;
}
</style>
