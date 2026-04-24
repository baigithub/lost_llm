<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowLeft,
  Camera,
  Location,
  MagicStick,
  Plus,
  Promotion,
  EditPen,
} from '@element-plus/icons-vue'
import { fetchCategories, recognitionUpload, createItem } from '@/api/items'
import { ElMessage } from 'element-plus'

const router = useRouter()
const cats = ref<{ id: number; name: string }[]>([])
const title = ref('')
const description = ref('')
const categoryId = ref<number | undefined>(undefined)
const type = ref<'lost' | 'found'>('lost')
const location = ref('')
const contactInfo = ref('')
const imageUrls = ref<string[]>([])
const rec = ref<any>(null)
const uploading = ref(false)

function imgUrl(s: string) {
  if (!s) return ''
  if (s.startsWith('http')) return s
  return s
}

function selectedCategoryName() {
  return cats.value.find((c) => c.id === categoryId.value)?.name || ''
}

function categoryCoverClass() {
  const name = selectedCategoryName()
  if (name.includes('电子')) return 'cover-electronic'
  if (name.includes('证件') || name.includes('卡')) return 'cover-card'
  if (name.includes('箱包')) return 'cover-bag'
  if (name.includes('钥匙')) return 'cover-key'
  if (name.includes('水杯') || name.includes('水壶')) return 'cover-cup'
  return 'cover-other'
}

/** 根据识别结果在系统分类中自动匹配（按优先级，未命中则「其他」） */
function guessCategoryId(
  recognition: { category?: string; features?: string; text?: string } | null,
  list: { id: number; name: string }[],
): number | undefined {
  if (!recognition || !list.length) return undefined
  const s = [recognition.category, recognition.features, recognition.text].filter(Boolean).join(' ')
  if (!s.trim()) return undefined

  const others = list.find((c) => c.name === '其他')
  const order = ['证件卡类', '电子产品', '水杯/水壶', '箱包', '钥匙/小件'] as const
  const kw: Record<string, string[]> = {
    证件卡类: ['校园卡', '身份证', '学生证', '一卡通', '门禁卡', '工作证', '银行卡', '证件卡', 'IC卡', '卡套'],
    电子产品: [
      '手机',
      '电脑',
      '平板',
      '耳机',
      '笔记本',
      '充电',
      '电子',
      '键盘',
      '鼠标',
      '显示器',
      '相机',
      '数据线',
      '移动电源',
      '充电宝',
      '智能手表',
      '手表',
      '平板电',
    ],
    '水杯/水壶': ['水杯', '水壶', '水瓶', '保温杯', '茶杯', '马克杯'],
    箱包: ['背包', '双肩包', '钱包', '行李箱', '手提包', '挎包', '手提箱', '书包'],
    '钥匙/小件': ['钥匙', 'U盘', '优盘', '钥匙扣', '门禁钥匙'],
  }

  for (const name of order) {
    const cat = list.find((c) => c.name === name)
    if (!cat) continue
    const words = kw[name] ?? []
    if (words.some((w) => s.includes(w))) return cat.id
  }

  for (const c of list) {
    if (c.name === '其他') continue
    if (s.includes(c.name)) return c.id
  }

  return others?.id
}

onMounted(async () => {
  cats.value = (await fetchCategories()) as { id: number; name: string }[]
})

async function onFileChange(file: File) {
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    const data = (await recognitionUpload(fd)) as { image_url: string; recognition: any }
    if (data.image_url && !imageUrls.value.includes(data.image_url)) {
      imageUrls.value = [...imageUrls.value, data.image_url]
    }
    rec.value = data.recognition
    if (data.recognition?.category) title.value = data.recognition.category + ' — 待确认标题'
    if (data.recognition?.features) description.value = data.recognition.features

    if (!cats.value.length) {
      cats.value = (await fetchCategories()) as { id: number; name: string }[]
    }
    const guessed = guessCategoryId(data.recognition, cats.value)
    if (guessed != null) {
      categoryId.value = guessed
      const name = cats.value.find((c) => c.id === guessed)?.name
      ElMessage.success(name ? `上传并识别完成，已预选分类：${name}` : '上传并识别完成')
    } else {
      ElMessage.success('上传并识别完成')
    }
  } finally {
    uploading.value = false
  }
}

function removeImage(idx: number) {
  imageUrls.value = imageUrls.value.filter((_, i) => i !== idx)
}

async function submit() {
  if (!imageUrls.value.length) {
    ElMessage.warning('请上传至少一张图片')
    return
  }
  await createItem({
    title: title.value || '未命名物品',
    description: description.value,
    category_id: categoryId.value,
    type: type.value,
    location: location.value,
    contact_info: contactInfo.value || undefined,
    image_urls: imageUrls.value,
  })
  ElMessage.success('发布成功')
  router.push('/home')
}
</script>

<template>
  <div class="publish-page">
    <div class="ambient" aria-hidden="true" />

    <header class="pub-nav">
      <button type="button" class="back-btn" @click="router.push('/home')">
        <el-icon><ArrowLeft /></el-icon>
        返回首页
      </button>
      <div class="pub-nav-title">
        <h1>发布失物 / 招领</h1>
        <p>上传照片，系统将尝试识别物品并预填信息；敏感信息请勿写进公开描述。</p>
      </div>
    </header>

    <main class="pub-main">
      <section class="glass panel-upload">
        <div class="panel-head">
          <span class="panel-icon"><el-icon><Camera /></el-icon></span>
          <div>
            <h2>物品照片</h2>
            <p class="panel-sub">支持 JPG / PNG，上传后自动调用模型识别</p>
          </div>
        </div>

        <div class="upload-wrap" :class="{ 'has-preview': imageUrls.length > 0 }">
          <el-upload
            class="pub-upload"
            drag
            :show-file-list="false"
            :auto-upload="false"
            accept="image/jpeg,image/png"
            :disabled="uploading"
            @change="(f: any) => f.raw && onFileChange(f.raw)"
          >
            <template v-if="!imageUrls.length">
              <el-icon class="upload-ico"><Plus /></el-icon>
              <p class="upload-title">拖拽图片到此处，或 <em>点击选择</em></p>
              <p class="upload-hint">识别过程可能需要几秒，请稍候</p>
            </template>
            <template v-else>
              <div class="preview-inner">
                <img :src="imgUrl(imageUrls[0])" alt="预览" />
                <span class="preview-overlay">点击或拖拽可更换图片</span>
              </div>
            </template>
          </el-upload>
          <div v-if="uploading" class="upload-loading">
            <el-icon class="spin"><MagicStick /></el-icon>
            <span>识别中…</span>
          </div>
        </div>

        <div v-if="!imageUrls.length" class="default-cover" :class="categoryCoverClass()">
          <span>系统默认封面 · {{ selectedCategoryName() || '未分类' }}</span>
        </div>

        <div v-if="imageUrls.length > 1" class="thumb-list">
          <div v-for="(u, i) in imageUrls" :key="`${u}-${i}`" class="thumb">
            <img :src="imgUrl(u)" alt="物品照片" />
            <button type="button" class="thumb-del" @click="removeImage(i)">移除</button>
          </div>
        </div>

        <div v-if="rec" class="rec-card" :class="{ err: rec.error }">
          <div class="rec-head">
            <el-icon><MagicStick /></el-icon>
            <span>识别结果</span>
          </div>
          <template v-if="rec.error">
            <p class="rec-err">{{ rec.error }}</p>
          </template>
          <template v-else>
            <p><span class="k">类别</span> {{ rec.category }}</p>
            <p v-if="rec.confidence != null">
              <span class="k">置信度</span>
              <span class="conf">{{ (rec.confidence * 100).toFixed(1) }}%</span>
            </p>
            <p v-if="rec.text" class="rec-text"><span class="k">图中文字</span> {{ rec.text }}</p>
          </template>
        </div>
      </section>

      <section class="glass panel-form">
        <div class="panel-head">
          <span class="panel-icon"><el-icon><EditPen /></el-icon></span>
          <div>
            <h2>填写信息</h2>
            <p class="panel-sub">标题与分类可手动修改；地点建议只写到楼宇级</p>
          </div>
        </div>

        <el-form class="pub-form" label-position="top" @submit.prevent="submit">
          <el-form-item label="发布类型">
            <el-radio-group v-model="type" class="type-radios" size="large">
              <el-radio-button label="lost">失物求助</el-radio-button>
              <el-radio-button label="found">拾物招领</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="标题" class="field-tall">
            <el-input v-model="title" placeholder="简要说明物品" clearable />
          </el-form-item>
          <el-form-item label="分类" class="field-tall">
            <el-select v-model="categoryId" clearable placeholder="选择分类" filterable>
              <el-option v-for="c in cats" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="描述">
            <el-input
              v-model="description"
              type="textarea"
              :rows="8"
              placeholder="颜色、品牌等可写；勿写学号、完整卡号等隐私"
            />
          </el-form-item>
          <el-form-item label="地点" class="field-tall">
            <el-input v-model="location" placeholder="例如：图书馆 · 三楼（不必过于精确）">
              <template #prefix>
                <el-icon class="input-prefix-ico"><Location /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item v-if="type === 'lost'" label="联系方式" class="field-tall">
            <el-input v-model="contactInfo" placeholder="如：手机号/微信（用于失物求助联系）" />
          </el-form-item>
          <div class="form-actions">
            <el-button class="btn-secondary" size="large" @click="router.push('/home')">取消</el-button>
            <el-button
              class="btn-submit"
              type="primary"
              size="large"
              native-type="submit"
              :loading="uploading"
            >
              <el-icon class="btn-ico"><Promotion /></el-icon>
              发布
            </el-button>
          </div>
        </el-form>
      </section>
    </main>
  </div>
</template>

<style scoped>
.publish-page {
  min-height: 100vh;
  position: relative;
  background: linear-gradient(180deg, #060a12 0%, #0b1220 40%, #0d1526 100%);
  color: #e2e8f0;
  padding-bottom: 48px;
}

.ambient {
  position: fixed;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(ellipse 70% 45% at 20% 0%, rgba(56, 189, 248, 0.12), transparent),
    radial-gradient(ellipse 50% 40% at 90% 20%, rgba(99, 102, 241, 0.1), transparent);
  z-index: 0;
}

.pub-nav {
  position: relative;
  z-index: 1;
  max-width: 1080px;
  margin: 0 auto;
  padding: 20px 24px 8px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 10px;
  border: 1px solid rgba(56, 189, 248, 0.25);
  background: rgba(15, 23, 42, 0.5);
  color: #67e8f9;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}
.back-btn:hover {
  background: rgba(56, 189, 248, 0.12);
  border-color: rgba(56, 189, 248, 0.45);
}

.pub-nav-title {
  margin-top: 20px;
}
.pub-nav-title h1 {
  margin: 0 0 8px;
  font-size: clamp(22px, 3.5vw, 28px);
  font-weight: 700;
  letter-spacing: -0.02em;
  background: linear-gradient(120deg, #f8fafc 0%, #94a3b8 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.pub-nav-title p {
  margin: 0;
  font-size: 14px;
  color: #64748b;
  line-height: 1.6;
  max-width: 520px;
}

.pub-main {
  position: relative;
  z-index: 1;
  max-width: 1080px;
  margin: 0 auto;
  padding: 16px 24px 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: start;
}

@media (max-width: 900px) {
  .pub-main {
    grid-template-columns: 1fr;
  }
}

.glass {
  border-radius: 20px;
  padding: 24px;
  background: linear-gradient(155deg, rgba(30, 41, 59, 0.72) 0%, rgba(15, 23, 42, 0.88) 100%);
  border: 1px solid rgba(56, 189, 248, 0.14);
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(12px);
}

.panel-head {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 20px;
}
.panel-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.2), rgba(99, 102, 241, 0.22));
  border: 1px solid rgba(34, 211, 238, 0.35);
  color: #67e8f9;
  font-size: 22px;
}
.panel-head h2 {
  margin: 0 0 4px;
  font-size: 17px;
  font-weight: 600;
  color: #f1f5f9;
}
.panel-sub {
  margin: 0;
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
}

.upload-wrap {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
}

.pub-upload :deep(.el-upload) {
  width: 100%;
}
.pub-upload :deep(.el-upload-dragger) {
  width: 100%;
  padding: 36px 20px;
  border-radius: 16px;
  border: 1px dashed rgba(56, 189, 248, 0.35);
  background: rgba(15, 23, 42, 0.55);
  transition: border-color 0.2s, background 0.2s;
}
.pub-upload :deep(.el-upload-dragger:hover) {
  border-color: rgba(34, 211, 238, 0.55);
  background: rgba(56, 189, 248, 0.06);
}

.upload-wrap.has-preview .pub-upload :deep(.el-upload-dragger) {
  padding: 0;
  border-style: solid;
  border-color: rgba(56, 189, 248, 0.2);
  overflow: hidden;
}

.upload-ico {
  font-size: 42px;
  color: #22d3ee;
  margin-bottom: 12px;
}
.upload-title {
  margin: 0 0 8px;
  font-size: 15px;
  color: #cbd5e1;
}
.upload-title em {
  color: #67e8f9;
  font-style: normal;
  font-weight: 600;
}
.upload-hint {
  margin: 0;
  font-size: 12px;
  color: #64748b;
}

.preview-inner {
  position: relative;
  height: 240px;
  background: #0f172a;
}
.preview-inner img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.preview-overlay {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 10px;
  font-size: 12px;
  text-align: center;
  color: #e2e8f0;
  background: linear-gradient(transparent, rgba(15, 23, 42, 0.92));
}

.upload-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: rgba(6, 10, 18, 0.72);
  color: #67e8f9;
  font-size: 14px;
  font-weight: 500;
  pointer-events: none;
}
.upload-loading .spin {
  font-size: 28px;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.rec-card {
  margin-top: 18px;
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(56, 189, 248, 0.08);
  border: 1px solid rgba(56, 189, 248, 0.2);
  font-size: 13px;
  color: #cbd5e1;
  line-height: 1.65;
}
.rec-card.err {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(248, 113, 113, 0.35);
}
.rec-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #67e8f9;
  margin-bottom: 8px;
}
.rec-card .k {
  display: inline-block;
  min-width: 4em;
  color: #64748b;
  font-size: 12px;
}
.rec-card .conf {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  color: #a5b4fc;
}
.rec-err {
  margin: 0;
  color: #fca5a5;
}
.rec-text {
  margin: 8px 0 0;
  word-break: break-all;
}

.default-cover {
  margin-top: 12px;
  height: 80px;
  border-radius: 12px;
  display: flex;
  align-items: flex-end;
  padding: 10px 12px;
  font-size: 12px;
  color: #e2e8f0;
  border: 1px solid rgba(148, 163, 184, 0.35);
}

.cover-electronic {
  background: linear-gradient(135deg, #0ea5e9, #1d4ed8);
}
.cover-card {
  background: linear-gradient(135deg, #7c3aed, #4f46e5);
}
.cover-bag {
  background: linear-gradient(135deg, #0f766e, #0ea5a4);
}
.cover-key {
  background: linear-gradient(135deg, #b45309, #f59e0b);
}
.cover-cup {
  background: linear-gradient(135deg, #0369a1, #06b6d4);
}
.cover-other {
  background: linear-gradient(135deg, #334155, #475569);
}

.thumb-list {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.thumb {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.35);
}

.thumb img {
  display: block;
  width: 100%;
  height: 72px;
  object-fit: cover;
}

.thumb-del {
  position: absolute;
  right: 4px;
  bottom: 4px;
  border: 0;
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 11px;
  color: #fff;
  background: rgba(15, 23, 42, 0.78);
  cursor: pointer;
}

.pub-form :deep(.el-form-item__label) {
  color: #94a3b8;
  font-weight: 500;
}
/* 标题、分类、地点：控件高度在默认基础上提高 30% */
.pub-form :deep(.field-tall .el-input__wrapper),
.pub-form :deep(.field-tall .el-select__wrapper) {
  min-height: calc(var(--el-component-size, 32px) * 1.3);
}
.pub-form :deep(.field-tall .el-input__inner) {
  min-height: calc(var(--el-component-size, 32px) * 1.3 - 2px);
}
.pub-form :deep(.el-input__wrapper),
.pub-form :deep(.el-textarea__inner) {
  background: rgba(15, 23, 42, 0.75) !important;
  box-shadow: 0 0 0 1px rgba(51, 65, 85, 0.6) inset !important;
  border-radius: 12px !important;
}
.pub-form :deep(.el-input__wrapper:hover),
.pub-form :deep(.el-textarea__inner:hover) {
  box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.35) inset !important;
}
.pub-form :deep(.el-input__wrapper.is-focus),
.pub-form :deep(.el-textarea__inner:focus) {
  box-shadow: 0 0 0 1px rgba(34, 211, 238, 0.5) inset, 0 0 0 3px rgba(56, 189, 248, 0.15) !important;
}
.pub-form :deep(.el-input__inner),
.pub-form :deep(.el-textarea__inner) {
  color: #f1f5f9;
}
.pub-form :deep(.el-input__inner::placeholder),
.pub-form :deep(.el-textarea__inner::placeholder) {
  color: #64748b;
}
.pub-form :deep(.el-select .el-select__wrapper) {
  background: rgba(15, 23, 42, 0.75) !important;
  box-shadow: 0 0 0 1px rgba(51, 65, 85, 0.6) inset !important;
  border-radius: 12px !important;
}
.pub-form :deep(.el-select .el-select__placeholder) {
  color: #64748b;
}
.pub-form :deep(.el-select .el-select__selected-item) {
  color: #f1f5f9;
}

.input-prefix-ico {
  color: #64748b;
  margin-right: 4px;
}

.type-radios :deep(.el-radio-button__inner) {
  background: rgba(15, 23, 42, 0.6);
  border-color: rgba(51, 65, 85, 0.8) !important;
  color: #94a3b8;
  padding: 10px 20px;
}
.type-radios :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(105deg, rgba(6, 182, 212, 0.35), rgba(79, 70, 229, 0.35)) !important;
  border-color: rgba(34, 211, 238, 0.45) !important;
  color: #f8fafc !important;
  box-shadow: none;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
  padding-top: 8px;
}
.btn-secondary {
  background: transparent !important;
  border: 1px solid rgba(148, 163, 184, 0.35) !important;
  color: #94a3b8 !important;
}
.btn-submit {
  background: linear-gradient(105deg, #0891b2, #4f46e5) !important;
  border: none !important;
  font-weight: 600;
  padding: 0 28px !important;
}
.btn-submit .btn-ico {
  margin-right: 6px;
  vertical-align: middle;
}
</style>
