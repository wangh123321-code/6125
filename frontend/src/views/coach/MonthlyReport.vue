<template>
  <div class="report-container">
    <div class="page-header">
      <div>
        <h2 class="page-title">月度报告</h2>
        <p class="page-subtitle">自动生成运动员的月度训练分析与进步评估报告</p>
      </div>
    </div>

    <el-card class="filter-card" shadow="hover">
      <div class="filter-bar">
        <div class="filter-item">
          <span class="filter-label">选择运动员</span>
          <el-select
            v-model="form.athlete_id"
            placeholder="请选择运动员"
            filterable
            class="filter-select-lg"
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
          <span class="filter-label">年</span>
          <el-select v-model="form.year" class="filter-select-sm">
            <el-option v-for="y in yearOptions" :key="y" :label="`${y}年`" :value="y" />
          </el-select>
        </div>
        <div class="filter-item">
          <span class="filter-label">月</span>
          <el-select v-model="form.month" class="filter-select-sm">
            <el-option v-for="m in 12" :key="m" :label="`${m}月`" :value="m" />
          </el-select>
        </div>
        <el-button
          type="primary"
          :icon="DocumentAdd"
          @click="generateReport"
          :loading="generating"
        >
          生成报告
        </el-button>
        <el-button
          type="success"
          :icon="Download"
          @click="downloadReport"
          :disabled="!currentReport?.id"
        >
          下载 PDF
        </el-button>
      </div>
    </el-card>

    <div v-if="!currentReport" class="empty-wrap">
      <el-empty description="请选择运动员和月份后点击「生成报告」">
        <el-button type="primary" @click="generateReport" :disabled="!form.athlete_id">
          立即生成
        </el-button>
      </el-empty>
    </div>

    <template v-else>
      <el-row :gutter="20">
        <el-col :xs="12" :sm="12" :md="6">
          <el-card class="stat-card s-blue" shadow="hover">
            <div class="sc-head">
              <el-icon class="sc-icon"><Location /></el-icon>
            </div>
            <div class="sc-value">{{ reportStats.total_distance_km.toFixed(1) }}<span>km</span></div>
            <div class="sc-label">总距离</div>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="12" :md="6">
          <el-card class="stat-card s-green" shadow="hover">
            <div class="sc-head">
              <el-icon class="sc-icon"><List /></el-icon>
            </div>
            <div class="sc-value">{{ reportStats.training_count }}<span>次</span></div>
            <div class="sc-label">训练次数</div>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="12" :md="6">
          <el-card class="stat-card s-orange" shadow="hover">
            <div class="sc-head">
              <el-icon class="sc-icon"><Cpu /></el-icon>
            </div>
            <div class="sc-value">{{ reportStats.avg_heart_rate }}<span>bpm</span></div>
            <div class="sc-label">平均心率</div>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="12" :md="6">
          <el-card class="stat-card s-purple" shadow="hover">
            <div class="sc-head">
              <el-icon class="sc-icon"><Trophy /></el-icon>
            </div>
            <div class="sc-value">
              {{ reportStats.progress_index }}
              <span class="trend" :class="reportStats.progress_index >= 0 ? 'up' : 'down'">
                <el-icon>{{ reportStats.progress_index >= 0 ? Top : Bottom }}</el-icon>
                {{ Math.abs(reportStats.progress_index) }}%
              </span>
            </div>
            <div class="sc-label">进步指数</div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :md="12" :sm="24">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-title">
                  <el-icon class="title-icon"><PieChart /></el-icon>
                  泳姿占比
                </span>
              </div>
            </template>
            <div ref="pieChartRef" class="chart-md"></div>
          </el-card>
        </el-col>
        <el-col :md="12" :sm="24">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-title">
                  <el-icon class="title-icon"><DataLine /></el-icon>
                  心率区间分布
                </span>
              </div>
            </template>
            <div ref="barChartRef" class="chart-md"></div>
          </el-card>
        </el-col>
      </el-row>

      <el-card class="chart-card" shadow="hover" style="margin-top: 20px;">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon class="title-icon"><TrendCharts /></el-icon>
              技术指标趋势 - 划距
            </span>
          </div>
        </template>
        <div ref="trendChartRef" class="chart-lg"></div>
      </el-card>

      <el-card class="table-card" shadow="hover" style="margin-top: 20px;">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon class="title-icon"><Competition /></el-icon>
              与上月对比
            </span>
            <el-tag type="info" effect="plain" size="small">
              {{ form.year }}年{{ form.month }}月 vs {{ prevMonthLabel }}
            </el-tag>
          </div>
        </template>
        <el-table :data="compareData" border style="width: 100%" :row-class-name="rowClass">
          <el-table-column prop="metric" label="指标" min-width="140">
            <template #default="{ row }">
              <span class="metric-name">{{ row.metric }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="current" label="本月" width="140" align="center">
            <template #default="{ row }">
              <span class="highlight">{{ row.current }}{{ row.unit }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="previous" label="上月" width="140" align="center">
            <template #default="{ row }">
              <span>{{ row.previous }}{{ row.unit }}</span>
            </template>
          </el-table-column>
          <el-table-column label="变化率" width="180" align="center">
            <template #default="{ row }">
              <el-tag
                :type="row.regressed ? 'danger' : 'success'"
                effect="light"
                size="small"
                round
              >
                <el-icon style="vertical-align: -2px;">
                  {{ row.regressed ? Bottom : Top }}
                </el-icon>
                {{ row.change_rate }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="说明" min-width="200">
            <template #default="{ row }">
              <span class="desc-text">{{ row.description }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DocumentAdd, Download, Location, List, Cpu, Trophy, Top, Bottom,
  PieChart, DataLine, TrendCharts, Competition
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import request from '@/utils/request'

const generating = ref(false)
const athleteList = ref([])
const currentReport = ref(null)

const currentYear = dayjs().year()
const currentMonth = dayjs().month() + 1

const form = reactive({
  athlete_id: null,
  year: currentYear,
  month: currentMonth
})

const yearOptions = computed(() => {
  const years = []
  for (let y = currentYear - 2; y <= currentYear; y++) years.push(y)
  return years
})

const prevMonthLabel = computed(() => {
  const d = dayjs(`${form.year}-${form.month}-01`).subtract(1, 'month')
  return `${d.year()}年${d.month() + 1}月`
})

const reportStats = reactive({
  total_distance_km: 0,
  training_count: 0,
  avg_heart_rate: 0,
  progress_index: 0
})

const compareData = ref([])

const pieChartRef = ref(null)
const barChartRef = ref(null)
const trendChartRef = ref(null)
let pieChart = null
let barChart = null
let trendChart = null

const rowClass = ({ row }) => {
  return row.regressed ? 'regressed-row' : ''
}

const fetchAthletes = async () => {
  try {
    const res = await request({ method: 'GET', url: '/api/auth/athletes' })
    if (res.data) {
      athleteList.value = res.data.data || res.data || []
      if (athleteList.value.length) form.athlete_id = athleteList.value[0].id
    }
  } catch {
    athleteList.value = [
      { id: 1, name: '张伟', group: '一组' },
      { id: 2, name: '李娜', group: '一组' },
      { id: 3, name: '王强', group: '二组' }
    ]
    form.athlete_id = 1
  }
}

const generateReport = async () => {
  if (!form.athlete_id) {
    ElMessage.warning('请先选择运动员')
    return
  }
  generating.value = true
  try {
    const res = await request({
      method: 'POST',
      url: '/api/reports/generate',
      data: {
        athlete_id: form.athlete_id,
        year: form.year,
        month: form.month
      }
    })
    if (res.data) {
      const data = res.data.data || res.data
      currentReport.value = data
      fillReportData(data)
      ElMessage.success('报告生成成功')
      await nextTick()
      initAllCharts()
    }
  } catch {
    fillMockReport()
    ElMessage.success('报告生成成功 (模拟)')
    await nextTick()
    initAllCharts()
  } finally {
    generating.value = false
  }
}

const fillReportData = (data) => {
  reportStats.total_distance_km = data.total_distance_km ?? data.total_distance / 1000 ?? 0
  reportStats.training_count = data.training_count ?? 0
  reportStats.avg_heart_rate = data.avg_heart_rate ?? 0
  reportStats.progress_index = data.progress_index ?? 0
  compareData.value = data.compare_data || data.compare || []
}

const fillMockReport = () => {
  currentReport.value = { id: Date.now() }
  reportStats.total_distance_km = 128.5
  reportStats.training_count = 22
  reportStats.avg_heart_rate = 145
  reportStats.progress_index = 8
  compareData.value = [
    { metric: '总距离', current: '128.5', previous: '112.3', unit: ' km', change_rate: '+14.4%', regressed: false, description: '训练量稳步提升' },
    { metric: '训练次数', current: '22', previous: '20', unit: ' 次', change_rate: '+10.0%', regressed: false, description: '出勤率良好' },
    { metric: '平均配速', current: '1:28', previous: '1:30', unit: '', change_rate: '-2.2%', regressed: false, description: '配速提升明显' },
    { metric: '平均心率', current: '145', previous: '142', unit: ' bpm', change_rate: '+2.1%', regressed: true, description: '强度略有上升' },
    { metric: '平均划距', current: '2.35', previous: '2.28', unit: ' m', change_rate: '+3.1%', regressed: false, description: '划水效率提升' },
    { metric: '最大摄氧量', current: '58.2', previous: '56.8', unit: '', change_rate: '+2.5%', regressed: false, description: '有氧能力增强' },
    { metric: '100米最好成绩', current: '58.32', previous: '59.10', unit: ' s', change_rate: '-1.3%', regressed: false, description: '短距离速度提升' },
    { metric: '训练时长', current: '34.5', previous: '38.2', unit: ' h', change_rate: '-9.7%', regressed: true, description: '效率提升，时长减少' }
  ]
}

const downloadReport = () => {
  if (!currentReport.value?.id) {
    ElMessage.warning('请先生成报告')
    return
  }
  const url = `/api/reports/${currentReport.value.id}/download`
  const a = document.createElement('a')
  a.href = url
  a.target = '_blank'
  a.download = `月度报告_${form.year}${form.month}.pdf`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  ElMessage.info('开始下载...')
}

const initAllCharts = () => {
  initPieChart()
  initBarChart()
  initTrendChart()
}

const initPieChart = () => {
  if (!pieChartRef.value) return
  pieChart?.dispose()
  pieChart = echarts.init(pieChartRef.value)
  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0, 30, 80, 0.95)',
      borderColor: '#0052d9',
      textStyle: { color: '#fff' },
      formatter: '{b}: {c}km ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: '#606266' }
    },
    series: [{
      name: '泳姿占比',
      type: 'pie',
      radius: ['45%', '72%'],
      center: ['38%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 6,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        formatter: '{b}\n{d}%',
        fontSize: 12,
        fontWeight: 600
      },
      data: [
        { value: 52.6, name: '自由泳', itemStyle: { color: '#0052d9' } },
        { value: 30.2, name: '蛙泳', itemStyle: { color: '#10b981' } },
        { value: 18.5, name: '仰泳', itemStyle: { color: '#f59e0b' } },
        { value: 15.8, name: '蝶泳', itemStyle: { color: '#ef4444' } },
        { value: 11.4, name: '混合泳', itemStyle: { color: '#8b5cf6' } }
      ]
    }]
  }
  pieChart.setOption(option)
}

const initBarChart = () => {
  if (!barChartRef.value) return
  barChart?.dispose()
  barChart = echarts.init(barChartRef.value)
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 30, 80, 0.95)',
      borderColor: '#0052d9',
      textStyle: { color: '#fff' },
      formatter: (p) => `${p[0].name}<br/>训练时间: <b>${p[0].value}</b> 小时`
    },
    grid: { left: 50, right: 30, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      data: ['<120bpm', '120-140bpm', '140-160bpm', '160-180bpm', '>180bpm'],
      axisLine: { lineStyle: { color: '#e0e6ed' } },
      axisLabel: { color: '#606266', fontSize: 11, interval: 0, rotate: 0 }
    },
    yAxis: {
      type: 'value',
      name: '小时',
      nameTextStyle: { color: '#909399' },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#606266' },
      splitLine: { lineStyle: { color: '#f0f2f5' } }
    },
    series: [{
      type: 'bar',
      barWidth: '50%',
      data: [
        { value: 3.2, itemStyle: { color: '#10b981', borderRadius: [6, 6, 0, 0] } },
        { value: 8.6, itemStyle: { color: '#3b82f6', borderRadius: [6, 6, 0, 0] } },
        { value: 12.4, itemStyle: { color: '#0052d9', borderRadius: [6, 6, 0, 0] } },
        { value: 7.8, itemStyle: { color: '#f59e0b', borderRadius: [6, 6, 0, 0] } },
        { value: 2.5, itemStyle: { color: '#ef4444', borderRadius: [6, 6, 0, 0] } }
      ]
    }]
  }
  barChart.setOption(option)
}

const initTrendChart = () => {
  if (!trendChartRef.value) return
  trendChart?.dispose()
  trendChart = echarts.init(trendChartRef.value)
  const days = []
  const cur = []
  const prev = []
  for (let i = 1; i <= 30; i++) {
    days.push(`${i}日`)
    cur.push((Math.random() * 0.3 + 2.2).toFixed(2))
    prev.push((Math.random() * 0.3 + 2.05).toFixed(2))
  }
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 30, 80, 0.95)',
      borderColor: '#0052d9',
      textStyle: { color: '#fff' }
    },
    legend: {
      data: ['本月划距', '上月划距'],
      top: 0,
      textStyle: { color: '#606266' }
    },
    grid: { left: 50, right: 30, top: 45, bottom: 40 },
    xAxis: {
      type: 'category',
      data: days,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#e0e6ed' } },
      axisLabel: { color: '#606266', fontSize: 10, interval: 2 }
    },
    yAxis: {
      type: 'value',
      min: 1.8,
      max: 2.8,
      name: '米/次',
      nameTextStyle: { color: '#909399' },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#606266' },
      splitLine: { lineStyle: { color: '#f0f2f5' } }
    },
    series: [
      {
        name: '本月划距',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: cur,
        lineStyle: { width: 3, color: '#0052d9' },
        itemStyle: { color: '#0052d9' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 82, 217, 0.4)' },
            { offset: 1, color: 'rgba(0, 82, 217, 0.02)' }
          ])
        }
      },
      {
        name: '上月划距',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: prev,
        lineStyle: { width: 2, color: '#13c2c2', type: 'dashed' },
        itemStyle: { color: '#13c2c2' }
      }
    ]
  }
  trendChart.setOption(option)
}

const handleResize = () => {
  pieChart?.resize()
  barChart?.resize()
  trendChart?.resize()
}

onMounted(async () => {
  await fetchAthletes()
  window.addEventListener('resize', handleResize)
})
</script>

<style scoped>
.report-container {
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

.filter-card { border: none; border-radius: 14px; }
.filter-card :deep(.el-card__body) { padding: 16px 20px; }
.filter-bar { display: flex; align-items: center; gap: 18px; flex-wrap: wrap; }
.filter-item { display: flex; align-items: center; gap: 10px; }
.filter-label { font-size: 14px; color: #606266; font-weight: 500; white-space: nowrap; }
.filter-select-lg { width: 240px; }
.filter-select-sm { width: 110px; }

.empty-wrap {
  background: #fff;
  border-radius: 14px;
  padding: 60px 20px;
}

.stat-card, .chart-card, .table-card { border: none; border-radius: 14px; }
.stat-card :deep(.el-card__body) { padding: 20px; position: relative; }
.sc-head {
  width: 48px; height: 48px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 14px;
}
.sc-icon { font-size: 24px; color: #fff; }
.s-blue .sc-head { background: linear-gradient(135deg, #0052d9, #003d9e); }
.s-green .sc-head { background: linear-gradient(135deg, #10b981, #059669); }
.s-orange .sc-head { background: linear-gradient(135deg, #f59e0b, #d97706); }
.s-purple .sc-head { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }
.sc-value { font-size: 28px; font-weight: 700; color: #1a1a2e; line-height: 1.2; display: flex; align-items: baseline; gap: 4px; }
.sc-value > span:first-of-type { font-size: 13px; color: #8c8c8c; font-weight: 500; }
.sc-label { font-size: 13px; color: #8c8c8c; margin-top: 4px; }
.trend {
  display: inline-flex; align-items: center; gap: 2px;
  font-size: 12px; padding: 2px 8px; border-radius: 10px;
  margin-left: 8px; font-weight: 600;
}
.trend.up { background: #d4f7e0; color: #10b981; }
.trend.down { background: #fee2e2; color: #ef4444; }

.chart-card :deep(.el-card__header),
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
.chart-md { width: 100%; height: 300px; }
.chart-lg { width: 100%; height: 340px; }

.metric-name { font-weight: 600; color: #1a1a2e; }
.highlight { font-weight: 700; color: #0052d9; }
.desc-text { color: #606266; font-size: 13px; }

:deep(.regressed-row) {
  background-color: #fff1f0 !important;
}
:deep(.regressed-row td) {
  background-color: #fff1f0 !important;
}

@media (max-width: 768px) {
  .filter-bar { flex-direction: column; align-items: stretch; }
  .filter-item { flex-direction: column; align-items: stretch; }
  .filter-select-lg, .filter-select-sm { width: 100%; }
}
</style>
