<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchItem, createClaim, myClaims, offlineItem } from '@/api/items'
import { itemStatusLabel } from '@/utils/itemStatus'
import { getToken } from '@/api/http'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const u = useUserStore()
const item = ref<any>(null)
const proof = ref('')
const contact = ref('')

const id = computed(() => Number(route.params.id))
const claimId = computed(() => Number(route.query.claim_id || 0))
const readonlyClaim = ref<any | null>(null)
const lockClaimForm = computed(
  () => !!readonlyClaim.value && readonlyClaim.value.status !== 'rejected',
)

function imgUrl(s: string) {
  if (!s) return ''
  if (s.startsWith('http')) return s
  return s
}

function isPartialBlur() {
  return item.value?.image_mask_mode === 'partial'
}

function isFullBlur() {
  return item.value?.image_mask_mode === 'full' || (item.value?.privacy_masked && !item.value?.image_mask_mode)
}

const clearWindowPositions = [
  'circle(16% at 50% 55%)', // 中间
  'circle(16% at 30% 30%)', // 左上
  'circle(16% at 70% 30%)', // 右上
  'circle(16% at 30% 72%)', // 左下
  'circle(16% at 70% 72%)', // 右下
]

function hashKey(s: string) {
  let h = 0
  for (let i = 0; i < s.length; i += 1) {
    h = (h * 31 + s.charCodeAt(i)) >>> 0
  }
  return h
}

function partialWindowStyle(im: any, i: string | number) {
  const seed = `${item.value?.id ?? ''}|${Number(i)}|${im?.image_url ?? ''}`
  const idx = hashKey(seed) % clearWindowPositions.length
  return { clipPath: clearWindowPositions[idx] }
}

const isOwner = computed(() => u.profile && item.value && (u.profile as any).id === item.value.publisher_id)

const canOffline = computed(
  () =>
    isOwner.value &&
    item.value &&
    ((item.value.status_code || item.value.status) === 'pending' ||
      (item.value.status_code || item.value.status) === 'matched'),
)

async function doOffline() {
  await ElMessageBox.confirm('下架后前台将不可见，您仍可在「我的发布」中查看。', '确认下架', { type: 'warning' })
  await offlineItem(id.value)
  ElMessage.success('已下架')
  item.value = await fetchItem(id.value)
}

onMounted(async () => {
  item.value = await fetchItem(id.value)
  if (claimId.value > 0 && getToken()) {
    const claims = await myClaims()
    const list = Array.isArray(claims) ? claims : (claims as any)?.items || []
    const matched = list.find((c: any) => Number(c.id) === claimId.value)
    if (matched) {
      readonlyClaim.value = matched
      proof.value = matched.verification_proof || ''
      contact.value = matched.contact_info || ''
    }
  }
})

async function claim() {
  if (!getToken()) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  await createClaim(id.value, { verification_proof: proof.value, contact_info: contact.value })
  ElMessage.success('已提交认领申请')
  router.push('/review-center')
}
</script>

<template>
  <div class="page" v-if="item">
    <el-page-header @back="router.push('/home')" content="物品详情" />
    <el-alert
      v-if="isOwner && (item.status_code || item.status) === 'offline'"
      type="warning"
      :closable="false"
      show-icon
      class="privacy-tip"
      title="该物品已下架，前台用户无法浏览；您仍可在个人中心「我的发布」中查看。"
    />
    <el-alert
      v-else-if="item.privacy_masked"
      type="info"
      :closable="false"
      show-icon
      class="privacy-tip"
      title="已隐藏部分信息以防冒领：描述与地点已脱敏，图片已模糊。认领时请填写独有特征，由发布者核对后再进一步沟通。"
    />
    <el-row :gutter="24" style="margin-top: 16px">
      <el-col :span="12">
        <el-carousel v-if="item.images?.length" height="320px">
          <el-carousel-item v-for="(im, i) in item.images" :key="i">
            <div class="slide-wrap">
              <img
                :src="imgUrl(im.image_url)"
                class="slide"
                :class="{ 'privacy-blur': isFullBlur(), 'partial-base-blur': isPartialBlur() }"
              />
              <img
                v-if="isPartialBlur()"
                :src="imgUrl(im.image_url)"
                class="slide partial-clear-window"
                :style="partialWindowStyle(im, i)"
              />
            </div>
          </el-carousel-item>
        </el-carousel>
      </el-col>
      <el-col :span="12">
        <h2>{{ item.title }}</h2>
        <p class="desc">{{ item.description }}</p>
        <p><strong>地点</strong>：{{ item.location || '—' }}</p>
        <p><strong>状态</strong>：{{ item.status || itemStatusLabel(item.status_code || item.status) }}</p>
        <p v-if="canOffline">
          <el-button type="warning" plain @click="doOffline">下架（前台不可见）</el-button>
        </p>
        <p><strong>发布者电话（脱敏）</strong>：{{ item.publisher_phone_masked || '—' }}</p>
        <template v-if="getToken() && !isOwner && (item.status_code || item.status) !== 'offline'">
          <el-divider />
          <h4>{{ lockClaimForm ? '我的认领信息（只读）' : '认领验证' }}</h4>
          <el-input
            v-model="proof"
            type="textarea"
            rows="4"
            :readonly="lockClaimForm"
            :placeholder="lockClaimForm ? '' : '请描述物品细节以证明归属'"
          />
          <el-input
            v-model="contact"
            :readonly="lockClaimForm"
            :placeholder="lockClaimForm ? '' : '您的联系方式'"
            style="margin-top: 8px"
          />
          <template v-if="readonlyClaim">
            <p style="margin-top: 10px"><strong>认领申请状态</strong>：{{
              readonlyClaim.status === 'pending'
                ? '待审核'
                : readonlyClaim.status === 'approved'
                  ? '已通过'
                  : readonlyClaim.status === 'rejected'
                    ? '已驳回'
                    : readonlyClaim.status
            }}</p>
            <p><strong>审批人员</strong>：{{ readonlyClaim.reviewer_username || '—' }}</p>
            <p><strong>审批意见</strong>：{{ readonlyClaim.reject_reason || '—' }}</p>
          </template>
          <el-button
            v-if="!lockClaimForm"
            type="primary"
            style="margin-top: 12px"
            @click="claim"
          >
            提交认领
          </el-button>
        </template>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px;
}
.privacy-tip {
  margin-top: 16px;
}

.slide {
  width: 100%;
  height: 320px;
  object-fit: contain;
}

.slide-wrap {
  position: relative;
  width: 100%;
  height: 320px;
}

.slide.privacy-blur {
  filter: blur(14px);
  transform: scale(1.06);
}

.slide.partial-base-blur {
  filter: blur(16px);
  transform: scale(1.04);
}

.slide.partial-clear-window {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.desc {
  white-space: pre-wrap;
  color: #555;
}
</style>
