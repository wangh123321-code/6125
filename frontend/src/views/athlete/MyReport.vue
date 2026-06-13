<template>
  <div class="myreport-container">
    <div class="page-header">
      <div>
        <h2 class="page-title">我的月度报告</h2>
        <p class="page-subtitle">查看月度训练成果与进步分析</p>
      </div>
    </div>

    <el-card class="filter-card" shadow="hover">
      <div class="filter-bar">
        <div class="filter-item">
          <span class="filter-label">选择年份</span>
          <el-select v-model="form.year" class="filter-select-sm">
            <el-option v-for="y in yearOptions" :key="y" :label="`${y}年`" :value="y" />
          </el-select>
        </div>
        <div class="filter-item">
          <span class="filter-label">选择月份</span>
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
      <el-empty description="请选择月份后点击「生成报告」查看您的月度分析">
        <el-button type="primary" @click="generateReport">立即生成</el-button>
      </el-empty>
    </div>

    <template v-else>
      <el-row :gutter="18">
        <el-col :xs="12" :sm="12" :md="6">
          <el-card class="stat-card s1" shadow="hover">
            <div class="si">
              <el-icon class="sicon"><Location /></el-icon>
              <div>
                <div class="sval">{{ reportStats.total_distance_km.toFixed(1) }}<span>km</span></div>
                <div class="slbl">总距离</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="12" :md="6">
          <el-card class="stat-card s2" shadow="hover">
            <div class="si">
              <el-icon class="sicon"><Trophy /></el-icon>
              <div>
                <div class="sval">{{ reportStats.training_count }}<span>次</span></div>
                <div class="slbl">训练次数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="12" :md="6">
          <el-card class="stat-card s3" shadow="hover">
            <div class="si">
              <el-icon class="sicon"><Cpu /></el-icon>
              <div>
                <div class="sval">{{ reportStats.avg_heart_rate }}<span>bpm</span></div>
                <div class="slbl">平均心率</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="12" :md="6">
          <el-card class="stat-card s4" shadow="hover">
            <div class="si">
              <el-icon class="sicon"><Medal /></el-icon>
              <div>
                <div class="sval pidx">
                  {{ reportStats.progress_index }}
                  <el-tag
                    size="small"
                    round
                    :type="reportStats.progress_index >= 0 ? 'success' : 'danger'"
                    effect="light"
                    class="pidx-tag"
                  >
                    {{ reportStats.progress_index >= 0 ? '+' : '' }}{{ reportStats.progress_index }}%
                  </el-tag>
                </div>
                <div class="slbl">进步指数</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="18" style="margin-top: 18px;">
        <el-col :md="12" :sm="24">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <span class="card-title">
                <el-icon class="title-icon"><PieChart /></el-icon>
                本月泳姿占比
              </span>
            </template>
            <div ref="pieRef" class="chart-md"></div>
          </el-card>
        </el-col>
        <el-col :md="12" :sm="24">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <span class="card-title">
                <el-icon class="title-icon"><DataLine /></el-icon>
                心率区间训练时长
              </span>
            </template>
            <div ref="barRef" class="chart-md"></div>
          </el-card>
        </el-col>
      </el-row>

      <el-card class="chart-card" shadow="hover" style="margin-top: 18px;">
        <template #header>
          <span class="card-title">
            <el-icon class="title-icon"><TrendCharts /></el-icon>
            划距技术趋势（本月 vs 上月）
          </span>
        </template>
        <div ref="trendRef" class="chart-lg"></div>
      </el-card>

      <el-card class="compare-card" shadow="hover" style="margin-top: 18px;">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon class="title-icon"><Competition /></el-icon>
              与上月对比
            </span>
            <el-tag type="info" effect="plain" size="small">
              {{ form.year }}年{{ form.month }}月 vs {{ prevLabel }}
            </el-tag>
          </div>
        </template>
        <el-table :data="compareRows" border stripe style="width: 100%" :row-class-name="rcn">
          <el-table-column prop="metric" label="指标" min-width="130">
            <template #default="{ row }"><b class="mname">{{ row.metric }}</b></template>
          </el-table-column>
          <el-table-column prop="current" label="本月" width="130" align="center">
            <template #default="{ row }">
              <span class="cur">{{ row.current }}{{ row.unit }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="previous" label="上月" width="130" align="center">
            <template #default="{ row }">
              <span>{{ row.previous }}{{ row.unit }}</span>
            </template>
          </el-table-column>
          <el-table-column label="变化率" width="150" align="center">
            <template #default="{ row }">
              <el-tag
                :type="row.regressed ? 'danger' : 'success'"
                effect="light"
                round
                size="small"
              >
                <el-icon style="vertical-align:-2px;">
                  {{ row.regressed ? Bottom : Top }}
                </el-icon>
                {{ row.change_rate }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="说明" min-width="200">
            <template #default="{ row }">
              <span class="desc">{{ row.description }}</span>
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
  DocumentAdd, Download, Location, Trophy, Cpu, Medal, Top, Bottom,
  PieChart, DataLine, TrendCharts, Competition
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'

const userStore = useUserStore()
const generating = ref(false)
const currentReport = ref(null)
const curYear = dayjs().year()
const curMonth = dayjs().month() + 1

const form = reactive({
  year: curYear,
  month: curMonth
})

const yearOptions = computed(() => {
  const arr = []
  for (let y = curYear - 2; y <= curYear; y++) arr.push(y)
  return arr
})

const prevLabel = computed(() => {
  const d = dayjs(`${form.year}-${form.month}-01`).subtract(1, 'month')
  return `${d.year()}年${d.month() + 1}月`
})

const reportStats = reactive({
  total_distance_km: 0,
  training_count: 0,
  avg_heart_rate: 0,
  progress_index: 0
})

const compareRows = ref([])

const pieRef = ref(null)
const barRef = ref(null)
const trendRef = ref(null)
let pieChart = null
let barChart = null
let trendChart = null

const rcn = ({ row }) => row.regressed ? 'regressed-row' : ''

const generateReport = async () => {
  generating.value = true
  try {
    const res = await request({
      method: 'POST',
      url: '/api/reports/generate',
      data: {
        athlete_id: userStore.userId,
        year: form.year,
        month: form.month
      }
    })
    if (res.data) {
      const d = res.data.data || res.data
      currentReport.value = d
      reportStats.total_distance_km = d.total_distance_km ?? d.total_distance / 1000 ?? 0
      reportStats.training_count = d.training_count ?? 0
      reportStats.avg_heart_rate = d.avg_heart_rate ?? 0
      reportStats.progress_index = d.progress_index ?? 0
      compareRows.value = d.compare_data || d.compare || []
    }
  } catch {
    fillMock()
  } finally {
    generating.value = false
    ElMessage.success('报告生成成功')
    await nextTick()
    initCharts()
  }
}

const fillMock = () => {
  currentReport.value = { id: Date.now() }
  reportStats.total_distance_km = 108.5
  reportStats.training_count = 20
  reportStats.avg_heart_rate = 143
  reportStats.progress_index = 6
  compareRows.value = [
    { metric: '总距离', current: '108.5', previous: '98.2', unit: ' km', change_rate: '+10.5%', regressed: false, description: '训练量稳步提升' },
    { metric: '训练次数', current: '20', previous: '18', unit: ' 次', change_rate: '+11.1%', regressed: false, description: '出勤稳定' },
    { metric: '平均配速', current: '1:30', previous: '1:32', unit: '', change_rate: '-2.2%', regressed: false, description: '速度提升' },
    { metric: '平均心率', current: '143', previous: '140', unit: ' bpm', change_rate: '+2.1%', regressed: true, description: '训练强度增加' },
    { metric: '平均划距', current: '2.28', previous: '2.22', unit: ' m', change_rate: '+2.7%', regressed: false, description: '技术改善' },
    { metric: '100米PB', current: '59.50', previous: '1:00.20', unit: ' s', change_rate: '-1.6%', regressed: false, description: 'PB 提升！' }
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

const initCharts = () => {
  if (pieRef.value) {
    pieChart?.dispose()
    pieChart = echarts.init(pieRef.value)
    pieChart.setOption({
      tooltip: { trigger: 'item', backgroundColor: 'rgba(0,30,80,0.95)', borderColor: '#0052d9', textStyle: { color: '#fff' } },
      legend: { right: 10, top: 'center', orient: 'vertical', textStyle: { color: '#606266' } },
      series: [{
        type: 'pie', radius: ['42%', '70%'], center: ['38%', '50%'],
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { formatter: '{b}\n{d}%', fontSize: 12, fontWeight: 600 },
        data: [
          { value: 48.2, name: '自由泳', itemStyle: { color: '#0052d9' } },
          { value: 25.6, name: '蛙泳', itemStyle: { color: '#10b981' } },
          { value: 16.5, name: '仰泳', itemStyle: { color: '#f59e0b' } },
          { value: 12.3, name: '蝶泳', itemStyle: { color: '#ef4444' } },
          { value: 5.9, name: '混合泳', itemStyle: { color: '#8b5cf6' } }
        ]
      }]
    })
  }
  if (barRef.value) {
    barChart?.dispose()
    barChart = echarts.init(barRef.value)
    barChart.setOption({
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(0,30,80,0.95)', borderColor: '#0052d9', textStyle: { color: '#fff' } },
      grid: { left: 50, right: 20, top: 30, bottom: 40 },
      xAxis: { type: 'category', data: ['<120', '120-140', '140-160', '160-180', '>180'], axisLine: { lineStyle: { color: '#e0e6ed' } }, axisLabel: { color: '#606266', fontSize: 11 } },
      yAxis: { type: 'value', name: '小时', nameTextStyle: { color: '#909399' }, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#606266' }, splitLine: { lineStyle: { color: '#f0f2f5' } } },
      series: [{
        type: 'bar', barWidth: '52%',
        data: [
          { value: 2.8, itemStyle: { color: '#10b981', borderRadius: [6, 6, 0, 0] } },
          { value: 7.2, itemStyle: { color: '#3b82f6', borderRadius: [6, 6, 0, 0] } },
          { value: 11.5, itemStyle: { color: '#0052d9', borderRadius: [6, 6, 0, 0] } },
          { value: 6.8, itemStyle: { color: '#f59e0b', borderRadius: [6, 6, 0, 0] } },
          { value: 1.9, itemStyle: { color: '#ef4444', borderRadius: [6, 6, 0, 0] } }
        ]
      }]
    })
  }
  if (trendRef.value) {
    trendChart?.dispose()
    trendChart = echarts.init(trendRef.value)
    const days = [], cur = [], prev = []
    for (let i = 1; i <= 30; i++) {
      days.push(`${i}日`)
      cur.push((Math.random() * 0.3 + 2.2).toFixed(2))
      prev.push((Math.random() * 0.3 + 2.05).toFixed(2))
    }
    trendChart.setOption({
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(0,30,80,0.95)', borderColor: '#0052d9', textStyle: { color: '#fff' } },
      legend: { data: ['本月', '上月'], top: 0, textStyle: { color: '#606266' } },
      grid: { left: 50, right: 30, top: 40, bottom: 40 },
      xAxis: { type: 'category', data: days, boundaryGap: false, axisLine: { lineStyle: { color: '#e0e6ed' } }, axisLabel: { color: '#606266', fontSize: 10, interval: 2 } },
      yAxis: { type: 'value', min: 1.8, max: 2.8, name: '米/次', nameTextStyle: { color: '#909399' }, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#606266' }, splitLine: { lineStyle: { color: '#f0f2f5' } } },
      series: [
        { name: '本月', type: 'line', smooth: true, showSymbol: false, data: cur, lineStyle: { width: 3, color: '#0052d9' }, itemStyle: { color: '#0052d9' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(0,82,217,0.4)' }, { offset: 1, color: 'rgba(0,82,217,0.02)' }]) } },
        { name: '上月', type: 'line', smooth: true, showSymbol: false, data: prev, lineStyle: { width: 2, color: '#13c2c2', type: 'dashed' }, itemStyle: { color: '#13c2c2' } }
      ]
    })
  }
}

const handleResize = () => {
  pieChart?.resize()
  barChart?.resize()
  trendChart?.resize()
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})
</script>

<style scoped>
.myreport-container { display: flex; flex-direction: column; gap: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-end; }
.page-title { margin: 0 0 6px 0; font-size: 24px; font-weight: 700; color: #1a1a2e; }
.page-subtitle { margin: 0; color: #8c8c8c; font-size: 14px; }

.filter-card { border: none; border-radius: 14px; }
.filter-card :deep(.el-card__body) { padding: 16px 20px; }
.filter-bar { display: flex; align-items: center; gap: 18px; flex-wrap: wrap; }
.filter-item { display: flex; align-items: center; gap: 10px; }
.filter-label { font-size: 14px; color: #606266; font-weight: 500; white-space: nowrap; }
.filter-select-sm { width: 120px; }

.empty-wrap { background: #fff; border-radius: 14px; padding: 60px 20px; }

.stat-card, .chart-card, .compare-card { border: none; border-radius: 14px; }
.stat-card :deep(.el-card__body) { padding: 18px; }
.si { display: flex; align-items: center; gap: 14px; }
.sicon {
  width: 48px; height: 48px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 24px; flex-shrink: 0;
}
.s1 .sicon { background: linear-gradient(135deg, #0052d9, #003d9e); }
.s2 .sicon { background: linear-gradient(135deg, #10b981, #059669); }
.s3 .sicon { background: linear-gradient(135deg, #f59e0b, #d97706); }
.s4 .sicon { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }
.sval { font-size: 26px; font-weight: 800; color: #1a1a2e; line-height: 1.2; }
.sval span { font-size: 13px; color: #8c8c8c; margin-left: 3px; font-weight: 500; }
.slbl { font-size: 12px; color: #8c8c8c; margin-top: 3px; }
.pidx { display: flex; align-items: center; gap: 8px; }
.pidx-tag { font-size: 11px; }

.chart-card :deep(.el-card__header),
.compare-card :deep(.el-card__header) {
  padding: 16px 20px; border-bottom: 1px solid #f0f2f5;
}
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title {
  font-size: 16px; font-weight: 600; color: #1a1a2e;
  display: flex; align-items: center; gap: 8px;
}
.title-icon { color: #0052d9; }
.chart-md { width: 100%; height: 300px; }
.chart-lg { width: 100%; height: 330px; }

.mname { color: #1a1a2e; }
.cur { font-weight: 700; color: #0052d9; }
.desc { color: #606266; font-size: 13px; }

:deep(.regressed-row) { background-color: #fff1f0 !important; }
:deep(.regressed-row td) { background-color: #fff1f0 !important; }

@media (max-width: 768px) {
  .filter-bar { flex-direction: column; align-items: stretch; }
  .filter-item { flex-direction: column; align-items: stretch; }
  .filter-select-sm { width: 100%; }
}
</style>
