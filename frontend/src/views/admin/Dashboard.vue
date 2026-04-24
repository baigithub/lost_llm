<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { admin } from '@/api/admin'
import { User, Goods, Clock, Bell, TrendCharts, DataLine } from '@element-plus/icons-vue'

const s = ref<Record<string, number>>({})
const charts = ref<any>({})
const chartBarEl = ref<HTMLElement | null>(null)
const chartPieEl = ref<HTMLElement | null>(null)
const chartLineEl = ref<HTMLElement | null>(null)
const chartRadarEl = ref<HTMLElement | null>(null)
let echartsLib: any = null

onMounted(async () => {
  s.value = (await admin.dashboard()) as Record<string, number>
  await nextTick()
  await loadCharts()
})

const cards = [
  { key: 'total_users', title: '用户总数', icon: User, accent: 'cyan' },
  { key: 'total_items', title: '物品总数', icon: Goods, accent: 'violet' },
  { key: 'pending_items', title: '待处理物品', icon: Clock, accent: 'amber' },
  { key: 'approved_claims_today', title: '当日审批通过认领', icon: Bell, accent: 'rose' },
] as const

const extra = { key: 'login_success_today', title: '今日成功登录', icon: TrendCharts, accent: 'emerald' }

async function ensureEcharts() {
  if ((window as any).echarts) {
    echartsLib = (window as any).echarts
    return
  }
  await new Promise<void>((resolve, reject) => {
    const existed = document.querySelector('script[data-echarts="1"]') as HTMLScriptElement | null
    if (existed) {
      existed.addEventListener('load', () => resolve(), { once: true })
      existed.addEventListener('error', () => reject(new Error('echarts load error')), { once: true })
      return
    }
    const script = document.createElement('script')
    script.src = 'https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js'
    script.async = true
    script.dataset.echarts = '1'
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('echarts load error'))
    document.head.appendChild(script)
  })
  echartsLib = (window as any).echarts
}

function setChart(el: HTMLElement | null, option: Record<string, unknown>) {
  if (!echartsLib || !el) return
  const ins = echartsLib.init(el)
  ins.setOption(option)
  charts.value[el.className] = ins
}

function chartBaseTitle(text: string) {
  return {
    text,
    left: 'center',
    top: 6,
    textStyle: { color: '#0f172a', fontSize: 14, fontWeight: 700 },
  }
}

async function loadCharts() {
  await ensureEcharts()
  const data = (await admin.dashboardCharts()) as {
    publish_top5_dates: { date: string; value: number }[]
    publish_by_category: { name: string; value: number }[]
    claims_top5_dates: { date: string; value: number }[]
    publish_category_radar: { indicators: { name: string; max: number }[]; values: number[] }
  }

  setChart(chartBarEl.value, {
    title: chartBaseTitle('发布物品数量 Top5（按日期）'),
    grid: { left: 56, right: 24, top: 56, bottom: 38 },
    xAxis: { type: 'category', data: data.publish_top5_dates.map((x) => x.date), axisLabel: { color: '#334155' } },
    yAxis: { type: 'value', axisLabel: { color: '#334155' } },
    tooltip: { trigger: 'axis' },
    series: [
      {
        type: 'bar',
        data: data.publish_top5_dates.map((x) => x.value),
        itemStyle: { color: '#3b82f6' },
        barMaxWidth: 42,
      },
    ],
  })

  setChart(chartPieEl.value, {
    title: chartBaseTitle('按分类统计发布物品数量'),
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, textStyle: { color: '#334155' } },
    series: [
      {
        type: 'pie',
        radius: ['35%', '68%'],
        center: ['50%', '46%'],
        data: data.publish_by_category,
        label: { color: '#334155' },
      },
    ],
  })

  setChart(chartLineEl.value, {
    title: chartBaseTitle('物品认领数量 Top5（按日期）'),
    grid: { left: 56, right: 24, top: 56, bottom: 38 },
    xAxis: { type: 'category', data: data.claims_top5_dates.map((x) => x.date), axisLabel: { color: '#334155' } },
    yAxis: { type: 'value', axisLabel: { color: '#334155' } },
    tooltip: { trigger: 'axis' },
    series: [
      {
        type: 'line',
        smooth: true,
        data: data.claims_top5_dates.map((x) => x.value),
        symbolSize: 8,
        lineStyle: { width: 3, color: '#10b981' },
        itemStyle: { color: '#10b981' },
        areaStyle: { color: 'rgba(16,185,129,0.15)' },
      },
    ],
  })

  setChart(chartRadarEl.value, {
    title: chartBaseTitle('按分类：发布物品 + 认领数量'),
    tooltip: {},
    radar: {
      center: ['50%', '52%'],
      radius: '62%',
      indicator: data.publish_category_radar.indicators,
      splitArea: { areaStyle: { color: ['rgba(59,130,246,0.03)', 'rgba(59,130,246,0.06)'] } },
      axisName: { color: '#334155' },
    },
    series: [
      {
        type: 'radar',
        data: [{ value: data.publish_category_radar.values, name: '总量' }],
        lineStyle: { color: '#8b5cf6', width: 2 },
        itemStyle: { color: '#8b5cf6' },
        areaStyle: { color: 'rgba(139,92,246,0.18)' },
      },
    ],
  })
}

function resizeAll() {
  Object.values(charts.value).forEach((ins: any) => ins?.resize?.())
}

onMounted(() => window.addEventListener('resize', resizeAll))
onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeAll)
  Object.values(charts.value).forEach((ins: any) => ins?.dispose?.())
})
</script>

<template>
  <div class="dash-page">
    <div class="dash-bg" aria-hidden="true" />

    <header class="dash-head">
      <div class="titles">
        <p class="eyebrow">Operations Console</p>
        <h1>工作台</h1>
        <p class="sub">实时总览 · 失物招领业务运行态势</p>
      </div>
      <div class="decor">
        <el-icon class="deco-icon"><DataLine /></el-icon>
      </div>
    </header>

    <div class="stat-grid">
      <div
        v-for="c in cards"
        :key="c.key"
        class="stat-card"
        :class="'acc-' + c.accent"
      >
        <div class="stat-icon">
          <el-icon :size="26"><component :is="c.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-label">{{ c.title }}</span>
          <span class="stat-value font-mono">{{ s[c.key] ?? 0 }}</span>
        </div>
        <div class="stat-glow" aria-hidden="true" />
      </div>
    </div>

    <div class="stat-grid secondary">
      <div class="stat-card wide acc-emerald">
        <div class="stat-icon">
          <el-icon :size="26"><component :is="extra.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-label">{{ extra.title }}</span>
          <span class="stat-value font-mono">{{ s[extra.key] ?? 0 }}</span>
        </div>
        <p class="stat-hint">统计当日 00:00 起成功登录次数</p>
        <div class="stat-glow" aria-hidden="true" />
      </div>
    </div>

    <footer class="dash-foot">
      <span class="pulse" />
      系统服务运行中 · 数据来自业务库实时聚合
    </footer>

    <section class="charts-grid">
      <el-card class="chart-card" shadow="never">
        <div ref="chartBarEl" class="chart-el" />
      </el-card>
      <el-card class="chart-card" shadow="never">
        <div ref="chartPieEl" class="chart-el" />
      </el-card>
      <el-card class="chart-card" shadow="never">
        <div ref="chartLineEl" class="chart-el" />
      </el-card>
      <el-card class="chart-card" shadow="never">
        <div ref="chartRadarEl" class="chart-el" />
      </el-card>
    </section>
  </div>
</template>

<style scoped>
.font-mono {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
}

.dash-page {
  position: relative;
  padding: 8px 8px 32px;
  min-height: calc(100vh - 100px);
  overflow: hidden;
}

.dash-bg {
  position: absolute;
  inset: -20% -10% auto;
  height: 60%;
  background: radial-gradient(ellipse at 30% 0%, rgba(56, 189, 248, 0.12), transparent 55%),
    radial-gradient(ellipse at 80% 20%, rgba(99, 102, 241, 0.1), transparent 50%);
  pointer-events: none;
}

.dash-head {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
  padding-bottom: 24px;
  border-bottom: 1px solid rgba(56, 189, 248, 0.12);
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 11px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #22d3ee;
}

.dash-head h1 {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
}

.sub {
  margin: 0;
  font-size: 14px;
  color: #334155;
}

.decor {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.15), rgba(99, 102, 241, 0.2));
  border: 1px solid rgba(56, 189, 248, 0.25);
  color: #67e8f9;
}

.stat-grid {
  position: relative;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

@media (max-width: 1100px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 600px) {
  .stat-grid {
    grid-template-columns: 1fr;
  }
}

.stat-grid.secondary {
  grid-template-columns: 1fr;
}

.stat-card {
  position: relative;
  padding: 20px 20px 18px;
  border-radius: 16px;
  background: linear-gradient(150deg, rgba(236, 246, 255, 0.95) 0%, rgba(228, 241, 255, 0.98) 100%);
  border: 1px solid rgba(112, 168, 255, 0.42);
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 14px;
  overflow: hidden;
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  border-color: rgba(37, 99, 235, 0.5);
}

.stat-card.wide {
  align-items: center;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.acc-cyan .stat-icon {
  background: rgba(6, 182, 212, 0.15);
  color: #22d3ee;
}
.acc-violet .stat-icon {
  background: rgba(99, 102, 241, 0.15);
  color: #a5b4fc;
}
.acc-amber .stat-icon {
  background: rgba(245, 158, 11, 0.12);
  color: #fbbf24;
}
.acc-rose .stat-icon {
  background: rgba(244, 63, 94, 0.12);
  color: #fb7185;
}
.acc-emerald .stat-icon {
  background: rgba(16, 185, 129, 0.12);
  color: #34d399;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.stat-label {
  font-size: 13px;
  color: #334155;
  font-weight: 500;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.1;
}

.stat-hint {
  width: 100%;
  margin: 8px 0 0;
  padding-left: 62px;
  font-size: 12px;
  color: #334155;
  flex-basis: 100%;
}

.stat-card.wide .stat-hint {
  padding-left: 0;
  margin-top: 12px;
  flex-basis: auto;
  width: 100%;
}

.stat-glow {
  position: absolute;
  right: -20%;
  top: -40%;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  filter: blur(40px);
  opacity: 0.35;
  pointer-events: none;
}

.acc-cyan .stat-glow {
  background: #06b6d4;
}
.acc-violet .stat-glow {
  background: #6366f1;
}
.acc-amber .stat-glow {
  background: #f59e0b;
}
.acc-rose .stat-glow {
  background: #f43f5e;
}
.acc-emerald .stat-glow {
  background: #10b981;
}

.dash-foot {
  position: relative;
  margin-top: 32px;
  padding: 14px 18px;
  border-radius: 12px;
  font-size: 12px;
  color: #334155;
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(231, 242, 255, 0.95);
  border: 1px solid rgba(112, 168, 255, 0.35);
}

.charts-grid {
  position: relative;
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

@media (max-width: 980px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

.chart-card {
  border-radius: 14px;
  border: 1px solid rgba(83, 140, 255, 0.22);
  background: rgba(255, 255, 255, 0.9);
}

.chart-el {
  height: 340px;
}

.pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 12px #22c55e;
  animation: pulse 2s ease infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.45;
  }
}
</style>
