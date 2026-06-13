<template>
  <div class="dashboard-container">
    <div class="page-header">
      <div>
        <h2 class="page-title">训练概览</h2>
        <p class="page-subtitle">欢迎回来，{{ userStore.userInfo?.name || userStore.username }}！今天也要加油训练！</p>
      </div>
      <div class="header-date">
        <el-icon :size="18"><Calendar /></el-icon>
        <span>{{ currentDate }}</span>
      </div>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="12" :md="6">
        <el-card class="stat-card stat-card-blue" shadow="hover">
          <div class="stat-icon-wrap">
            <el-icon :size="28" class="stat-icon"><UserFilled /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.todayTrainees }}</div>
            <div class="stat-label">今日训练人数</div>
          </div>
          <div class="stat-trend up">
            <el-icon><Top /></el-icon>
            <span>+12%</span>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card class="stat-card stat-card-green" shadow="hover">
          <div class="stat-icon-wrap">
            <el-icon :size="28" class="stat-icon"><Location /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalDistance.toFixed(1) }}<span class="unit">km</span></div>
            <div class="stat-label">累计训练距离</div>
          </div>
          <div class="stat-trend up">
            <el-icon><Top /></el-icon>
            <span>+8.5%</span>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card class="stat-card stat-card-orange" shadow="hover">
          <div class="stat-icon-wrap">
            <el-icon :size="28" class="stat-icon"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.monthlyReports }}</div>
            <div class="stat-label">本月报告数</div>
          </div>
          <div class="stat-trend up">
            <el-icon><Top /></el-icon>
            <span>+5</span>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card class="stat-card stat-card-purple" shadow="hover">
          <div class="stat-icon-wrap">
            <el-icon :size="28" class="stat-icon"><Cpu /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.avgHeartRate }}<span class="unit">bpm</span></div>
            <div class="stat-label">平均心率</div>
          </div>
          <div class="stat-trend down">
            <el-icon><Bottom /></el-icon>
            <span>-3%</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="charts-row">
      <el-col :lg="16" :md="24">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon class="title-icon"><TrendCharts /></el-icon>
                最近7天组内总训练距离
              </span>
              <el-radio-group v-model="distanceRange" size="small">
                <el-radio-button value="7">7天</el-radio-button>
                <el-radio-button value="14">14天</el-radio-button>
                <el-radio-button value="30">30天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="distanceChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :lg="8" :md="24">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon class="title-icon"><PieChart /></el-icon>
                组内各泳姿占比
              </span>
            </div>
          </template>
          <div ref="strokeChartRef" class="chart-container chart-sm"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="session-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon class="title-icon"><List /></el-icon>
            最近训练记录
          </span>
          <el-button type="primary" link @click="$router.push('/coach/training-data')">
            查看全部 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>
      <el-table :data="recentSessions" stripe style="width: 100%" class="session-table">
        <el-table-column prop="athleteName" label="运动员" min-width="120">
          <template #default="{ row }">
            <div class="athlete-cell">
              <el-avatar :size="32" class="mini-avatar">
                {{ row.athleteName.charAt(0) }}
              </el-avatar>
              <span>{{ row.athleteName }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="distance" label="距离(米)" width="120" align="center">
          <template #default="{ row }">
            <span class="highlight-num">{{ row.distance }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="pace" label="配速(/100m)" width="140" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="getPaceTagType(row.pace)">
              {{ row.pace }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="stroke" label="泳姿" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStrokeTagType(row.stroke)" effect="plain" size="small">
              {{ row.stroke }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="avgHeartRate" label="平均心率" width="110" align="center">
          <template #default="{ row }">
            <span class="heart-rate">{{ row.avgHeartRate }} bpm</span>
          </template>
        </el-table-column>
        <el-table-column prop="time" label="训练时间" min-width="160">
          <template #default="{ row }">
            <div class="time-cell">
              <el-icon><Clock /></el-icon>
              <span>{{ row.time }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewSession(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import {
  Calendar, UserFilled, Location, Document, Cpu, Top, Bottom,
  TrendCharts, PieChart, List, ArrowRight, Clock
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'

const router = useRouter()
const userStore = useUserStore()

const currentDate = dayjs().format('YYYY年MM月DD日 dddd')
const distanceRange = ref('7')

const stats = reactive({
  todayTrainees: 0,
  totalDistance: 0,
  monthlyReports: 0,
  avgHeartRate: 0
})

const distanceChartRef = ref(null)
const strokeChartRef = ref(null)
let distanceChart = null
let strokeChart = null

const mockSessions = [
  { id: 1, athleteName: '张伟', distance: 3200, pace: '1:28', stroke: '自由泳', avgHeartRate: 145, time: '2024-06-12 08:30' },
  { id: 2, athleteName: '李娜', distance: 2800, pace: '1:35', stroke: '蛙泳', avgHeartRate: 138, time: '2024-06-12 09:15' },
  { id: 3, athleteName: '王强', distance: 3500, pace: '1:22', stroke: '蝶泳', avgHeartRate: 152, time: '2024-06-12 10:00' },
  { id: 4, athleteName: '赵敏', distance: 2600, pace: '1:40', stroke: '仰泳', avgHeartRate: 132, time: '2024-06-11 17:30' },
  { id: 5, athleteName: '陈磊', distance: 3000, pace: '1:30', stroke: '自由泳', avgHeartRate: 142, time: '2024-06-11 16:45' },
  { id: 6, athleteName: '刘洋', distance: 2400, pace: '1:42', stroke: '蛙泳', avgHeartRate: 135, time: '2024-06-11 15:20' }
]

const recentSessions = ref(mockSessions)

const fetchDashboardData = async () => {
  try {
    const res = await request({
      method: 'GET',
      url: '/api/coach/dashboard'
    })
    if (res.data) {
      Object.assign(stats, res.data.stats || {})
      recentSessions.value = res.data.sessions || mockSessions
    } else {
      setMockStats()
    }
  } catch {
    setMockStats()
  }
}

const setMockStats = () => {
  stats.todayTrainees = 18
  stats.totalDistance = 426.8
  stats.monthlyReports = 45
  stats.avgHeartRate = 142
}

const initDistanceChart = () => {
  if (!distanceChartRef.value) return
  distanceChart = echarts.init(distanceChartRef.value)

  const days = parseInt(distanceRange.value)
  const dates = []
  const data = []
  for (let i = days - 1; i >= 0; i--) {
    dates.push(dayjs().subtract(i, 'day').format('MM-DD'))
    data.push(Math.round(2000 + Math.random() * 4000))
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 30, 80, 0.95)',
      borderColor: '#0052d9',
      textStyle: { color: '#fff' },
      formatter: (params) => {
        const p = params[0]
        return `${p.axisValue}<br/>训练距离: <b>${p.value}</b> 米`
      }
    },
    grid: { left: 50, right: 30, top: 40, bottom: 40 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#e0e6ed' } },
      axisLabel: { color: '#606266' }
    },
    yAxis: {
      type: 'value',
      name: '米',
      nameTextStyle: { color: '#909399' },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#606266' },
      splitLine: { lineStyle: { color: '#f0f2f5' } }
    },
    series: [
      {
        name: '训练距离',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        data,
        lineStyle: { width: 3, color: '#0052d9' },
        itemStyle: { color: '#0052d9', borderColor: '#fff', borderWidth: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 82, 217, 0.4)' },
            { offset: 1, color: 'rgba(0, 82, 217, 0.02)' }
          ])
        }
      }
    ]
  }

  distanceChart.setOption(option)
}

const initStrokeChart = () => {
  if (!strokeChartRef.value) return
  strokeChart = echarts.init(strokeChartRef.value)

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0, 30, 80, 0.95)',
      borderColor: '#0052d9',
      textStyle: { color: '#fff' },
      formatter: '{b}: {c}米 ({d}%)'
    },
    legend: {
      orient: 'horizontal',
      bottom: 0,
      textStyle: { color: '#606266' }
    },
    series: [
      {
        name: '泳姿占比',
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '42%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{d}%',
          fontSize: 12,
          fontWeight: 600
        },
        labelLine: { length: 10, length2: 10 },
        data: [
          { value: 42000, name: '自由泳', itemStyle: { color: '#0052d9' } },
          { value: 28000, name: '蛙泳', itemStyle: { color: '#13c2c2' } },
          { value: 18000, name: '仰泳', itemStyle: { color: '#faad14' } },
          { value: 12000, name: '蝶泳', itemStyle: { color: '#f5222d' } },
          { value: 8000, name: '混合泳', itemStyle: { color: '#722ed1' } }
        ]
      }
    ]
  }

  strokeChart.setOption(option)
}

const getPaceTagType = (pace) => {
  const minSec = pace.split(':')
  const secs = parseInt(minSec[0]) * 60 + parseInt(minSec[1])
  if (secs <= 90) return 'success'
  if (secs <= 105) return 'warning'
  return 'danger'
}

const getStrokeTagType = (stroke) => {
  const map = { '自由泳': 'primary', '蛙泳': 'success', '仰泳': 'warning', '蝶泳': 'danger', '混合泳': 'info' }
  return map[stroke] || ''
}

const viewSession = (row) => {
  router.push({ path: '/coach/training-data', query: { sessionId: row.id } })
}

watch(distanceRange, () => {
  nextTick(() => initDistanceChart())
})

const handleResize = () => {
  distanceChart?.resize()
  strokeChart?.resize()
}

onMounted(async () => {
  await fetchDashboardData()
  await nextTick()
  initDistanceChart()
  initStrokeChart()
  window.addEventListener('resize', handleResize)
})
</script>

<style scoped>
.dashboard-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.page-title {
  margin: 0 0 6px 0;
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
}

.page-subtitle {
  margin: 0;
  color: #8c8c8c;
  font-size: 14px;
}

.header-date {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #e6f1ff;
  color: #0052d9;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.stats-row {
  margin-bottom: 0;
}

.stat-card {
  border: none;
  border-radius: 14px;
  overflow: hidden;
  position: relative;
}

.stat-card :deep(.el-card__body) {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
}

.stat-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-card-blue .stat-icon-wrap {
  background: linear-gradient(135deg, #e6f1ff 0%, #bfdbfe 100%);
  color: #0052d9;
}

.stat-card-green .stat-icon-wrap {
  background: linear-gradient(135deg, #d4f7e0 0%, #a6f0c1 100%);
  color: #10b981;
}

.stat-card-orange .stat-icon-wrap {
  background: linear-gradient(135deg, #fff1e0 0%, #ffd6a8 100%);
  color: #f59e0b;
}

.stat-card-purple .stat-icon-wrap {
  background: linear-gradient(135deg, #f0e7ff 0%, #d8c4ff 100%);
  color: #8b5cf6;
}

.stat-info {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  line-height: 1.2;
  margin-bottom: 4px;
}

.stat-value .unit {
  font-size: 14px;
  font-weight: 500;
  color: #8c8c8c;
  margin-left: 4px;
}

.stat-label {
  font-size: 13px;
  color: #8c8c8c;
}

.stat-trend {
  position: absolute;
  top: 16px;
  right: 16px;
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
}

.stat-trend.up {
  background: #d4f7e0;
  color: #10b981;
}

.stat-trend.down {
  background: #fee2e2;
  color: #ef4444;
}

.charts-row {
  margin-bottom: 0;
}

.chart-card,
.session-card {
  border: none;
  border-radius: 14px;
}

.chart-card :deep(.el-card__header),
.session-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f2f5;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  color: #0052d9;
}

.chart-container {
  width: 100%;
  height: 320px;
}

.chart-sm {
  height: 280px;
}

.athlete-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mini-avatar {
  background: linear-gradient(135deg, #0052d9, #003d9e);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
}

.highlight-num {
  font-weight: 600;
  color: #0052d9;
}

.heart-rate {
  color: #ef4444;
  font-weight: 500;
}

.time-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #606266;
  font-size: 13px;
}

.session-table :deep(.el-table__cell) {
  padding: 14px 0;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
