<template>
  <div class="myplan-container">
    <div class="page-header">
      <div>
        <h2 class="page-title">我的训练计划</h2>
        <p class="page-subtitle">查看本周教练为您安排的训练计划，加油训练！</p>
      </div>
      <div class="week-info">
        <el-button :icon="ArrowLeft" circle size="small" @click="changeWeek(-1)" />
        <span class="week-label">{{ weekLabel }}</span>
        <el-button :icon="ArrowRight" circle size="small" @click="changeWeek(1)" />
      </div>
    </div>

    <el-row :gutter="14" class="week-bar">
      <el-col
        v-for="(day, idx) in weekDays"
        :key="idx"
        :xs="24" :sm="12" :md="3"
      >
        <div
          class="day-card"
          :class="{ active: selectedIdx === idx, today: day.isToday, empty: !day.hasPlan }"
          @click="selectedIdx = idx"
        >
          <div class="dc-top">
            <span class="dc-name">{{ day.name }}</span>
            <el-tag v-if="day.isToday" type="danger" effect="dark" size="small" round>今天</el-tag>
          </div>
          <div class="dc-date">{{ day.date }}</div>
          <div class="dc-status">
            <el-icon v-if="day.hasPlan" class="icon-yes"><CircleCheckFilled /></el-icon>
            <span v-else class="no-plan">暂无计划</span>
          </div>
          <div v-if="day.hasPlan" class="dc-summary">
            <span class="dc-dist">{{ day.totalDistance }}m</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-card v-if="selectedDayPlan" class="detail-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon class="title-icon"><Document /></el-icon>
            {{ weekDays[selectedIdx]?.name }} ({{ weekDays[selectedIdx]?.fullDate }}) 训练详情
          </span>
          <el-tag v-if="selectedDayPlan.intensity" :type="intensityType" effect="dark" size="small">
            {{ intensityLabel }}
          </el-tag>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :md="8" :sm="24">
          <el-card class="phase-card warm" shadow="hover">
            <div class="phase-head">
              <el-icon class="phase-icon"><Sunrise /></el-icon>
              <span class="phase-name">热身</span>
            </div>
            <div class="phase-val">
              <span class="num">{{ selectedDayPlan.warmup_distance || 0 }}</span>
              <span class="unit">米</span>
            </div>
            <div class="phase-desc">轻松配速 · 活动关节</div>
          </el-card>
        </el-col>
        <el-col :md="8" :sm="24">
          <el-card class="phase-card main" shadow="hover">
            <div class="phase-head">
              <el-icon class="phase-icon"><Flame /></el-icon>
              <span class="phase-name">主训练集</span>
            </div>
            <div class="phase-val">
              <span class="num">{{ selectedDayPlan.main_distance || 0 }}</span>
              <span class="unit">米</span>
              <el-tag size="small" type="primary" effect="plain" class="set-tag">
                {{ (selectedDayPlan.sets || []).length }} 组
              </el-tag>
            </div>
            <div class="phase-desc">核心训练 · 全力以赴</div>
          </el-card>
        </el-col>
        <el-col :md="8" :sm="24">
          <el-card class="phase-card cool" shadow="hover">
            <div class="phase-head">
              <el-icon class="phase-icon"><Moon /></el-icon>
              <span class="phase-name">冷身放松</span>
            </div>
            <div class="phase-val">
              <span class="num">{{ selectedDayPlan.cooldown_distance || 0 }}</span>
              <span class="unit">米</span>
            </div>
            <div class="phase-desc">慢速放松 · 拉伸恢复</div>
          </el-card>
        </el-col>
      </el-row>

      <el-card class="sets-card" shadow="hover" style="margin-top: 20px;">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon class="title-icon"><List /></el-icon>
              主训练集详情（只读）
            </span>
          </div>
        </template>
        <el-table
          :data="selectedDayPlan.sets || []"
          border
          stripe
          style="width: 100%"
          class="sets-table"
        >
          <el-table-column label="组序" type="index" width="80" align="center">
            <template #default="{ $index }">
              <el-tag type="primary" effect="dark" size="small">第 {{ $index + 1 }} 组</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="distance" label="距离" width="130" align="center">
            <template #default="{ row }">
              <span class="num-bold">{{ row.distance || 0 }} 米</span>
            </template>
          </el-table-column>
          <el-table-column prop="target_pace" label="目标配速" width="150" align="center">
            <template #default="{ row }">
              <el-tag type="success" effect="plain" size="small">
                {{ formatPace(row.target_pace) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="rest_seconds" label="间歇" width="130" align="center">
            <template #default="{ row }">
              <el-tag type="warning" effect="plain" size="small">
                {{ row.rest_seconds || 0 }} 秒
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="note" label="泳姿 / 要求">
            <template #default="{ row }">
              <span v-if="row.note" class="note-text">{{ row.note }}</span>
              <span v-else class="empty-tip">-</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card v-if="selectedDayPlan.notes" class="notes-card" shadow="never" style="margin-top: 20px;">
        <div class="notes-head">
          <el-icon class="notes-icon"><ChatDotRound /></el-icon>
          <span>教练备注</span>
        </div>
        <p class="notes-body">{{ selectedDayPlan.notes }}</p>
      </el-card>
    </el-card>

    <el-empty
      v-else
      :description="`${weekDays[selectedIdx]?.name}暂无训练计划，好好休息吧！`"
      class="empty-area"
    >
      <el-icon :size="60" color="#c0c4cc"><CoffeeCup /></el-icon>
    </el-empty>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, ArrowRight, CircleCheckFilled, Document, Sunrise, MagicStick, Moon,
  List, ChatDotRound, CoffeeCup
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'

dayjs.locale('zh-cn')
const userStore = useUserStore()

const selectedIdx = ref(dayjs().day() === 0 ? 6 : dayjs().day() - 1)
const weekStart = ref(dayjs().startOf('week').add(1, 'day'))
const planCache = reactive({})
const loading = ref(false)

const weekNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const weekLabel = computed(() => {
  const end = weekStart.value.add(6, 'day')
  return `${weekStart.value.format('YYYY年M月D日')} - ${end.format('M月D日')}`
})

const weekDays = computed(() => {
  return weekNames.map((name, idx) => {
    const d = weekStart.value.add(idx, 'day')
    const key = d.format('YYYY-MM-DD')
    const plan = planCache[key]
    return {
      name,
      date: d.format('M/D'),
      fullDate: d.format('YYYY-MM-DD'),
      isToday: d.format('YYYY-MM-DD') === dayjs().format('YYYY-MM-DD'),
      hasPlan: !!plan,
      totalDistance: plan ? calcDistance(plan) : 0
    }
  })
})

const selectedDayPlan = computed(() => {
  const key = weekDays.value[selectedIdx.value]?.fullDate
  return key ? planCache[key] : null
})

const intensityType = computed(() => {
  const map = { low: 'success', medium: 'warning', high: 'danger', extreme: 'danger' }
  return map[selectedDayPlan.value?.intensity] || 'info'
})
const intensityLabel = computed(() => {
  const map = { low: '恢复课', medium: '常规课', high: '强度课', extreme: '比赛配速' }
  return map[selectedDayPlan.value?.intensity] || '常规课'
})

const calcDistance = (plan) => {
  const sets = Array.isArray(plan.sets) ? plan.sets : []
  const main = sets.reduce((sum, s) => sum + (parseInt(s.distance) || 0), 0)
  return (parseInt(plan.warmup_distance) || 0) + main + (parseInt(plan.cooldown_distance) || 0)
}

const formatPace = (pace) => {
  if (!pace) return '-'
  if (typeof pace === 'string' && pace.includes(':')) return pace + ' /100m'
  return pace + ' /100m'
}

const changeWeek = (delta) => {
  weekStart.value = weekStart.value.add(delta * 7, 'day')
  selectedIdx.value = 0
  fetchPlans()
}

const fetchPlans = async () => {
  loading.value = true
  try {
    const res = await request({
      method: 'GET',
      url: '/api/training/plans',
      params: {
        athlete_id: userStore.userId,
        week_start: weekStart.value.format('YYYY-MM-DD')
      }
    })
    if (res.data) {
      Object.keys(planCache).forEach(k => delete planCache[k])
      const plans = res.data.data || res.data || []
      plans.forEach(p => {
        const plan = transformPlan(p)
        planCache[p.plan_date] = plan
      })
    }
  } catch {
    Object.keys(planCache).forEach(k => delete planCache[k])
    const base = weekStart.value
    ;[0, 1, 2, 3, 4].forEach(i => {
      const dateKey = base.add(i, 'day').format('YYYY-MM-DD')
      planCache[dateKey] = {
        warmup_distance: 400,
        cooldown_distance: 200,
        intensity: i === 2 ? 'high' : i === 4 ? 'low' : 'medium',
        sets: [
          { distance: 800, target_pace: '1:30', rest_seconds: 60, note: '自由泳' },
          { distance: 600, target_pace: '1:28', rest_seconds: 50, note: '自由泳 快节奏' },
          { distance: 400, target_pace: '1:25', rest_seconds: 80, note: '包干' }
        ],
        notes: i === 2 ? '今天强度课，注意控制配速，最后一组全力冲刺！' : '按计划完成即可，注意补水和休息。'
      }
      planCache[dateKey].main_distance = 1800
    })
  } finally {
    loading.value = false
  }
}

const transformPlan = (apiPlan) => {
  const sets = Array.isArray(apiPlan.sets) ? apiPlan.sets.map(s => ({
    distance: s.distance || 0,
    target_pace: s.target_pace || '',
    rest_seconds: s.rest_seconds || 0,
    note: s.note || ''
  })) : []
  const main = sets.reduce((sum, s) => sum + (parseInt(s.distance) || 0), 0)
  return {
    warmup_distance: apiPlan.warmup_distance || 0,
    cooldown_distance: apiPlan.cooldown_distance || 0,
    intensity: apiPlan.intensity,
    sets,
    main_distance: main,
    notes: apiPlan.notes || ''
  }
}

onMounted(() => {
  fetchPlans()
})
</script>

<style scoped>
.myplan-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 14px;
}
.page-title { margin: 0 0 6px 0; font-size: 24px; font-weight: 700; color: #1a1a2e; }
.page-subtitle { margin: 0; color: #8c8c8c; font-size: 14px; }
.week-info {
  display: flex; align-items: center; gap: 12px;
  background: #fff; padding: 8px 14px; border-radius: 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.week-label { font-weight: 600; color: #1a1a2e; min-width: 220px; text-align: center; }

.week-bar { margin-bottom: 0; }
.day-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px 14px;
  cursor: pointer;
  transition: all 0.25s;
  border: 2px solid transparent;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  margin-bottom: 14px;
  position: relative;
  overflow: hidden;
}
.day-card:hover { transform: translateY(-3px); box-shadow: 0 6px 18px rgba(0,82,217,0.12); }
.day-card.active {
  border-color: #0052d9;
  background: linear-gradient(135deg, #e6f1ff 0%, #fff 100%);
}
.day-card.today:not(.active) { border-color: #ef4444; }
.day-card.empty { opacity: 0.65; }
.dc-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.dc-name { font-weight: 700; color: #1a1a2e; font-size: 15px; }
.dc-date { font-size: 12px; color: #8c8c8c; margin-bottom: 10px; }
.dc-status { min-height: 22px; margin-bottom: 4px; display: flex; align-items: center; }
.icon-yes { color: #10b981; font-size: 18px; }
.no-plan { font-size: 12px; color: #c0c4cc; }
.dc-summary .dc-dist {
  display: inline-block;
  background: linear-gradient(135deg, #0052d9, #003d9e);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 10px;
}

.detail-card, .phase-card, .sets-card, .notes-card { border: none; border-radius: 14px; }
.detail-card :deep(.el-card__header) {
  padding: 16px 20px; border-bottom: 1px solid #f0f2f5;
}
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title {
  font-size: 16px; font-weight: 600; color: #1a1a2e;
  display: flex; align-items: center; gap: 8px;
}
.title-icon { color: #0052d9; }

.phase-card :deep(.el-card__body) { padding: 20px; }
.phase-head { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.phase-icon { font-size: 20px; }
.phase-name { font-weight: 700; color: #1a1a2e; font-size: 15px; }
.warm .phase-icon { color: #f59e0b; }
.main .phase-icon { color: #ef4444; }
.cool .phase-icon { color: #3b82f6; }
.warm { background: linear-gradient(135deg, #fffbeb, #fff); }
.main { background: linear-gradient(135deg, #fef2f2, #fff); }
.cool { background: linear-gradient(135deg, #eff6ff, #fff); }
.phase-val { display: flex; align-items: baseline; gap: 6px; margin-bottom: 6px; }
.num { font-size: 32px; font-weight: 800; color: #1a1a2e; line-height: 1; }
.unit { font-size: 14px; color: #8c8c8c; font-weight: 500; }
.set-tag { margin-left: 10px; }
.phase-desc { font-size: 12px; color: #8c8c8c; }

.sets-card :deep(.el-card__header) { padding: 14px 18px; border-bottom: 1px solid #f0f2f5; }
.sets-table :deep(.el-table__cell) { padding: 12px 0; }
.num-bold { font-weight: 700; color: #0052d9; }
.note-text { color: #606266; }
.empty-tip { color: #c0c4cc; }

.notes-card { background: #fafcff; border: 1px dashed #bfdbfe !important; }
.notes-head { display: flex; align-items: center; gap: 6px; font-weight: 600; color: #0052d9; margin-bottom: 8px; }
.notes-icon { font-size: 18px; }
.notes-body { margin: 0; line-height: 1.75; color: #606266; }

.empty-area {
  background: #fff;
  border-radius: 14px;
  padding: 60px 20px;
}
</style>
