<template>
  <div class="data-container">
    <div class="page-header">
      <div>
        <h2 class="page-title">训练数据</h2>
        <p class="page-subtitle">查看和分析运动员的每次训练详细数据与AI建议</p>
      </div>
    </div>

    <el-card class="filter-card" shadow="hover">
      <div class="filter-bar">
        <div class="filter-item">
          <span class="filter-label">运动员</span>
          <el-select
            v-model="filter.athlete_id"
            placeholder="全部运动员"
            filterable
            clearable
            class="filter-select"
          >
            <el-option
              v-for="a in athleteList"
              :key="a.id"
              :label="`${a.name} (${a.group})`"
              :value="a.id"
            />
          </el-select>
        </div>
        <div class="filter-item">
          <span class="filter-label">日期范围</span>
          <el-date-picker
            v-model="filter.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            class="filter-range"
          />
        </div>
        <el-button type="primary" @click="fetchSessions" :icon="Search" :loading="loading">
          查询
        </el-button>
        <el-button @click="resetFilter" :icon="RefreshLeft">
          重置
        </el-button>
      </div>
    </el-card>

    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon class="title-icon"><List /></el-icon>
            训练记录 ({{ sessionList.length }}条)
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
        <el-table-column prop="athlete_name" label="运动员" min-width="130">
          <template #default="{ row }">
            <div class="athlete-cell">
              <el-avatar :size="32" class="mini-avatar">
                {{ row.athlete_name?.charAt(0) }}
              </el-avatar>
              <span>{{ row.athlete_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="total_distance" label="总距离(米)" width="130" align="center" sortable>
          <template #default="{ row }">
            <span class="highlight-num">{{ row.total_distance?.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="avg_pace" label="平均配速" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="getPaceType(row.avg_pace)" effect="plain">
              {{ row.avg_pace }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="avg_heart_rate" label="平均心率" width="130" align="center">
          <template #default="{ row }">
            <div class="hr-cell">
              <el-icon><Cpu /></el-icon>
              <span :class="getHrClass(row.avg_heart_rate)">{{ row.avg_heart_rate }} bpm</span>
            </div>
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
      :title="`训练详情 - ${currentSession?.athlete_name || ''}`"
      direction="rtl"
      size="75%"
      class="detail-drawer"
      destroy-on-close
    >
      <div v-loading="detailLoading" class="drawer-content">
        <el-row :gutter="16">
          <el-col :xs="12" :sm="12" :md="6">
            <el-card class="mini-stat mini-blue" shadow="hover">
              <el-icon class="ms-icon"><Location /></el-icon>
              <div class="ms-val">{{ (currentSession?.total_distance / 1000 || 0).toFixed(2) }}<span>km</span></div>
              <div class="ms-lbl">总距离</div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="12" :md="6">
            <el-card class="mini-stat mini-green" shadow="hover">
              <el-icon class="ms-icon"><Timer /></el-icon>
              <div class="ms-val">{{ currentSession?.duration || '00:00:00' }}</div>
              <div class="ms-lbl">总时长</div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="12" :md="6">
            <el-card class="mini-stat mini-orange" shadow="hover">
              <el-icon class="ms-icon"><Cpu /></el-icon>
              <div class="ms-val">{{ currentSession?.avg_heart_rate || 0 }}<span>bpm</span></div>
              <div class="ms-lbl">平均心率</div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="12" :md="6">
            <el-card class="mini-stat mini-purple" shadow="hover">
              <el-icon class="ms-icon"><TrendCharts /></el-icon>
              <div class="ms-val">{{ currentSession?.avg_pace || '-' }}<span>/100m</span></div>
              <div class="ms-lbl">平均配速</div>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="16" style="margin-top: 18px;">
          <el-col :lg="14" :md="24">
            <el-card class="chart-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <span class="card-title">
                    <el-icon class="title-icon"><Cpu /></el-icon>
                    心率曲线
                  </span>
                </div>
              </template>
              <div ref="hrChartRef" class="chart-md"></div>
            </el-card>
          </el-col>
          <el-col :lg="10" :md="24">
            <el-card class="chart-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <span class="card-title">
                    <el-icon class="title-icon"><DataLine /></el-icon>
                    每圈配速
                  </span>
                </div>
              </template>
              <div ref="paceChartRef" class="chart-md"></div>
            </el-card>
          </el-col>
        </el-row>

        <el-card class="chart-card" shadow="hover" style="margin-top: 18px;">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon class="title-icon"><DataAnalysis /></el-icon>
                技术指标：划距 &amp; 身体转动
              </span>
            </div>
          </template>
          <div ref="strokeChartRef" class="chart-lg"></div>
        </el-card>

        <el-row :gutter="16" style="margin-top: 18px;">
          <el-col :md="12" :sm="24">
            <el-card class="ai-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <span class="card-title">
                    <el-icon class="title-icon ai-icon"><MagicStick /></el-icon>
                    AI 训练建议
                  </span>
                  <el-tag type="success" effect="dark" size="small">AI V2.0</el-tag>
                </div>
              </template>
              <div class="ai-body">
                <div class="ai-row">
                  <span class="ai-label">建议配速</span>
                  <el-tag type="primary" effect="plain" size="large" class="ai-tag">
                    {{ suggestion.suggested_pace || '1:28' }} /100m
                  </el-tag>
                </div>
                <div class="ai-row">
                  <span class="ai-label">建议间歇</span>
                  <el-tag type="warning" effect="plain" size="large" class="ai-tag">
                    {{ suggestion.suggested_rest || '60' }} 秒
                  </el-tag>
                </div>
                <el-divider />
                <div class="ai-reason">
                  <el-icon class="reason-icon"><InfoFilled /></el-icon>
                  <span>原因分析</span>
                </div>
                <p class="ai-reason-text">
                  {{ suggestion.reason || '根据本次训练数据，运动员配速波动较大，建议在保持现有距离基础上，适当降低每组间歇时间以提升有氧耐力。心率曲线显示第3组后体能下降明显，可增加热身距离并调整强度区间。' }}
                </p>
              </div>
            </el-card>
          </el-col>

          <el-col :md="12" :sm="24">
            <el-card class="form-card-inner" shadow="hover">
              <template #header>
                <div class="card-header">
                  <span class="card-title">
                    <el-icon class="title-icon"><Edit /></el-icon>
                    教练调整 &amp; 备注
                  </span>
                </div>
              </template>
              <el-form :model="coachForm" label-width="100px" label-position="right" class="coach-form">
                <el-form-item label="调整后配速">
                  <div class="pace-inputs">
                    <el-input-number
                      v-model="coachForm.modified_pace_min"
                      :min="0"
                      :max="5"
                      placeholder="分"
                    />
                    <span class="pace-sep">:</span>
                    <el-input-number
                      v-model="coachForm.modified_pace_sec"
                      :min="0"
                      :max="59"
                      placeholder="秒"
                    />
                    <span class="input-unit">/100m</span>
                  </div>
                </el-form-item>
                <el-form-item label="调整后间歇">
                  <el-input-number
                    v-model="coachForm.modified_rest"
                    :min="0"
                    :max="1800"
                    :step="10"
                    style="width: calc(100% - 60px)"
                  />
                  <span class="input-unit">秒</span>
                </el-form-item>
                <el-form-item label="教练备注">
                  <el-input
                    v-model="coachForm.coach_notes"
                    type="textarea"
                    :rows="4"
                    placeholder="根据AI建议结合您的判断，输入调整说明..."
                    maxlength="300"
                    show-word-limit
                  />
                </el-form-item>
                <div class="form-actions">
                  <el-button
                    type="primary"
                    size="large"
                    :icon="Check"
                    :loading="saving"
                    @click="saveSuggestion"
                  >
                    保存修改
                  </el-button>
                </div>
              </el-form>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search, RefreshLeft, Calendar, List, View, Location, Timer,
  Cpu, TrendCharts, DataLine, DataAnalysis, MagicStick, InfoFilled, Edit, Check
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import request from '@/utils/request'

const loading = ref(false)
const detailLoading = ref(false)
const saving = ref(false)
const drawerVisible = ref(false)
const sessionList = ref([])
const athleteList = ref([])
const currentSession = ref(null)

const filter = reactive({
  athlete_id: null,
  dateRange: []
})

const hrChartRef = ref(null)
const paceChartRef = ref(null)
const strokeChartRef = ref(null)
let hrChart = null
let paceChart = null
let strokeChart = null

const suggestion = reactive({
  id: null,
  suggested_pace: '',
  suggested_rest: '',
  reason: ''
})

const coachForm = reactive({
  modified_pace_min: 1,
  modified_pace_sec: 28,
  modified_rest: 60,
  coach_notes: ''
})

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

const resetFilter = () => {
  filter.athlete_id = null
  filter.dateRange = []
  fetchSessions()
}

const fetchAthletes = async () => {
  try {
    const res = await request({ method: 'GET', url: '/api/auth/athletes' })
    if (res.data) {
      athleteList.value = res.data.data || res.data || []
    }
  } catch {
    athleteList.value = [
      { id: 1, name: '张伟', group: '一组' },
      { id: 2, name: '李娜', group: '一组' },
      { id: 3, name: '王强', group: '二组' }
    ]
  }
}

const fetchSessions = async () => {
  loading.value = true
  try {
    const params = {}
    if (filter.athlete_id) params.athlete_id = filter.athlete_id
    if (filter.dateRange?.length === 2) {
      params.start_date = filter.dateRange[0]
      params.end_date = filter.dateRange[1]
    }
    const res = await request({
      method: 'GET',
      url: '/api/data/sessions',
      params
    })
    if (res.data) {
      sessionList.value = res.data.data || res.data || []
    }
  } catch {
    sessionList.value = [
      { id: 101, date: '2024-06-12', athlete_name: '张伟', total_distance: 3200, avg_pace: '1:28', avg_heart_rate: 148, duration: '00:58:30' },
      { id: 102, date: '2024-06-12', athlete_name: '李娜', total_distance: 2800, avg_pace: '1:35', avg_heart_rate: 138, duration: '00:55:20' },
      { id: 103, date: '2024-06-11', athlete_name: '王强', total_distance: 3500, avg_pace: '1:22', avg_heart_rate: 155, duration: '01:02:10' },
      { id: 104, date: '2024-06-11', athlete_name: '张伟', total_distance: 2600, avg_pace: '1:32', avg_heart_rate: 140, duration: '00:48:45' },
      { id: 105, date: '2024-06-10', athlete_name: '李娜', total_distance: 3000, avg_pace: '1:33', avg_heart_rate: 142, duration: '00:55:12' },
      { id: 106, date: '2024-06-10', athlete_name: '赵敏', total_distance: 2400, avg_pace: '1:40', avg_heart_rate: 135, duration: '00:52:00' }
    ]
  } finally {
    loading.value = false
  }
}

const fetchSuggestion = async (sessionId) => {
  try {
    const res = await request({
      method: 'GET',
      url: '/api/training/suggestions',
      params: { session_id: sessionId }
    })
    if (res.data) {
      const s = (res.data.data || res.data || [])[0] || res.data.data || res.data || {}
      suggestion.id = s.id || null
      suggestion.suggested_pace = s.suggested_pace || ''
      suggestion.suggested_rest = s.suggested_rest || ''
      suggestion.reason = s.reason || ''
      if (s.suggested_pace) {
        const [m, sec] = s.suggested_pace.split(':').map(n => parseInt(n) || 0)
        coachForm.modified_pace_min = m
        coachForm.modified_pace_sec = sec
      }
      if (s.modified_rest !== undefined) coachForm.modified_rest = s.modified_rest
      if (s.coach_notes) coachForm.coach_notes = s.coach_notes
    }
  } catch {
    suggestion.suggested_pace = '1:28'
    suggestion.suggested_rest = '60'
    suggestion.reason = '根据本次训练数据，运动员配速波动较大，建议在保持现有距离基础上，适当降低每组间歇时间以提升有氧耐力。心率曲线显示第3组后体能下降明显，可增加热身距离并调整强度区间。'
  }
}

const openDetail = async (row) => {
  currentSession.value = row
  drawerVisible.value = true
  detailLoading.value = true
  try {
    const res = await request({
      method: 'GET',
      url: `/api/data/session/${row.id}`
    })
    if (res.data) {
      const d = res.data.data || res.data
      if (d) Object.assign(currentSession.value, d)
    }
  } catch {
    currentSession.value = {
      ...row,
      hr_series: generateMockHR(),
      lap_paces: generateMockPaces(),
      stroke_length: generateMockStroke(),
      body_rotation: generateMockRotation()
    }
  }
  await fetchSuggestion(row.id)
  detailLoading.value = false
  await nextTick()
  initCharts()
}

const generateMockHR = () => {
  const data = []
  for (let i = 0; i < 60; i++) {
    data.push([`${Math.floor(i / 60)}:${String(i % 60).padStart(2, '0')}`, Math.round(115 + Math.sin(i / 6) * 30 + Math.random() * 8)])
  }
  return data
}
const generateMockPaces = () => {
  const names = [], vals = []
  for (let i = 1; i <= 16; i++) {
    names.push(`L${i}`)
    vals.push(80 + Math.round(Math.random() * 25))
  }
  return { names, vals }
}
const generateMockStroke = () => Array.from({ length: 16 }, () => (Math.random() * 0.5 + 1.8).toFixed(2))
const generateMockRotation = () => Array.from({ length: 16 }, () => (Math.random() * 20 + 40).toFixed(1))

const initCharts = () => {
  initHRChart()
  initPaceChart()
  initStrokeChart()
}

const initHRChart = () => {
  if (!hrChartRef.value) return
  hrChart?.dispose()
  hrChart = echarts.init(hrChartRef.value)
  const data = currentSession.value?.hr_series || generateMockHR()
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 30, 80, 0.95)',
      borderColor: '#ef4444',
      textStyle: { color: '#fff' },
      formatter: (p) => `${p[0].value[0]}<br/>心率: <b>${p[0].value[1]}</b> bpm`
    },
    grid: { left: 50, right: 30, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      data: data.map(d => d[0]),
      axisLine: { lineStyle: { color: '#e0e6ed' } },
      axisLabel: { color: '#606266', fontSize: 10, interval: 5 }
    },
    yAxis: {
      type: 'value',
      min: 80,
      max: 200,
      name: 'bpm',
      nameTextStyle: { color: '#909399' },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#606266' },
      splitLine: { lineStyle: { color: '#f0f2f5' } }
    },
    series: [{
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: data.map(d => d[1]),
      lineStyle: { width: 2.5, color: '#ef4444' },
      itemStyle: { color: '#ef4444' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(239, 68, 68, 0.45)' },
          { offset: 1, color: 'rgba(239, 68, 68, 0.02)' }
        ])
      },
      markLine: {
        silent: true,
        lineStyle: { color: '#f59e0b', type: 'dashed' },
        data: [{ yAxis: 160, label: { formatter: '极限 {c}', color: '#f59e0b' } }]
      }
    }]
  }
  hrChart.setOption(option)
}

const initPaceChart = () => {
  if (!paceChartRef.value) return
  paceChart?.dispose()
  paceChart = echarts.init(paceChartRef.value)
  const laps = currentSession.value?.lap_paces || generateMockPaces()
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 30, 80, 0.95)',
      borderColor: '#0052d9',
      textStyle: { color: '#fff' },
      formatter: (p) => `${p[0].name}<br/>配速: <b>${formatPace(p[0].value)}</b>`
    },
    grid: { left: 50, right: 20, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      data: laps.names,
      axisLine: { lineStyle: { color: '#e0e6ed' } },
      axisLabel: { color: '#606266', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      min: 70,
      max: 120,
      inverse: true,
      name: '秒/100m',
      nameTextStyle: { color: '#909399' },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#606266' },
      splitLine: { lineStyle: { color: '#f0f2f5' } }
    },
    series: [{
      type: 'bar',
      data: laps.vals,
      barWidth: '55%',
      itemStyle: {
        borderRadius: [5, 5, 0, 0],
        color: (p) => {
          if (p.value < 90) return '#10b981'
          if (p.value < 100) return '#f59e0b'
          return '#ef4444'
        }
      }
    }]
  }
  paceChart.setOption(option)
}

const formatPace = (sec) => {
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

const initStrokeChart = () => {
  if (!strokeChartRef.value) return
  strokeChart?.dispose()
  strokeChart = echarts.init(strokeChartRef.value)
  const lapNames = (currentSession.value?.lap_paces || generateMockPaces()).names
  const sl = currentSession.value?.stroke_length || generateMockStroke()
  const br = currentSession.value?.body_rotation || generateMockRotation()
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 30, 80, 0.95)',
      borderColor: '#0052d9',
      textStyle: { color: '#fff' }
    },
    legend: {
      data: ['划距(m)', '身体转动(°)'],
      top: 0,
      textStyle: { color: '#606266' }
    },
    grid: { left: 55, right: 55, top: 45, bottom: 40 },
    xAxis: {
      type: 'category',
      data: lapNames,
      axisLine: { lineStyle: { color: '#e0e6ed' } },
      axisLabel: { color: '#606266' }
    },
    yAxis: [
      {
        type: 'value',
        name: '划距(m)',
        min: 1.0,
        max: 3.0,
        nameTextStyle: { color: '#0052d9' },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#0052d9' },
        splitLine: { lineStyle: { color: '#f0f2f5' } }
      },
      {
        type: 'value',
        name: '转动(°)',
        min: 20,
        max: 70,
        nameTextStyle: { color: '#8b5cf6' },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#8b5cf6' },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '划距(m)',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 7,
        data: sl,
        lineStyle: { width: 2.5, color: '#0052d9' },
        itemStyle: { color: '#0052d9', borderColor: '#fff', borderWidth: 2 }
      },
      {
        name: '身体转动(°)',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbol: 'diamond',
        symbolSize: 7,
        data: br,
        lineStyle: { width: 2.5, color: '#8b5cf6' },
        itemStyle: { color: '#8b5cf6', borderColor: '#fff', borderWidth: 2 }
      }
    ]
  }
  strokeChart.setOption(option)
}

const saveSuggestion = async () => {
  saving.value = true
  try {
    const payload = {
      session_id: currentSession.value?.id,
      suggested_pace: suggestion.suggested_pace,
      suggested_rest: suggestion.suggested_rest,
      reason: suggestion.reason,
      modified_pace: `${coachForm.modified_pace_min}:${String(coachForm.modified_pace_sec).padStart(2, '0')}`,
      modified_rest: coachForm.modified_rest,
      coach_notes: coachForm.coach_notes
    }
    let res
    if (suggestion.id) {
      res = await request({
        method: 'PUT',
        url: `/api/training/suggestion/${suggestion.id}`,
        data: payload
      })
    } else {
      res = await request({
        method: 'POST',
        url: '/api/training/suggestions',
        data: payload
      })
    }
    if (res.data) ElMessage.success('修改已保存')
  } catch {
    ElMessage.success('修改已保存 (模拟)')
  } finally {
    saving.value = false
  }
}

const handleResize = () => {
  hrChart?.resize()
  paceChart?.resize()
  strokeChart?.resize()
}

onMounted(async () => {
  await fetchAthletes()
  await fetchSessions()
  window.addEventListener('resize', handleResize)
})
</script>

<style scoped>
.data-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}
.page-title { margin: 0 0 6px 0; font-size: 24px; font-weight: 700; color: #1a1a2e; }
.page-subtitle { margin: 0; color: #8c8c8c; font-size: 14px; }

.filter-card, .table-card { border: none; border-radius: 14px; }
.filter-card :deep(.el-card__body) { padding: 16px 20px; }
.filter-bar { display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
.filter-item { display: flex; align-items: center; gap: 10px; }
.filter-label { font-size: 14px; color: #606266; font-weight: 500; white-space: nowrap; }
.filter-select { width: 220px; }
.filter-range { width: 300px; }

.table-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f2f5;
}
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title {
  font-size: 16px; font-weight: 600; color: #1a1a2e;
  display: flex; align-items: center; gap: 8px;
}
.title-icon { color: #0052d9; }
.ai-icon { color: #8b5cf6 !important; }

.date-cell { display: flex; align-items: center; gap: 6px; color: #606266; font-size: 13px; }
.date-icon { color: #0052d9; }
.athlete-cell { display: flex; align-items: center; gap: 10px; }
.mini-avatar {
  background: linear-gradient(135deg, #0052d9, #003d9e);
  color: #fff; font-size: 12px; font-weight: 600;
}
.highlight-num { font-weight: 700; color: #0052d9; }
.hr-cell { display: inline-flex; align-items: center; gap: 4px; font-weight: 500; }
.hr-low { color: #10b981; }
.hr-mid { color: #f59e0b; }
.hr-high { color: #ef4444; }

.detail-drawer :deep(.el-drawer__header) {
  background: linear-gradient(135deg, #0052d9, #003d9e);
  color: #fff;
  margin: 0;
  padding: 18px 24px;
}
.detail-drawer :deep(.el-drawer__title) { color: #fff; font-weight: 600; }
.detail-drawer :deep(.el-drawer__close-btn) { color: #fff; }
.detail-drawer :deep(.el-drawer__body) { background: #f5f7fa; padding: 20px 24px; }

.drawer-content { min-height: 100%; }

.mini-stat {
  border: none; border-radius: 12px; position: relative; overflow: hidden;
}
.mini-stat :deep(.el-card__body) {
  padding: 16px; display: flex; flex-direction: column; align-items: flex-start; gap: 6px;
  position: relative; z-index: 1;
}
.mini-stat::before {
  content: ''; position: absolute; right: -20px; top: -20px;
  width: 90px; height: 90px; border-radius: 50%; opacity: 0.12;
}
.mini-blue::before { background: #0052d9; }
.mini-green::before { background: #10b981; }
.mini-orange::before { background: #f59e0b; }
.mini-purple::before { background: #8b5cf6; }
.ms-icon {
  font-size: 22px; width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center; color: #fff;
}
.mini-blue .ms-icon { background: linear-gradient(135deg, #0052d9, #003d9e); }
.mini-green .ms-icon { background: linear-gradient(135deg, #10b981, #059669); }
.mini-orange .ms-icon { background: linear-gradient(135deg, #f59e0b, #d97706); }
.mini-purple .ms-icon { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }
.ms-val { font-size: 24px; font-weight: 700; color: #1a1a2e; line-height: 1.2; }
.ms-val span { font-size: 13px; color: #8c8c8c; margin-left: 3px; font-weight: 500; }
.ms-lbl { font-size: 12px; color: #8c8c8c; }

.chart-card, .ai-card, .form-card-inner { border: none; border-radius: 12px; }
.chart-card :deep(.el-card__header),
.ai-card :deep(.el-card__header),
.form-card-inner :deep(.el-card__header) {
  padding: 14px 18px;
  border-bottom: 1px solid #f0f2f5;
}
.chart-md { width: 100%; height: 280px; }
.chart-lg { width: 100%; height: 320px; }

.ai-body { padding: 6px 4px; }
.ai-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 0;
  border-bottom: 1px dashed #f0f2f5;
}
.ai-label { font-size: 14px; color: #606266; font-weight: 500; }
.ai-tag { font-weight: 600; }
.ai-reason {
  display: flex; align-items: center; gap: 6px;
  margin: 12px 0 8px; font-weight: 600; color: #1a1a2e;
}
.reason-icon { color: #0052d9; }
.ai-reason-text {
  margin: 0; line-height: 1.7; color: #606266; font-size: 13px;
  padding: 10px 14px; background: #fafcff; border-radius: 8px;
  border-left: 3px solid #0052d9;
}

.coach-form { padding: 6px 4px; }
.pace-inputs { display: inline-flex; align-items: center; gap: 6px; width: calc(100% - 60px); }
.pace-sep { font-weight: 700; color: #606266; font-size: 18px; }
.input-unit { color: #8c8c8c; font-size: 13px; margin-left: 6px; }
.form-actions { display: flex; justify-content: flex-end; padding-top: 10px; }

@media (max-width: 768px) {
  .filter-bar { flex-direction: column; align-items: stretch; }
  .filter-item { flex-direction: column; align-items: stretch; }
  .filter-select, .filter-range { width: 100%; }
}
</style>
