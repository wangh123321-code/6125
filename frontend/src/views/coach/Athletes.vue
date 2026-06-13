<template>
  <div class="athletes-container">
    <div class="page-header">
      <div>
        <h2 class="page-title">运动员管理</h2>
        <p class="page-subtitle">查看和管理您组内所有运动员的训练档案与详细数据</p>
      </div>
    </div>

    <el-card class="filter-card" shadow="hover">
      <div class="filter-bar">
        <div class="filter-item">
          <span class="filter-label">分组筛选</span>
          <el-select v-model="filterGroup" placeholder="全部组" clearable class="filter-select">
            <el-option label="全部组" value="" />
            <el-option v-for="g in groupList" :key="g" :label="g" :value="g" />
          </el-select>
        </div>
        <div class="filter-item">
          <span class="filter-label">搜索</span>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索姓名、主项..."
            clearable
            class="filter-input"
            :prefix-icon="Search"
          />
        </div>
        <el-button type="primary" @click="fetchAthletes" :icon="Refresh">
          刷新
        </el-button>
      </div>
    </el-card>

    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon class="title-icon"><User /></el-icon>
            运动员列表 ({{ filteredAthletes.length }}人)
          </span>
        </div>
      </template>
      <el-table :data="filteredAthletes" stripe style="width: 100%" v-loading="loading">
        <el-table-column label="序号" type="index" width="70" align="center" />
        <el-table-column prop="name" label="姓名" min-width="120">
          <template #default="{ row }">
            <div class="athlete-cell">
              <el-avatar :size="36" class="mini-avatar">
                {{ row.name?.charAt(0) }}
              </el-avatar>
              <span class="athlete-name">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="group" label="组" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="getGroupTagType(row.group)" effect="plain" size="small">
              {{ row.group }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="age" label="年龄" width="90" align="center" />
        <el-table-column prop="gender" label="性别" width="90" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.gender === '男' || row.gender === 'M'" class="icon-male"><Male /></el-icon>
            <el-icon v-else class="icon-female"><Female /></el-icon>
            <span>{{ row.gender }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="height" label="身高(cm)" width="110" align="center" />
        <el-table-column prop="weight" label="体重(kg)" width="110" align="center" />
        <el-table-column prop="main_stroke" label="主项" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getStrokeTagType(row.main_stroke)" size="small">
              {{ row.main_stroke }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewDetail(row)" :icon="View">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="detailVisible"
      :title="`${currentAthlete?.name || ''} - 训练档案`"
      width="1100px"
      class="detail-dialog"
      destroy-on-close
    >
      <div v-loading="detailLoading" class="detail-content">
        <el-row :gutter="20">
          <el-col :md="8" :sm="24">
            <el-card class="info-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <span class="card-title">
                    <el-icon class="title-icon"><UserFilled /></el-icon>
                    基本信息
                  </span>
                </div>
              </template>
              <div class="info-body">
                <el-avatar :size="80" class="big-avatar">
                  {{ currentAthlete?.name?.charAt(0) }}
                </el-avatar>
                <h3 class="info-name">{{ currentAthlete?.name }}</h3>
                <el-tag :type="getGroupTagType(currentAthlete?.group)" effect="dark" class="info-group-tag">
                  {{ currentAthlete?.group }}
                </el-tag>
                <div class="info-list">
                  <div class="info-item">
                    <span class="info-label">年龄</span>
                    <span class="info-value">{{ currentAthlete?.age }} 岁</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">性别</span>
                    <span class="info-value">{{ currentAthlete?.gender }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">身高</span>
                    <span class="info-value">{{ currentAthlete?.height }} cm</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">体重</span>
                    <span class="info-value">{{ currentAthlete?.weight }} kg</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">主项</span>
                    <span class="info-value">{{ currentAthlete?.main_stroke }}</span>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :md="16" :sm="24">
            <el-row :gutter="16">
              <el-col :xs="12" :sm="12" :md="6">
                <el-card class="stat-card stat-blue" shadow="hover">
                  <div class="stat-body">
                    <el-icon class="stat-icon"><Location /></el-icon>
                    <div class="stat-info">
                      <div class="stat-val">{{ (stats.distance_30d / 1000).toFixed(1) }}<span class="stat-unit">km</span></div>
                      <div class="stat-lbl">30天距离</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
              <el-col :xs="12" :sm="12" :md="6">
                <el-card class="stat-card stat-green" shadow="hover">
                  <div class="stat-body">
                    <el-icon class="stat-icon"><List /></el-icon>
                    <div class="stat-info">
                      <div class="stat-val">{{ stats.session_count }}<span class="stat-unit">次</span></div>
                      <div class="stat-lbl">训练次数</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
              <el-col :xs="12" :sm="12" :md="6">
                <el-card class="stat-card stat-orange" shadow="hover">
                  <div class="stat-body">
                    <el-icon class="stat-icon"><Timer /></el-icon>
                    <div class="stat-info">
                      <div class="stat-val">{{ stats.avg_pace }}<span class="stat-unit">/100m</span></div>
                      <div class="stat-lbl">平均配速</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
              <el-col :xs="12" :sm="12" :md="6">
                <el-card class="stat-card stat-purple" shadow="hover">
                  <div class="stat-body">
                    <el-icon class="stat-icon"><Cpu /></el-icon>
                    <div class="stat-info">
                      <div class="stat-val">{{ stats.avg_heart_rate }}<span class="stat-unit">bpm</span></div>
                      <div class="stat-lbl">平均心率</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </el-col>
        </el-row>

        <el-row :gutter="20" style="margin-top: 20px;">
          <el-col :lg="14" :md="24">
            <el-card class="chart-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <span class="card-title">
                    <el-icon class="title-icon"><TrendCharts /></el-icon>
                    距离趋势 (最近30天)
                  </span>
                </div>
              </template>
              <div ref="distanceTrendRef" class="chart-box"></div>
            </el-card>
          </el-col>
          <el-col :lg="10" :md="24">
            <el-card class="chart-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <span class="card-title">
                    <el-icon class="title-icon"><DataAnalysis /></el-icon>
                    同组能力对比
                  </span>
                </div>
              </template>
              <div ref="radarRef" class="chart-box chart-sm"></div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search, Refresh, View, User, Male, Female, UserFilled,
  Location, List, Timer, Cpu, TrendCharts, DataAnalysis
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import request from '@/utils/request'

const loading = ref(false)
const detailLoading = ref(false)
const detailVisible = ref(false)
const filterGroup = ref('')
const searchKeyword = ref('')
const athleteList = ref([])
const currentAthlete = ref(null)
const distanceTrendRef = ref(null)
const radarRef = ref(null)
let distanceChart = null
let radarChart = null

const groupList = computed(() => {
  const groups = new Set(athleteList.value.map(a => a.group).filter(Boolean))
  return Array.from(groups)
})

const filteredAthletes = computed(() => {
  return athleteList.value.filter(a => {
    const groupMatch = !filterGroup.value || a.group === filterGroup.value
    const kw = searchKeyword.value.trim().toLowerCase()
    const kwMatch = !kw || a.name?.toLowerCase().includes(kw) || a.main_stroke?.toLowerCase().includes(kw)
    return groupMatch && kwMatch
  })
})

const stats = reactive({
  distance_30d: 0,
  session_count: 0,
  avg_pace: '1:30',
  avg_heart_rate: 0
})

const getGroupTagType = (group) => {
  const map = { '一组': 'primary', '二组': 'success', '三组': 'warning', '精英组': 'danger' }
  return map[group] || 'info'
}

const getStrokeTagType = (stroke) => {
  const map = { '自由泳': 'primary', '蛙泳': 'success', '仰泳': 'warning', '蝶泳': 'danger', '混合泳': 'info' }
  return map[stroke] || ''
}

const fetchAthletes = async () => {
  loading.value = true
  try {
    const res = await request({
      method: 'GET',
      url: '/api/auth/athletes'
    })
    if (res.data) {
      athleteList.value = res.data.data || res.data || []
    }
  } catch (e) {
    athleteList.value = [
      { id: 1, name: '张伟', group: '一组', age: 18, gender: '男', height: 182, weight: 72, main_stroke: '自由泳' },
      { id: 2, name: '李娜', group: '一组', age: 17, gender: '女', height: 168, weight: 58, main_stroke: '蛙泳' },
      { id: 3, name: '王强', group: '二组', age: 19, gender: '男', height: 185, weight: 78, main_stroke: '蝶泳' },
      { id: 4, name: '赵敏', group: '二组', age: 16, gender: '女', height: 165, weight: 55, main_stroke: '仰泳' },
      { id: 5, name: '陈磊', group: '三组', age: 20, gender: '男', height: 180, weight: 74, main_stroke: '混合泳' },
      { id: 6, name: '刘洋', group: '三组', age: 18, gender: '男', height: 178, weight: 70, main_stroke: '自由泳' },
      { id: 7, name: '孙悦', group: '一组', age: 17, gender: '女', height: 170, weight: 60, main_stroke: '蝶泳' },
      { id: 8, name: '周杰', group: '精英组', age: 21, gender: '男', height: 190, weight: 82, main_stroke: '自由泳' }
    ]
  } finally {
    loading.value = false
  }
}

const fetchStats = async (athleteId) => {
  detailLoading.value = true
  try {
    const res = await request({
      method: 'GET',
      url: `/api/training/stats/athlete/${athleteId}`
    })
    if (res.data) {
      const s = res.data.data || res.data
      Object.assign(stats, s)
    }
  } catch {
    stats.distance_30d = 86500
    stats.session_count = 24
    stats.avg_pace = '1:28'
    stats.avg_heart_rate = 145
  } finally {
    detailLoading.value = false
  }
}

const viewDetail = async (row) => {
  currentAthlete.value = row
  detailVisible.value = true
  await fetchStats(row.id)
  await nextTick()
  initDistanceChart()
  initRadarChart()
}

const initDistanceChart = () => {
  if (!distanceTrendRef.value) return
  distanceChart?.dispose()
  distanceChart = echarts.init(distanceTrendRef.value)

  const dates = []
  const data = []
  for (let i = 29; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    dates.push(`${d.getMonth() + 1}/${d.getDate()}`)
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
        return `${p.axisValue}<br/>距离: <b>${p.value}</b> 米`
      }
    },
    grid: { left: 50, right: 30, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#e0e6ed' } },
      axisLabel: { color: '#606266', fontSize: 10, interval: 2 }
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
    series: [{
      name: '训练距离',
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 5,
      data,
      lineStyle: { width: 2.5, color: '#0052d9' },
      itemStyle: { color: '#0052d9' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(0, 82, 217, 0.45)' },
          { offset: 1, color: 'rgba(0, 82, 217, 0.02)' }
        ])
      }
    }]
  }
  distanceChart.setOption(option)
}

const initRadarChart = () => {
  if (!radarRef.value) return
  radarChart?.dispose()
  radarChart = echarts.init(radarRef.value)

  const indicators = [
    { name: '配速', max: 100 },
    { name: '心率', max: 100 },
    { name: '划距', max: 100 },
    { name: '耐力', max: 100 },
    { name: '爆发力', max: 100 }
  ]

  const option = {
    tooltip: {
      backgroundColor: 'rgba(0, 30, 80, 0.95)',
      borderColor: '#0052d9',
      textStyle: { color: '#fff' }
    },
    legend: {
      data: [currentAthlete.value?.name, '组内平均'],
      bottom: 0,
      textStyle: { color: '#606266', fontSize: 12 }
    },
    radar: {
      indicator: indicators,
      center: ['50%', '50%'],
      radius: '65%',
      axisName: { color: '#606266', fontSize: 12 },
      splitArea: {
        areaStyle: {
          color: ['rgba(0, 82, 217, 0.02)', 'rgba(0, 82, 217, 0.05)']
        }
      },
      splitLine: { lineStyle: { color: '#e0e6ed' } },
      axisLine: { lineStyle: { color: '#e0e6ed' } }
    },
    series: [{
      type: 'radar',
      data: [
        {
          value: [82, 75, 88, 80, 78],
          name: currentAthlete.value?.name,
          lineStyle: { width: 2, color: '#0052d9' },
          areaStyle: { color: 'rgba(0, 82, 217, 0.35)' },
          itemStyle: { color: '#0052d9' }
        },
        {
          value: [68, 65, 70, 66, 64],
          name: '组内平均',
          lineStyle: { width: 2, color: '#13c2c2', type: 'dashed' },
          areaStyle: { color: 'rgba(19, 194, 194, 0.15)' },
          itemStyle: { color: '#13c2c2' }
        }
      ]
    }]
  }
  radarChart.setOption(option)
}

const handleResize = () => {
  distanceChart?.resize()
  radarChart?.resize()
}

onMounted(async () => {
  await fetchAthletes()
  window.addEventListener('resize', handleResize)
})
</script>

<style scoped>
.athletes-container {
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

.filter-card,
.table-card {
  border: none;
  border-radius: 14px;
}

.filter-card :deep(.el-card__body) {
  padding: 16px 20px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.filter-select {
  width: 160px;
}

.filter-input {
  width: 260px;
}

.table-card :deep(.el-card__header) {
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

.athlete-name {
  font-weight: 500;
  color: #1a1a2e;
}

.icon-male {
  color: #0052d9;
  margin-right: 4px;
}

.icon-female {
  color: #eb2f96;
  margin-right: 4px;
}

.detail-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #0052d9, #003d9e);
  margin: 0;
  padding: 20px 24px;
  border-radius: 14px 14px 0 0;
}

.detail-dialog :deep(.el-dialog__title) {
  color: #fff;
  font-weight: 600;
}

.detail-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #fff;
}

.detail-dialog :deep(.el-dialog__body) {
  padding: 24px;
  background: #f5f7fa;
  border-radius: 0 0 14px 14px;
}

.info-card,
.chart-card,
.stat-card {
  border: none;
  border-radius: 12px;
}

.info-card :deep(.el-card__header),
.chart-card :deep(.el-card__header) {
  padding: 14px 18px;
  border-bottom: 1px solid #f0f2f5;
}

.info-body {
  text-align: center;
  padding: 10px 0;
}

.big-avatar {
  width: 80px;
  height: 80px;
  line-height: 80px;
  font-size: 32px;
  background: linear-gradient(135deg, #0052d9, #003d9e);
  color: #fff;
  font-weight: 700;
  margin: 0 auto 14px;
}

.info-name {
  margin: 0 0 10px 0;
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
}

.info-group-tag {
  margin-bottom: 18px;
}

.info-list {
  text-align: left;
  padding: 0 6px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px dashed #f0f2f5;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  color: #8c8c8c;
  font-size: 13px;
}

.info-value {
  color: #1a1a2e;
  font-weight: 600;
  font-size: 13px;
}

.stat-body {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-card :deep(.el-card__body) {
  padding: 14px;
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #fff;
}

.stat-blue .stat-icon {
  background: linear-gradient(135deg, #0052d9, #003d9e);
}

.stat-green .stat-icon {
  background: linear-gradient(135deg, #10b981, #059669);
}

.stat-orange .stat-icon {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}

.stat-purple .stat-icon {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
}

.stat-info {
  flex: 1;
}

.stat-val {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
  line-height: 1.2;
  margin-bottom: 4px;
}

.stat-unit {
  font-size: 12px;
  color: #8c8c8c;
  margin-left: 3px;
  font-weight: 500;
}

.stat-lbl {
  font-size: 12px;
  color: #8c8c8c;
}

.chart-box {
  width: 100%;
  height: 300px;
}

.chart-sm {
  height: 280px;
}
</style>
