<template>
  <div class="all-data-page">
    <el-card class="page-header-card">
      <div class="page-header">
        <div>
          <h2 class="page-title"><el-icon><DataLine /></el-icon> 全局训练数据总览</h2>
          <p class="page-subtitle">三组横向对比 · 全运动员数据 · 教练团队联系</p>
        </div>
        <div class="header-actions">
          <el-tag type="primary" effect="dark" round size="large">
            数据更新时间：{{ lastUpdateTime }}
          </el-tag>
          <el-button type="primary" :icon="Refresh" @click="refreshAll" style="margin-left: 12px;">
            刷新数据
          </el-button>
        </div>
      </div>
    </el-card>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :xs="24" :sm="24" :md="8">
        <div class="group-stat-card team1">
          <div class="group-header">
            <div class="group-icon-wrapper">
              <el-icon :size="32"><Trophy /></el-icon>
            </div>
            <div class="group-name">精英一组</div>
          </div>
          <div class="group-metrics">
            <div class="metric-item">
              <div class="metric-label">
                <el-icon><User /></el-icon> 总人数
              </div>
              <div class="metric-value">{{ group1Stats.totalAthletes }}<small>人</small></div>
            </div>
            <div class="metric-item">
              <div class="metric-label">
                <el-icon><Location /></el-icon> 总距离
              </div>
              <div class="metric-value">{{ group1Stats.totalDistance }}<small>km</small></div>
            </div>
            <div class="metric-item">
              <div class="metric-label">
                <el-icon><Timer /></el-icon> 平均配速
              </div>
              <div class="metric-value">{{ group1Stats.avgPace }}<small>/100m</small></div>
            </div>
          </div>
          <div class="group-footer">
            <el-icon><TrendCharts /></el-icon> 本月训练完成率 {{ group1Stats.completionRate }}%
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="24" :md="8">
        <div class="group-stat-card team2">
          <div class="group-header">
            <div class="group-icon-wrapper">
              <el-icon :size="32"><Medal /></el-icon>
            </div>
            <div class="group-name">冲刺二组</div>
          </div>
          <div class="group-metrics">
            <div class="metric-item">
              <div class="metric-label">
                <el-icon><User /></el-icon> 总人数
              </div>
              <div class="metric-value">{{ group2Stats.totalAthletes }}<small>人</small></div>
            </div>
            <div class="metric-item">
              <div class="metric-label">
                <el-icon><Location /></el-icon> 总距离
              </div>
              <div class="metric-value">{{ group2Stats.totalDistance }}<small>km</small></div>
            </div>
            <div class="metric-item">
              <div class="metric-label">
                <el-icon><Timer /></el-icon> 平均配速
              </div>
              <div class="metric-value">{{ group2Stats.avgPace }}<small>/100m</small></div>
            </div>
          </div>
          <div class="group-footer">
            <el-icon><TrendCharts /></el-icon> 本月训练完成率 {{ group2Stats.completionRate }}%
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="24" :md="8">
        <div class="group-stat-card team3">
          <div class="group-header">
            <div class="group-icon-wrapper">
              <el-icon :size="32"><Flag /></el-icon>
            </div>
            <div class="group-name">耐力三组</div>
          </div>
          <div class="group-metrics">
            <div class="metric-item">
              <div class="metric-label">
                <el-icon><User /></el-icon> 总人数
              </div>
              <div class="metric-value">{{ group3Stats.totalAthletes }}<small>人</small></div>
            </div>
            <div class="metric-item">
              <div class="metric-label">
                <el-icon><Location /></el-icon> 总距离
              </div>
              <div class="metric-value">{{ group3Stats.totalDistance }}<small>km</small></div>
            </div>
            <div class="metric-item">
              <div class="metric-label">
                <el-icon><Timer /></el-icon> 平均配速
              </div>
              <div class="metric-value">{{ group3Stats.avgPace }}<small>/100m</small></div>
            </div>
          </div>
          <div class="group-footer">
            <el-icon><TrendCharts /></el-icon> 本月训练完成率 {{ group3Stats.completionRate }}%
          </div>
        </div>
      </el-col>
    </el-row>

    <el-card class="chart-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span class="card-title"><el-icon><DataAnalysis /></el-icon> 三组最近30天训练距离对比</span>
          <div class="chart-legend-tags">
            <el-tag type="primary" effect="dark" size="small">精英一组</el-tag>
            <el-tag type="success" effect="dark" size="small" style="margin-left: 8px;">冲刺二组</el-tag>
            <el-tag type="warning" effect="dark" size="small" style="margin-left: 8px;">耐力三组</el-tag>
          </div>
        </div>
      </template>
      <div ref="groupCompareChartRef" class="chart-container-large"></div>
    </el-card>

    <el-card class="table-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span class="card-title"><el-icon><List /></el-icon> 全部运动员数据</span>
          <div class="header-actions">
            <el-select v-model="filterGroup" placeholder="按组筛选" style="width: 140px; margin-right: 12px;" clearable>
              <el-option label="全部组" value="" />
              <el-option label="精英一组" value="精英一组" />
              <el-option label="冲刺二组" value="冲刺二组" />
              <el-option label="耐力三组" value="耐力三组" />
            </el-select>
            <el-input
              v-model="searchKeyword"
              placeholder="搜索姓名/编号"
              style="width: 200px; margin-right: 12px;"
              clearable
              :prefix-icon="Search"
            />
          </div>
        </div>
      </template>
      <el-table :data="filteredAthletes" stripe v-loading="loadingAthletes">
        <el-table-column type="index" label="序号" width="70" align="center" />
        <el-table-column label="姓名" width="120">
          <template #default="{ row }">
            <div class="athlete-name-cell">
              <el-avatar :size="32" :style="{ background: getAvatarColor(row.name) }">
                {{ row.name ? row.name.charAt(0) : '?' }}
              </el-avatar>
              <span class="name-text">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="group" label="组" width="110">
          <template #default="{ row }">
            <el-tag :type="getGroupTagType(row.group)" effect="dark" size="small">{{ row.group }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="age" label="年龄" width="80" align="center" />
        <el-table-column prop="gender" label="性别" width="80" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.gender === '男'" :size="18" style="color: #409eff;"><Male /></el-icon>
            <el-icon v-else :size="18" style="color: #f56c6c;"><Female /></el-icon>
            <span style="margin-left: 4px;">{{ row.gender }}</span>
          </template>
        </el-table-column>
        <el-table-column label="身高" width="90" align="center">
          <template #default="{ row }">{{ row.height }}<small style="color:#909399"> cm</small></template>
        </el-table-column>
        <el-table-column label="体重" width="90" align="center">
          <template #default="{ row }">{{ row.weight }}<small style="color:#909399"> kg</small></template>
        </el-table-column>
        <el-table-column prop="specialty" label="主项" width="130">
          <template #default="{ row }">
            <el-tag type="info" size="small" effect="plain">{{ row.specialty }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="本月距离" width="110" align="center">
          <template #default="{ row }">
            <span class="distance-text">{{ row.monthDistance }}</span>
            <small style="color:#909399"> km</small>
          </template>
        </el-table-column>
        <el-table-column prop="avgPace" label="平均配速" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="primary" effect="plain" size="small">{{ row.avgPace }}/100m</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="出勤率" width="130">
          <template #default="{ row }">
            <el-progress :percentage="row.attendanceRate" :stroke-width="10"
              :status="row.attendanceRate >= 90 ? 'success' : row.attendanceRate >= 75 ? '' : 'exception'" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-row :gutter="20" style="margin-top: 20px; margin-bottom: 20px;">
      <el-col :xs="24" :sm="24" :md="8">
        <div class="coach-card">
          <div class="coach-card-header team1-header">
            <el-avatar :size="64" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png" />
            <div class="coach-title">
              <div class="coach-name">李明辉 主教练</div>
              <el-tag type="primary" effect="dark" size="small">负责：精英一组</el-tag>
            </div>
          </div>
          <div class="coach-contact-list">
            <div class="contact-item">
              <el-icon><Phone /></el-icon>
              <span class="contact-label">联系电话</span>
              <span class="contact-value">138-8888-0001</span>
            </div>
            <div class="contact-item">
              <el-icon><Message /></el-icon>
              <span class="contact-label">微信</span>
              <span class="contact-value">li_minghui_coach</span>
            </div>
            <div class="contact-item">
              <el-icon><Message /></el-icon>
              <span class="contact-label">邮箱</span>
              <span class="contact-value">limh@swimteam.cn</span>
            </div>
            <div class="contact-item">
              <el-icon><Clock /></el-icon>
              <span class="contact-label">办公时间</span>
              <span class="contact-value">周一至周六 06:00-18:00</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="24" :md="8">
        <div class="coach-card">
          <div class="coach-card-header team2-header">
            <el-avatar :size="64" src="https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png" />
            <div class="coach-title">
              <div class="coach-name">王志强 高级教练</div>
              <el-tag type="success" effect="dark" size="small">负责：冲刺二组</el-tag>
            </div>
          </div>
          <div class="coach-contact-list">
            <div class="contact-item">
              <el-icon><Phone /></el-icon>
              <span class="contact-label">联系电话</span>
              <span class="contact-value">139-9999-0002</span>
            </div>
            <div class="contact-item">
              <el-icon><Message /></el-icon>
              <span class="contact-label">微信</span>
              <span class="contact-value">wang_zq_sprint</span>
            </div>
            <div class="contact-item">
              <el-icon><Message /></el-icon>
              <span class="contact-label">邮箱</span>
              <span class="contact-value">wangzq@swimteam.cn</span>
            </div>
            <div class="contact-item">
              <el-icon><Clock /></el-icon>
              <span class="contact-label">办公时间</span>
              <span class="contact-value">周二至周日 06:00-18:00</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="24" :md="8">
        <div class="coach-card">
          <div class="coach-card-header team3-header">
            <el-avatar :size="64" src="https://cube.elemecdn.com/9/c2/f0ee8a3c7c9638a54940382568c9dpng.png" />
            <div class="coach-title">
              <div class="coach-name">张海涛 资深教练</div>
              <el-tag type="warning" effect="dark" size="small">负责：耐力三组</el-tag>
            </div>
          </div>
          <div class="coach-contact-list">
            <div class="contact-item">
              <el-icon><Phone /></el-icon>
              <span class="contact-label">联系电话</span>
              <span class="contact-value">137-7777-0003</span>
            </div>
            <div class="contact-item">
              <el-icon><Message /></el-icon>
              <span class="contact-label">微信</span>
              <span class="contact-value">zhang_ht_endurance</span>
            </div>
            <div class="contact-item">
              <el-icon><Message /></el-icon>
              <span class="contact-label">邮箱</span>
              <span class="contact-value">zhanght@swimteam.cn</span>
            </div>
            <div class="contact-item">
              <el-icon><Clock /></el-icon>
              <span class="contact-label">办公时间</span>
              <span class="contact-value">周一至周六 05:30-19:00</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DataLine, Refresh, Trophy, Medal, Flag, User, Location, Timer,
  TrendCharts, DataAnalysis, List, Search, Male, Female,
  Phone, Message, Clock
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import request from '@/utils/request'

const lastUpdateTime = ref(dayjs().format('YYYY-MM-DD HH:mm:ss'))
const filterGroup = ref('')
const searchKeyword = ref('')
const loadingAthletes = ref(false)
const groupCompareChartRef = ref(null)

const group1Stats = reactive({
  totalAthletes: 18,
  totalDistance: 2856,
  avgPace: '1:12',
  completionRate: 95
})

const group2Stats = reactive({
  totalAthletes: 16,
  totalDistance: 2340,
  avgPace: '1:08',
  completionRate: 91
})

const group3Stats = reactive({
  totalAthletes: 20,
  totalDistance: 3520,
  avgPace: '1:22',
  completionRate: 89
})

const athletes = ref([])

const mockAthletes = [
  { name: '陈天宇', group: '精英一组', age: 19, gender: '男', height: 188, weight: 82, specialty: '100m自由泳', monthDistance: 186, avgPace: '1:02', attendanceRate: 98 },
  { name: '林雨涵', group: '精英一组', age: 18, gender: '女', height: 175, weight: 65, specialty: '200m蝶泳', monthDistance: 172, avgPace: '1:10', attendanceRate: 96 },
  { name: '王浩然', group: '精英一组', age: 20, gender: '男', height: 190, weight: 85, specialty: '400m自由泳', monthDistance: 195, avgPace: '1:08', attendanceRate: 94 },
  { name: '刘诗雯', group: '精英一组', age: 17, gender: '女', height: 170, weight: 60, specialty: '100m仰泳', monthDistance: 158, avgPace: '1:12', attendanceRate: 92 },
  { name: '赵子轩', group: '精英一组', age: 19, gender: '男', height: 185, weight: 80, specialty: '200m混合泳', monthDistance: 178, avgPace: '1:05', attendanceRate: 97 },
  { name: '周晨曦', group: '冲刺二组', age: 17, gender: '男', height: 182, weight: 76, specialty: '50m自由泳', monthDistance: 132, avgPace: '0:55', attendanceRate: 93 },
  { name: '吴佳怡', group: '冲刺二组', age: 16, gender: '女', height: 168, weight: 58, specialty: '50m蝶泳', monthDistance: 125, avgPace: '1:02', attendanceRate: 90 },
  { name: '郑凯文', group: '冲刺二组', age: 18, gender: '男', height: 180, weight: 74, specialty: '100m蛙泳', monthDistance: 142, avgPace: '1:08', attendanceRate: 91 },
  { name: '孙梦琪', group: '冲刺二组', age: 17, gender: '女', height: 172, weight: 62, specialty: '50m仰泳', monthDistance: 128, avgPace: '1:00', attendanceRate: 89 },
  { name: '杨帆', group: '冲刺二组', age: 18, gender: '男', height: 184, weight: 78, specialty: '50m蛙泳', monthDistance: 138, avgPace: '1:06', attendanceRate: 92 },
  { name: '许文博', group: '耐力三组', age: 21, gender: '男', height: 192, weight: 88, specialty: '1500m自由泳', monthDistance: 210, avgPace: '1:20', attendanceRate: 95 },
  { name: '何雅婷', group: '耐力三组', age: 20, gender: '女', height: 178, weight: 68, specialty: '800m自由泳', monthDistance: 186, avgPace: '1:25', attendanceRate: 90 },
  { name: '黄俊杰', group: '耐力三组', age: 22, gender: '男', height: 195, weight: 92, specialty: '10km公开水域', monthDistance: 235, avgPace: '1:22', attendanceRate: 88 },
  { name: '朱晓彤', group: '耐力三组', age: 19, gender: '女', height: 174, weight: 64, specialty: '400m混合泳', monthDistance: 168, avgPace: '1:28', attendanceRate: 86 },
  { name: '马天宇', group: '耐力三组', age: 20, gender: '男', height: 188, weight: 84, specialty: '200m蝶泳', monthDistance: 192, avgPace: '1:18', attendanceRate: 85 },
  { name: '徐嘉怡', group: '精英一组', age: 18, gender: '女', height: 172, weight: 62, specialty: '200m蛙泳', monthDistance: 164, avgPace: '1:15', attendanceRate: 93 },
  { name: '马超然', group: '冲刺二组', age: 16, gender: '男', height: 178, weight: 72, specialty: '100m蝶泳', monthDistance: 136, avgPace: '1:04', attendanceRate: 88 },
  { name: '郭美玲', group: '耐力三组', age: 21, gender: '女', height: 176, weight: 66, specialty: '1500m自由泳', monthDistance: 202, avgPace: '1:24', attendanceRate: 84 }
]

const formatPace = (pace) => {
  if (typeof pace === 'string') return pace
  if (typeof pace !== 'number' || pace <= 0) return '0:00'
  const minutes = Math.floor(pace / 60)
  const seconds = Math.floor(pace % 60)
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

const fetchAllData = async () => {
  loadingAthletes.value = true
  try {
    const res = await request.get('/api/headcoach/all-data')
    const data = res.data?.data || res.data || {}

    const groups = data.groups || []
    if (groups && Array.isArray(groups)) {
      groups.forEach(g => {
        const formattedG = { ...g, avgPace: formatPace(g.avgPace) }
        if (g.name === '精英一组' || g.groupId === 1) Object.assign(group1Stats, formattedG)
        if (g.name === '冲刺二组' || g.groupId === 2) Object.assign(group2Stats, formattedG)
        if (g.name === '耐力三组' || g.groupId === 3) Object.assign(group3Stats, formattedG)
      })
    }

    const athletesList = data.athletes || []
    if (athletesList && Array.isArray(athletesList) && athletesList.length > 0) {
      athletes.value = athletesList.map(a => ({
        ...a,
        name: a.name || a.full_name,
        attendanceRate: a.attendanceRate ?? a.completionRate,
        monthDistance: a.monthDistance ?? a.totalDistance,
        avgPace: formatPace(a.avgPace),
      }))
    } else {
      athletes.value = mockAthletes
    }
  } catch (e) {
    console.log('获取全部数据失败，使用Mock数据', e.message)
    athletes.value = mockAthletes
  } finally {
    loadingAthletes.value = false
  }
}

const filteredAthletes = computed(() => {
  return athletes.value.filter(a => {
    const matchGroup = !filterGroup.value || a.group === filterGroup.value
    const matchKeyword = !searchKeyword.value ||
      a.name?.includes(searchKeyword.value)
    return matchGroup && matchKeyword
  })
})

const getGroupTagType = (group) => {
  if (group === '精英一组') return 'primary'
  if (group === '冲刺二组') return 'success'
  if (group === '耐力三组') return 'warning'
  return 'info'
}

const getAvatarColor = (name) => {
  const colors = [
    '#0052d9', '#0088cc', '#13c2c2', '#52c41a',
    '#faad14', '#eb2f96', '#722ed1', '#2f54eb'
  ]
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return colors[Math.abs(hash) % colors.length]
}

const refreshAll = async () => {
  await fetchAllData()
  lastUpdateTime.value = dayjs().format('YYYY-MM-DD HH:mm:ss')
  ElMessage.success('全局数据刷新成功')
  initGroupCompareChart()
}

const initGroupCompareChart = () => {
  if (!groupCompareChartRef.value) return
  const existing = echarts.getInstanceByDom(groupCompareChartRef.value)
  if (existing) existing.dispose()
  const chart = echarts.init(groupCompareChartRef.value)
  const days = Array.from({ length: 30 }, (_, i) => dayjs().subtract(29 - i, 'day').format('MM-DD'))
  const genLine = (base, variance, amplitude) => {
    const arr = []
    let val = base
    for (let i = 0; i < 30; i++) {
      val += (Math.random() - 0.5) * variance
      val = Math.max(base - amplitude, Math.min(base + amplitude, val))
      arr.push(Number(val.toFixed(1)))
    }
    return arr
  }
  const team1Data = genLine(95, 12, 40)
  const team2Data = genLine(78, 10, 35)
  const team3Data = genLine(117, 14, 45)
  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 30, 80, 0.95)',
      borderColor: '#0052d9',
      borderWidth: 1,
      textStyle: { color: '#fff', fontSize: 13 },
      axisPointer: { type: 'cross', lineStyle: { color: '#0052d9', width: 1, type: 'dashed' } }
    },
    legend: {
      data: ['精英一组', '冲刺二组', '耐力三组'],
      top: 10,
      right: 20,
      textStyle: { fontSize: 13, color: '#303133' }
    },
    grid: { left: '3%', right: '4%', bottom: '12%', top: '16%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: days,
      axisLine: { lineStyle: { color: '#e4e7ed' } },
      axisLabel: { color: '#606266', fontSize: 11, rotate: 35 }
    },
    yAxis: {
      type: 'value',
      name: '训练距离 (km)',
      nameTextStyle: { color: '#606266', fontSize: 12, padding: [0, 0, 0, 50] },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f0f2f5', type: 'dashed' } },
      axisLabel: { color: '#909399', fontSize: 11 }
    },
    series: [
      {
        name: '精英一组',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 5,
        lineStyle: { width: 2.5, color: '#0052d9' },
        itemStyle: { color: '#0052d9', borderWidth: 2, borderColor: '#fff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 82, 217, 0.35)' },
            { offset: 1, color: 'rgba(0, 82, 217, 0.02)' }
          ])
        },
        data: team1Data
      },
      {
        name: '冲刺二组',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 5,
        lineStyle: { width: 2.5, color: '#23c06a' },
        itemStyle: { color: '#23c06a', borderWidth: 2, borderColor: '#fff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(35, 192, 106, 0.3)' },
            { offset: 1, color: 'rgba(35, 192, 106, 0.02)' }
          ])
        },
        data: team2Data
      },
      {
        name: '耐力三组',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 5,
        lineStyle: { width: 2.5, color: '#ff9500' },
        itemStyle: { color: '#ff9500', borderWidth: 2, borderColor: '#fff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255, 149, 0, 0.3)' },
            { offset: 1, color: 'rgba(255, 149, 0, 0.02)' }
          ])
        },
        data: team3Data
      }
    ]
  })
}

onMounted(async () => {
  await nextTick()
  await fetchAllData()
  initGroupCompareChart()
  window.addEventListener('resize', () => {
    if (groupCompareChartRef.value) {
      echarts.getInstanceByDom(groupCompareChartRef.value)?.resize()
    }
  })
})
</script>

<style scoped>
.all-data-page {
  min-height: 100%;
  padding: 4px 2px 8px 2px;
}

.page-header-card {
  background: linear-gradient(135deg, #0052d9 0%, #003d9e 50%, #002a6e 100%);
  border: none;
  border-radius: 14px;
}

.page-header-card :deep(.el-card__body) {
  padding: 24px 28px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.page-title {
  color: #fff;
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-subtitle {
  color: rgba(255, 255, 255, 0.75);
  font-size: 14px;
  margin: 6px 0 0 0;
}

.header-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.group-stat-card {
  background: #fff;
  border-radius: 14px;
  padding: 22px 20px;
  box-shadow: 0 4px 16px rgba(0, 30, 80, 0.08);
  border: 1px solid #ebeef5;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.group-stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 30px rgba(0, 30, 80, 0.14);
}

.group-stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  border-radius: 14px 14px 0 0;
}

.group-stat-card.team1::before { background: linear-gradient(90deg, #0052d9, #0088cc); }
.group-stat-card.team2::before { background: linear-gradient(90deg, #23c06a, #52c41a); }
.group-stat-card.team3::before { background: linear-gradient(90deg, #ff9500, #ffb84d); }

.group-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 18px;
}

.group-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.team1 .group-icon-wrapper { background: linear-gradient(135deg, #0052d9, #0088cc); }
.team2 .group-icon-wrapper { background: linear-gradient(135deg, #23c06a, #52c41a); }
.team3 .group-icon-wrapper { background: linear-gradient(135deg, #ff9500, #ffb84d); }

.group-name {
  font-size: 20px;
  font-weight: 700;
  color: #1f2d3d;
}

.group-metrics {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 16px;
  padding: 12px 0;
  border-top: 1px dashed #e4e7ed;
  border-bottom: 1px dashed #e4e7ed;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-label {
  font-size: 13px;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 5px;
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1;
}

.team1 .metric-value { color: #0052d9; }
.team2 .metric-value { color: #23c06a; }
.team3 .metric-value { color: #ff9500; }

.metric-value small {
  font-size: 12px;
  font-weight: normal;
  color: #909399;
  margin-left: 3px;
}

.group-footer {
  font-size: 13px;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 6px;
  padding-top: 4px;
}

.chart-card {
  border-radius: 14px;
  border: 1px solid #ebeef5;
  box-shadow: 0 2px 12px rgba(0, 30, 80, 0.05);
}

.chart-card :deep(.el-card__header) {
  border-bottom: 1px solid #f0f2f5;
  padding: 16px 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2d3d;
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-title .el-icon {
  color: #0052d9;
}

.chart-legend-tags {
  display: flex;
  align-items: center;
}

.chart-container-large {
  width: 100%;
  height: 380px;
}

.table-card {
  border-radius: 14px;
  border: 1px solid #ebeef5;
  box-shadow: 0 2px 12px rgba(0, 30, 80, 0.05);
}

.table-card :deep(.el-card__header) {
  border-bottom: 1px solid #f0f2f5;
  padding: 16px 20px;
}

.athlete-name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.name-text {
  font-weight: 500;
  color: #1f2d3d;
}

.distance-text {
  font-weight: 700;
  color: #0052d9;
  font-size: 14px;
}

.coach-card {
  background: #fff;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 30, 80, 0.08);
  border: 1px solid #ebeef5;
  transition: all 0.3s ease;
}

.coach-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 28px rgba(0, 30, 80, 0.13);
}

.coach-card-header {
  padding: 22px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.team1-header {
  background: linear-gradient(135deg, #0052d9 0%, #0066bb 100%);
}

.team2-header {
  background: linear-gradient(135deg, #23c06a 0%, #3ec97e 100%);
}

.team3-header {
  background: linear-gradient(135deg, #ff9500 0%, #ffaa33 100%);
}

.coach-title {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.coach-name {
  color: #fff;
  font-size: 18px;
  font-weight: 700;
}

.coach-contact-list {
  padding: 18px 20px 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  padding: 8px 10px;
  background: #f8fafc;
  border-radius: 8px;
  transition: background 0.2s;
}

.contact-item:hover {
  background: #eef3fa;
}

.contact-item .el-icon {
  color: #0052d9;
  font-size: 16px;
  flex-shrink: 0;
}

.contact-label {
  color: #606266;
  min-width: 68px;
}

.contact-value {
  color: #1f2d3d;
  font-weight: 500;
  font-family: 'SF Mono', Consolas, monospace;
}

@media (max-width: 768px) {
  .page-title { font-size: 18px; }
  .page-header-card :deep(.el-card__body) { padding: 18px; }
  .chart-container-large { height: 300px; }
  .metric-value { font-size: 20px; }
  .group-name { font-size: 17px; }
}
</style>
