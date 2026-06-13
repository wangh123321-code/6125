<template>
  <div class="mydata-container">
    <div class="page-header">
      <div>
        <h2 class="page-title">我的训练数据</h2>
        <p class="page-subtitle">查看每次训练的详细数据与教练建议</p>
      </div>
      <div class="user-info">
        <el-avatar :size="40" class="my-avatar">
          {{ userStore.name?.charAt(0) }}
        </el-avatar>
        <div class="user-text">
          <div class="user-name">{{ userStore.name }}</div>
          <div class="user-sub">共 {{ sessionList.length }} 次训练</div>
        </div>
      </div>
    </div>

    <el-card class="summary-card" shadow="hover">
      <el-row :gutter="16">
        <el-col :xs="12" :sm="12" :md="3">
          <div class="sm-item">
            <div class="sm-icon sm-blue"><el-icon><Location /></el-icon></div>
            <div class="sm-val">{{ (totalStats.distance / 1000).toFixed(1) }}<span>km</span></div>
            <div class="sm-lbl">总距离</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="12" :md="3">
          <div class="sm-item">
            <div class="sm-icon sm-green"><el-icon><Trophy /></el-icon></div>
            <div class="sm-val">{{ totalStats.count }}<span>次</span></div>
            <div class="sm-lbl">训练次数</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="12" :md="3">
          <div class="sm-item">
            <div class="sm-icon sm-orange"><el-icon><Timer /></el-icon></div>
            <div class="sm-val">{{ totalStats.bestPace }}<span>/100m</span></div>
            <div class="sm-lbl">最佳配速</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="12" :md="3">
          <div class="sm-item">
            <div class="sm-icon sm-purple"><el-icon><Cpu /></el-icon></div>
            <div class="sm-val">{{ totalStats.avgHr }}<span>bpm</span></div>
            <div class="sm-lbl">平均心率</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon class="title-icon"><List /></el-icon>
            训练记录
          </span>
        </div>
      </template>
      <el-table :data="sessionList" stripe style="width: 100%" v-loading="loading">
        <el-table-column label="序号" type="index" width="70" align="center" />
        <el-table-column prop="date" label="训练日期" width="140" sortable>
          <template #default="{ row }">
            <div class="date-cell">
              <el-icon class="date-icon"><Calendar /></el-icon>
              <span>{{ row.date }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="total_distance" label="总距离(米)" width="140" align="center" sortable>
          <template #default="{ row }">
            <span class="highlight">{{ row.total_distance?.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="avg_pace" label="平均配速" width="130" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="getPaceType(row.avg_pace)">
              {{ row.avg_pace }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="avg_heart_rate" label="平均心率" width="130" align="center">
          <template #default="{ row }">
            <span :class="getHrClass(row.avg_heart_rate)">
              <el-icon><Cpu /></el-icon>
              {{ row.avg_heart_rate }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="训练时长" width="130" align="center">
          <template #default="{ row }">
            <span class="dur-text">{{ row.duration }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" :icon="View" @click="openDetail(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-drawer
      v-model="drawerVisible"
      :title="`训练详情 - ${currentSession?.date || ''}`"
      direction="rtl"
      size="70%"
      class="detail-drawer"
      destroy-on-close
    >
      <div v-loading="detailLoading" class="drawer-content">
        <el-row :gutter="16">
          <el-col :xs="12" :sm="12" :md="6">
            <el-card class="mini-stat ms-blue" shadow="hover">
              <el-icon class="msi"><Location /></el-icon>
              <div class="msv">{{ ((currentSession?.total_distance || 0) / 1000).toFixed(2) }}<span>km</span></div>
              <div class="msl">总距离</div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="12" :md="6">
            <el-card class="mini-stat ms-green" shadow="hover">
              <el-icon class="msi"><Timer /></el-icon>
              <div class="msv">{{ currentSession?.duration || '00:00:00' }}</div>
              <div class="msl">总时长</div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="12" :md="6">
            <el-card class="mini-stat ms-orange" shadow="hover">
              <el-icon class="msi"><Cpu /></el-icon>
              <div class="msv">{{ currentSession?.avg_heart_rate || 0 }}<span>bpm</span></div>
              <div class="msl">平均心率</div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="12" :md="6">
            <el-card class="mini-stat ms-purple" shadow="hover">
              <el-icon class="msi"><TrendCharts /></el-icon>
              <div class="msv">{{ currentSession?.avg_pace || '-' }}<span>/100m</span></div>
              <div class="msl">平均配速</div>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="16" style="margin-top: 18px;">
          <el-col :md="12" :sm="24">
            <el-card class="chart-card" shadow="hover">
              <template #header>
                <span class="card-title">
                  <el-icon class="title-icon"><Cpu /></el-icon>
                  心率曲线
                </span>
              </template>
              <div ref="hrChartRef" class="chart-md"></div>
            </el-card>
          </el-col>
          <el-col :md="12" :sm="24">
            <el-card class="chart-card" shadow="hover">
              <template #header>
                <span class="card-title">
                  <el-icon class="title-icon"><DataLine /></el-icon>
                  每圈配速
                </span>
              </template>
              <div ref="paceChartRef" class="chart-md"></div>
            </el-card>
          </el-col>
        </el-row>

        <el-card v-if="suggestionVisible" class="sug-card" shadow="hover" style="margin-top: 18px;">
          <template #header>
            <span class="card-title">
              <el-icon class="title-icon" style="color:#8b5cf6;"><MagicStick /></el-icon>
              教练建议
            </span>
            <el-tag type="success" effect="dark" size="small">AI + 教练</el-tag>
          </template>
          <el-row :gutter="20">
            <el-col :md="12" :sm="24">
              <div class="sug-row">
                <span class="sug-label">AI建议配速</span>
                <el-tag type="primary" effect="plain" size="large">{{ suggestion.suggested_pace || '-' }} /100m</el-tag>
              </div>
              <div class="sug-row">
                <span class="sug-label">AI建议间歇</span>
                <el-tag type="warning" effect="plain" size="large">{{ suggestion.suggested_rest || '-' }} 秒</el-tag>
              </div>
              <div v-if="suggestion.modified_pace" class="sug-row">
                <span class="sug-label">教练调整配速</span>
                <el-tag type="success" effect="plain" size="large">{{ suggestion.modified_pace }} /100m</el-tag>
              </div>
              <div v-if="suggestion.modified_rest !== undefined" class="sug-row">
                <span class="sug-label">教练调整间歇</span>
                <el-tag type="info" effect="plain" size="large">{{ suggestion.modified_rest }} 秒</el-tag>
              </div>
            </el-col>
            <el-col :md="12" :sm="24">
              <div class="reason-block">
                <div class="reason-head">
                  <el-icon style="color:#0052d9;"><InfoFilled /></el-icon>
                  <span>原因分析</span>
                </div>
                <p class="reason-text">{{ suggestion.reason || '暂无' }}</p>
              </div>
              <div v-if="suggestion.coach_notes" class="notes-block">
                <div class="notes-head">
                  <el-icon style="color:#10b981;"><ChatDotRound /></el-icon>
                  <span>教练备注</span>
                </div>
                <p class="notes-text">{{ suggestion.coach_notes }}</p>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Location, Trophy, Timer, Cpu, List, Calendar, View, TrendCharts,
  DataLine, MagicStick, InfoFilled, ChatDotRound
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'

const userStore = useUserStore()
const loading = ref(false)
const detailLoading = ref(false)
const drawerVisible = ref(false)
const sessionList = ref([])
const currentSession = ref(null)
const suggestionVisible = ref(false)

const totalStats = reactive({
  distance: 0,
  count: 0,
  bestPace: '1:30',
  avgHr: 0
})

const suggestion = reactive({
  suggested_pace: '',
  suggested_rest: '',
  modified_pace: '',
  modified_rest: undefined,
  reason: '',
  coach_notes: ''
})

const hrChartRef = ref(null)
const paceChartRef = ref(null)
let hrChart = null
let paceChart = null

const getPaceType = (pace) => {
  if (!pace) return 'info'
  const [m, s] = pace.split(':').map(n => parseInt(n) || 0)
  const sec = m * 60 + s
  if (sec <= 90) return 'success'
  if (sec <= 110) return 'warning'
  return 'danger'
}
const getHrClass = (hr) => {
  if (!hr) return ''
  if (hr < 130) return 'hr-low'
  if (hr < 160) return 'hr-mid'
  return 'hr-high'
}

const mockHR = () => {
  const data = []
  for (let i = 0; i < 50; i++) {
    data.push([`${Math.floor(i / 60)}:${String(i % 60).padStart(2, '0')}`, Math.round(120 + Math.sin(i / 5) * 28 + Math.random() * 6)])
  }
  return data
}
const mockPaces = () => {
  const names = [], vals = []
  for (let i = 1; i <= 12; i++) {
    names.push(`L${i}`)
    vals.push(82 + Math.round(Math.random() * 22))
  }
  return { names, vals }
}

const fetchSessions = async () => {
  loading.value = true
  try {
    const res = await request({
      method: 'GET',
      url: '/api/data/sessions',
      params: { athlete_id: userStore.userId }
    })
    if (res.data) {
      sessionList.value = res.data.data || res.data || []
    }
  } catch {
    sessionList.value = [
      { id: 201, date: '2024-06-12', total_distance: 3200, avg_pace: '1:28', avg_heart_rate: 148, duration: '00:58:30' },
      { id: 202, date: '2024-06-11', total_distance: 2600, avg_pace: '1:32', avg_heart_rate: 140, duration: '00:48:45' },
      { id: 203, date: '2024-06-10', total_distance: 3000, avg_pace: '1:30', avg_heart_rate: 145, duration: '00:55:10' },
      { id: 204, date: '2024-06-08', total_distance: 2800, avg_pace: '1:35', avg_heart_rate: 138, duration: '00:55:20' },
      { id: 205, date: '2024-06-07', total_distance: 3400, avg_pace: '1:25', avg_heart_rate: 155, duration: '01:02:10' },
      { id: 206, date: '2024-06-06', total_distance: 2200, avg_pace: '1:40', avg_heart_rate: 130, duration: '00:50:00' }
    ]
  } finally {
    loading.value = false
    calcStats()
  }
}

const calcStats = () => {
  totalStats.count = sessionList.value.length
  totalStats.distance = sessionList.value.reduce((sum, s) => sum + (parseInt(s.total_distance) || 0), 0)
  const hrs = sessionList.value.map(s => s.avg_heart_rate).filter(Boolean)
  totalStats.avgHr = hrs.length ? Math.round(hrs.reduce((a, b) => a + b, 0) / hrs.length) : 0
  let best = 999
  sessionList.value.forEach(s => {
    if (!s.avg_pace) return
    const [m, sec] = s.avg_pace.split(':').map(n => parseInt(n) || 0)
    const t = m * 60 + sec
    if (t && t < best) { best = t; totalStats.bestPace = s.avg_pace }
  })
}

const openDetail = async (row) => {
  currentSession.value = row
  drawerVisible.value = true
  detailLoading.value = true
  suggestionVisible.value = false
  Object.keys(suggestion).forEach(k => suggestion[k] = k === 'modified_rest' ? undefined : '')
  try {
    const res = await request({ method: 'GET', url: `/api/data/session/${row.id}` })
    if (res.data) {
      const d = res.data.data || res.data
      Object.assign(currentSession.value, d)
    }
  } catch {
    currentSession.value = {
      ...row,
      hr_series: mockHR(),
      lap_paces: mockPaces()
    }
  }
  try {
    const sRes = await request({
      method: 'GET',
      url: '/api/training/suggestions',
      params: { session_id: row.id }
    })
    if (sRes.data) {
      const s = (sRes.data.data || sRes.data || [])[0] || sRes.data.data || sRes.data || {}
      if (s && (s.suggested_pace || s.reason || s.coach_notes)) {
        Object.assign(suggestion, s)
        suggestionVisible.value = true
      }
    }
  } catch {
    suggestion.suggested_pace = '1:28'
    suggestion.suggested_rest = '60'
    suggestion.modified_pace = '1:30'
    suggestion.modified_rest = 70
    suggestion.reason = '本次训练整体完成较好，配速稳定性有所提升，建议下次训练适当增加强度，减少间歇时间以突破瓶颈。'
    suggestion.coach_notes = '加油，下周强度课继续保持这个状态，注意补水！'
    suggestionVisible.value = true
  }
  detailLoading.value = false
  await nextTick()
  initCharts()
}

const initCharts = () => {
  if (hrChartRef.value) {
    hrChart?.dispose()
    hrChart = echarts.init(hrChartRef.value)
    const data = currentSession.value?.hr_series || mockHR()
    hrChart.setOption({
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(0,30,80,0.95)', borderColor: '#ef4444', textStyle: { color: '#fff' } },
      grid: { left: 50, right: 20, top: 30, bottom: 40 },
      xAxis: { type: 'category', data: data.map(d => d[0]), axisLine: { lineStyle: { color: '#e0e6ed' } }, axisLabel: { color: '#606266', fontSize: 10, interval: 4 } },
      yAxis: { type: 'value', min: 80, max: 200, name: 'bpm', nameTextStyle: { color: '#909399' }, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#606266' }, splitLine: { lineStyle: { color: '#f0f2f5' } } },
      series: [{ type: 'line', smooth: true, showSymbol: false, data: data.map(d => d[1]), lineStyle: { width: 2.5, color: '#ef4444' }, itemStyle: { color: '#ef4444' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(239,68,68,0.4)' }, { offset: 1, color: 'rgba(239,68,68,0.02)' }]) } }]
    })
  }
  if (paceChartRef.value) {
    paceChart?.dispose()
    paceChart = echarts.init(paceChartRef.value)
    const laps = currentSession.value?.lap_paces || mockPaces()
    paceChart.setOption({
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(0,30,80,0.95)', borderColor: '#0052d9', textStyle: { color: '#fff' } },
      grid: { left: 50, right: 20, top: 30, bottom: 40 },
      xAxis: { type: 'category', data: laps.names, axisLine: { lineStyle: { color: '#e0e6ed' } }, axisLabel: { color: '#606266', fontSize: 10 } },
      yAxis: { type: 'value', min: 70, max: 120, inverse: true, name: '秒/100m', nameTextStyle: { color: '#909399' }, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#606266' }, splitLine: { lineStyle: { color: '#f0f2f5' } } },
      series: [{ type: 'bar', data: laps.vals, barWidth: '55%', itemStyle: { borderRadius: [5, 5, 0, 0], color: p => p.value < 90 ? '#10b981' : p.value < 100 ? '#f59e0b' : '#ef4444' } }]
    })
  }
}

const handleResize = () => {
  hrChart?.resize()
  paceChart?.resize()
}

onMounted(async () => {
  await fetchSessions()
  window.addEventListener('resize', handleResize)
})
</script>

<style scoped>
.mydata-container { display: flex; flex-direction: column; gap: 20px; }

.page-header { display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 14px; }
.page-title { margin: 0 0 6px 0; font-size: 24px; font-weight: 700; color: #1a1a2e; }
.page-subtitle { margin: 0; color: #8c8c8c; font-size: 14px; }

.user-info { display: flex; align-items: center; gap: 12px; background: #fff; padding: 8px 16px; border-radius: 28px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.my-avatar { background: linear-gradient(135deg, #0052d9, #003d9e); color: #fff; font-weight: 700; }
.user-name { font-weight: 700; color: #1a1a2e; font-size: 14px; }
.user-sub { font-size: 12px; color: #8c8c8c; }

.summary-card, .table-card, .mini-stat, .chart-card, .sug-card { border: none; border-radius: 14px; }
.summary-card :deep(.el-card__body) { padding: 20px 10px; }

.sm-item { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 8px 6px; }
.sm-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 20px; margin-bottom: 6px; }
.sm-blue { background: linear-gradient(135deg, #0052d9, #003d9e); }
.sm-green { background: linear-gradient(135deg, #10b981, #059669); }
.sm-orange { background: linear-gradient(135deg, #f59e0b, #d97706); }
.sm-purple { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }
.sm-val { font-size: 22px; font-weight: 800; color: #1a1a2e; line-height: 1.2; }
.sm-val span { font-size: 12px; color: #8c8c8c; margin-left: 2px; font-weight: 500; }
.sm-lbl { font-size: 12px; color: #8c8c8c; }

.table-card :deep(.el-card__header),
.chart-card :deep(.el-card__header),
.sug-card :deep(.el-card__header) { padding: 16px 20px; border-bottom: 1px solid #f0f2f5; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-size: 16px; font-weight: 600; color: #1a1a2e; display: flex; align-items: center; gap: 8px; }
.title-icon { color: #0052d9; }

.date-cell { display: flex; align-items: center; gap: 6px; color: #606266; font-size: 13px; }
.date-icon { color: #0052d9; }
.highlight { font-weight: 700; color: #0052d9; }
.hr-low { color: #10b981; font-weight: 500; display: inline-flex; align-items: center; gap: 3px; }
.hr-mid { color: #f59e0b; font-weight: 500; display: inline-flex; align-items: center; gap: 3px; }
.hr-high { color: #ef4444; font-weight: 500; display: inline-flex; align-items: center; gap: 3px; }
.dur-text { color: #606266; font-weight: 500; }

.detail-drawer :deep(.el-drawer__header) {
  background: linear-gradient(135deg, #0052d9, #003d9e);
  color: #fff; margin: 0; padding: 18px 24px;
}
.detail-drawer :deep(.el-drawer__title) { color: #fff; font-weight: 600; }
.detail-drawer :deep(.el-drawer__close-btn) { color: #fff; }
.detail-drawer :deep(.el-drawer__body) { background: #f5f7fa; padding: 20px 24px; }

.mini-stat :deep(.el-card__body) { padding: 16px; position: relative; }
.msi { width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; color: #fff; margin-bottom: 10px; }
.ms-blue .msi { background: linear-gradient(135deg, #0052d9, #003d9e); }
.ms-green .msi { background: linear-gradient(135deg, #10b981, #059669); }
.ms-orange .msi { background: linear-gradient(135deg, #f59e0b, #d97706); }
.ms-purple .msi { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }
.msv { font-size: 22px; font-weight: 700; color: #1a1a2e; line-height: 1.2; }
.msv span { font-size: 12px; color: #8c8c8c; margin-left: 2px; font-weight: 500; }
.msl { font-size: 12px; color: #8c8c8c; margin-top: 3px; }

.chart-md { width: 100%; height: 280px; }

.sug-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px dashed #f0f2f5; }
.sug-label { font-size: 14px; color: #606266; font-weight: 500; }

.reason-block, .notes-block { padding: 12px 0; }
.reason-head, .notes-head { display: flex; align-items: center; gap: 6px; font-weight: 600; margin-bottom: 8px; }
.reason-head { color: #1a1a2e; }
.notes-head { color: #1a1a2e; margin-top: 10px; }
.reason-text, .notes-text { margin: 0; line-height: 1.7; color: #606266; font-size: 13px; }
.reason-text { padding: 10px 14px; background: #fafcff; border-left: 3px solid #0052d9; border-radius: 0 8px 8px 0; }
.notes-text { padding: 10px 14px; background: #f0fdf4; border-left: 3px solid #10b981; border-radius: 0 8px 8px 0; }
</style>
