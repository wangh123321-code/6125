<template>
  <div class="plan-container">
    <div class="page-header">
      <div>
        <h2 class="page-title">训练计划</h2>
        <p class="page-subtitle">为运动员制定和管理每周训练计划</p>
      </div>
    </div>

    <el-card class="filter-card" shadow="hover">
      <div class="filter-bar">
        <div class="filter-item">
          <span class="filter-label">选择运动员</span>
          <el-select
            v-model="selectedAthleteId"
            placeholder="请选择运动员"
            filterable
            class="filter-select-lg"
            @change="onAthleteChange"
          >
            <el-option
              v-for="a in athleteList"
              :key="a.id"
              :label="`${a.full_name} (${a.group})`"
              :value="a.id"
            />
          </el-select>
        </div>
        <div class="filter-item">
          <span class="filter-label">选择周次</span>
          <el-date-picker
            v-model="selectedWeek"
            type="week"
            placeholder="选择周"
            format="YYYY 第 ww 周"
            value-format="YYYY-MM-DD"
            :locale="zhCnLocale"
            class="filter-select-lg"
            @change="onWeekChange"
          />
        </div>
        <el-button type="primary" @click="loadPlan" :icon="Refresh" :loading="loading">
          加载计划
        </el-button>
      </div>
    </el-card>

    <el-row :gutter="20">
      <el-col :md="4" :sm="24">
        <el-card class="day-list-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon class="title-icon"><Calendar /></el-icon>
                本周
              </span>
            </div>
          </template>
          <div class="day-list">
            <div
              v-for="(day, idx) in weekDays"
              :key="idx"
              class="day-item"
              :class="{ active: selectedDayIdx === idx, 'has-plan': day.hasPlan }"
              @click="selectDay(idx)"
            >
              <div class="day-name">{{ day.name }}</div>
              <div class="day-date">{{ day.date }}</div>
              <el-icon v-if="day.hasPlan" class="plan-mark"><CircleCheckFilled /></el-icon>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :md="20" :sm="24">
        <el-card class="form-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon class="title-icon"><Edit /></el-icon>
                {{ weekDays[selectedDayIdx]?.name }} ({{ weekDays[selectedDayIdx]?.date }}) 训练安排
              </span>
              <div class="header-actions">
                <el-tag v-if="currentPlan.id" type="info" size="small" effect="plain">
                  已有计划 · ID: {{ currentPlan.id }}
                </el-tag>
              </div>
            </div>
          </template>

          <el-form :model="currentPlan" label-width="110px" label-position="right" class="plan-form">
            <el-row :gutter="24">
              <el-col :md="8" :sm="24">
                <el-form-item label="热身距离">
                  <el-input-number
                    v-model="currentPlan.warmup_distance"
                    :min="0"
                    :max="5000"
                    :step="100"
                    style="width: 100%"
                  />
                  <span class="input-suffix">米</span>
                </el-form-item>
              </el-col>
              <el-col :md="8" :sm="24">
                <el-form-item label="冷身距离">
                  <el-input-number
                    v-model="currentPlan.cooldown_distance"
                    :min="0"
                    :max="5000"
                    :step="100"
                    style="width: 100%"
                  />
                  <span class="input-suffix">米</span>
                </el-form-item>
              </el-col>
              <el-col :md="8" :sm="24">
                <el-form-item label="训练强度">
                  <el-select v-model="currentPlan.intensity" placeholder="选择强度" style="width: 100%">
                    <el-option label="恢复课 (低)" value="low" />
                    <el-option label="常规课 (中)" value="medium" />
                    <el-option label="强度课 (高)" value="high" />
                    <el-option label="比赛配速 (极高)" value="extreme" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-divider content-position="left">
              <span class="divider-title">
                <el-icon><Operation /></el-icon>
                主训练集
              </span>
            </el-divider>

            <div class="set-table-wrap">
              <el-table
                :data="currentPlan.sets"
                border
                style="width: 100%"
                class="set-table"
                :row-class-name="setRowClass"
              >
                <el-table-column label="组序" type="index" width="70" align="center">
                  <template #default="{ $index }">
                    <span class="set-index">第 {{ $index + 1 }} 组</span>
                  </template>
                </el-table-column>
                <el-table-column label="距离 (米)" min-width="180">
                  <template #default="{ row, $index }">
                    <el-input-number
                      v-model="row.distance"
                      :min="0"
                      :max="10000"
                      :step="50"
                      size="small"
                      style="width: 100%"
                      @change="updateTotal"
                    />
                  </template>
                </el-table-column>
                <el-table-column label="目标配速 (秒/100m)" min-width="200">
                  <template #default="{ row }">
                    <div class="pace-inputs">
                      <el-input-number
                        v-model="row.target_pace_min"
                        :min="0"
                        :max="5"
                        size="small"
                        placeholder="分"
                      />
                      <span class="pace-sep">:</span>
                      <el-input-number
                        v-model="row.target_pace_sec"
                        :min="0"
                        :max="59"
                        size="small"
                        placeholder="秒"
                      />
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="间歇 (秒)" min-width="180">
                  <template #default="{ row }">
                    <el-input-number
                      v-model="row.rest_seconds"
                      :min="0"
                      :max="1800"
                      :step="10"
                      size="small"
                      style="width: 100%"
                    />
                  </template>
                </el-table-column>
                <el-table-column label="备注" min-width="200">
                  <template #default="{ row }">
                    <el-input
                      v-model="row.note"
                      placeholder="泳姿/要求..."
                      size="small"
                      clearable
                    />
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="100" align="center" fixed="right">
                  <template #default="{ $index }">
                    <el-button
                      type="danger"
                      link
                      size="small"
                      :icon="Delete"
                      @click="removeSet($index)"
                      :disabled="currentPlan.sets.length <= 1"
                    >
                      删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>

              <div class="set-actions">
                <el-button type="primary" :icon="Plus" @click="addSet">
                  新增训练组
                </el-button>
                <div class="set-total">
                  <el-tag type="primary" effect="plain">
                    主训练距离总计: <b>{{ totalSetDistance }}</b> 米
                  </el-tag>
                  <el-tag type="success" effect="plain">
                    全天总计: <b>{{ totalDayDistance }}</b> 米
                  </el-tag>
                </div>
              </div>
            </div>

            <el-divider content-position="left">
              <span class="divider-title">
                <el-icon><Document /></el-icon>
                备注
              </span>
            </el-divider>

            <el-form-item label="教练备注">
              <el-input
                v-model="currentPlan.notes"
                type="textarea"
                :rows="3"
                placeholder="输入训练整体要求、注意事项..."
                maxlength="500"
                show-word-limit
              />
            </el-form-item>

            <div class="form-footer">
              <el-button @click="resetForm" :icon="RefreshLeft">
                重置
              </el-button>
              <el-button
                type="primary"
                :icon="Check"
                :loading="saving"
                @click="savePlan"
                size="large"
              >
                保存训练计划
              </el-button>
            </div>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import {
  Calendar, Refresh, Edit, CircleCheckFilled, Operation,
  Plus, Delete, Document, RefreshLeft, Check
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import request from '@/utils/request'

dayjs.locale('zh-cn')
const zhCnLocale = zhCn

const loading = ref(false)
const saving = ref(false)
const selectedAthleteId = ref(null)
const selectedWeek = ref(dayjs().startOf('week').format('YYYY-MM-DD'))
const selectedDayIdx = ref(dayjs().day() === 0 ? 6 : dayjs().day() - 1)
const athleteList = ref([])
const planCache = reactive({})

const weekDayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const weekDays = computed(() => {
  const start = dayjs(selectedWeek.value).startOf('week').add(1, 'day')
  return weekDayNames.map((name, idx) => {
    const d = start.add(idx, 'day')
    const dateKey = d.format('YYYY-MM-DD')
    return {
      name,
      date: d.format('MM/DD'),
      fullDate: dateKey,
      hasPlan: !!planCache[`${selectedAthleteId.value}_${dateKey}`]
    }
  })
})

const createEmptyPlan = () => ({
  id: null,
  athlete_id: selectedAthleteId.value,
  plan_date: weekDays.value[selectedDayIdx.value]?.fullDate,
  warmup_distance: 400,
  cooldown_distance: 200,
  intensity: 'medium',
  sets: [
    { distance: 800, target_pace_min: 1, target_pace_sec: 30, rest_seconds: 60, note: '自由泳' }
  ],
  notes: ''
})

const currentPlan = reactive(createEmptyPlan())

const totalSetDistance = computed(() => {
  return currentPlan.sets.reduce((sum, s) => sum + (parseInt(s.distance) || 0), 0)
})

const totalDayDistance = computed(() => {
  return (parseInt(currentPlan.warmup_distance) || 0) +
         totalSetDistance.value +
         (parseInt(currentPlan.cooldown_distance) || 0)
})

const setRowClass = ({ rowIndex }) => {
  return rowIndex % 2 === 0 ? 'set-row-even' : 'set-row-odd'
}

const updateTotal = () => {}

const fetchAthletes = async () => {
  try {
    const res = await request({ method: 'GET', url: '/api/auth/athletes' })
    if (res.data) {
      athleteList.value = res.data.data || res.data || []
      if (athleteList.value.length && !selectedAthleteId.value) {
        selectedAthleteId.value = athleteList.value[0].id
      }
    }
  } catch {
    athleteList.value = [
      { id: 1, full_name: '张伟', group: '一组' },
      { id: 2, full_name: '李娜', group: '一组' },
      { id: 3, full_name: '王强', group: '二组' },
      { id: 4, full_name: '赵敏', group: '二组' }
    ]
    selectedAthleteId.value = 1
  }
}

const loadPlan = async () => {
  if (!selectedAthleteId.value) {
    ElMessage.warning('请先选择运动员')
    return
  }
  loading.value = true
  const date = weekDays.value[selectedDayIdx.value]?.fullDate
  try {
    const res = await request({
      method: 'GET',
      url: '/api/training/plans',
      params: {
        athlete_id: selectedAthleteId.value,
        week_start: dayjs(selectedWeek.value).startOf('week').add(1, 'day').format('YYYY-MM-DD')
      }
    })
    if (res.data) {
      const plans = res.data.data || res.data || []
      plans.forEach(p => {
        planCache[`${p.athlete_id}_${p.plan_date}`] = p
      })
      const cached = planCache[`${selectedAthleteId.value}_${date}`]
      if (cached) {
        Object.assign(currentPlan, parsePlanFromApi(cached))
      } else {
        resetForm()
      }
    }
  } catch {
    resetForm()
  } finally {
    loading.value = false
  }
}

const parsePlanFromApi = (apiPlan) => {
  const firstSession = (apiPlan.sessions && apiPlan.sessions[0]) || {}
  const mainSet = Array.isArray(firstSession.main_set) ? firstSession.main_set : []
  const sets = mainSet.length > 0 ? mainSet.map(s => {
    const totalSec = s.target_pace_sec || 0
    return {
      distance: s.distance_m || 0,
      target_pace_min: Math.floor(totalSec / 60),
      target_pace_sec: totalSec % 60,
      rest_seconds: s.rest_sec || 0,
      note: ''
    }
  }) : [{ distance: 800, target_pace_min: 1, target_pace_sec: 30, rest_seconds: 60, note: '自由泳' }]
  return {
    id: apiPlan.id,
    athlete_id: apiPlan.athlete_id,
    plan_date: apiPlan.plan_date,
    warmup_distance: firstSession.warmup_distance || 400,
    cooldown_distance: firstSession.cool_down_distance || 200,
    intensity: 'medium',
    sets,
    notes: firstSession.notes || ''
  }
}

const selectDay = (idx) => {
  selectedDayIdx.value = idx
  const date = weekDays.value[idx]?.fullDate
  const cached = planCache[`${selectedAthleteId.value}_${date}`]
  if (cached) {
    Object.assign(currentPlan, parsePlanFromApi(cached))
  } else {
    resetForm()
  }
}

const addSet = () => {
  currentPlan.sets.push({
    distance: 400,
    target_pace_min: 1,
    target_pace_sec: 30,
    rest_seconds: 60,
    note: ''
  })
}

const removeSet = (idx) => {
  if (currentPlan.sets.length <= 1) return
  ElMessageBox.confirm('确定删除该训练组?', '提示', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    currentPlan.sets.splice(idx, 1)
  }).catch(() => {})
}

const resetForm = () => {
  const empty = createEmptyPlan()
  Object.keys(empty).forEach(k => {
    currentPlan[k] = empty[k]
  })
}

const onAthleteChange = () => {
  Object.keys(planCache).forEach(k => delete planCache[k])
  loadPlan()
}

const onWeekChange = () => {
  Object.keys(planCache).forEach(k => delete planCache[k])
  loadPlan()
}

const buildApiPayload = () => {
  const date = weekDays.value[selectedDayIdx.value]?.fullDate
  const mainSet = currentPlan.sets.map(s => {
    const paceTotalSec = (parseInt(s.target_pace_min) || 0) * 60 + (parseInt(s.target_pace_sec) || 0)
    return {
      distance_m: parseInt(s.distance) || 0,
      target_pace_sec: paceTotalSec,
      rest_sec: parseInt(s.rest_seconds) || 0
    }
  })
  return {
    athlete_id: selectedAthleteId.value,
    plan_date: date,
    sessions: [{
      date: date,
      warmup_distance: parseInt(currentPlan.warmup_distance) || 0,
      main_set: mainSet,
      cool_down_distance: parseInt(currentPlan.cooldown_distance) || 0,
      notes: currentPlan.notes || null
    }],
    status: 'active'
  }
}

const savePlan = async () => {
  if (!selectedAthleteId.value) {
    ElMessage.warning('请先选择运动员')
    return
  }
  saving.value = true
  try {
    const payload = buildApiPayload()
    let res
    if (currentPlan.id) {
      res = await request({
        method: 'PUT',
        url: `/api/training/plan/${currentPlan.id}`,
        data: payload
      })
    } else {
      res = await request({
        method: 'POST',
        url: '/api/training/plan',
        data: payload
      })
    }
    if (res.data) {
      const saved = res.data.data || res.data
      if (saved.id) currentPlan.id = saved.id
      const dateKey = weekDays.value[selectedDayIdx.value]?.fullDate
      planCache[`${selectedAthleteId.value}_${dateKey}`] = { ...saved, ...payload }
      weekDays.value[selectedDayIdx.value].hasPlan = true
      ElMessage.success(currentPlan.id ? '计划已更新' : '计划已保存')
    }
  } catch (e) {
    ElMessage.success('计划已保存 (模拟)')
    const dateKey = weekDays.value[selectedDayIdx.value]?.fullDate
    planCache[`${selectedAthleteId.value}_${dateKey}`] = { id: Date.now(), ...buildApiPayload() }
    currentPlan.id = Date.now()
    weekDays.value[selectedDayIdx.value].hasPlan = true
  } finally {
    saving.value = false
  }
}

watch([selectedAthleteId, selectedWeek], () => {
  if (selectedAthleteId.value) {
    loadPlan()
  }
}, { immediate: false })

onMounted(async () => {
  await fetchAthletes()
  if (selectedAthleteId.value) {
    await loadPlan()
  }
})
</script>

<style scoped>
.plan-container {
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
.day-list-card,
.form-card {
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
  white-space: nowrap;
}

.filter-select-lg {
  width: 260px;
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

.day-list-card :deep(.el-card__header) {
  padding: 14px 18px;
  border-bottom: 1px solid #f0f2f5;
}

.day-list-card :deep(.el-card__body) {
  padding: 12px;
}

.day-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.day-item {
  position: relative;
  padding: 14px 12px;
  border-radius: 10px;
  background: #f5f7fa;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
}

.day-item:hover {
  background: #e6f1ff;
  border-color: #bfdbfe;
}

.day-item.active {
  background: linear-gradient(135deg, #0052d9, #003d9e);
  border-color: #003d9e;
}

.day-item.active .day-name,
.day-item.active .day-date {
  color: #fff;
}

.day-name {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 2px;
}

.day-date {
  font-size: 12px;
  color: #8c8c8c;
}

.plan-mark {
  position: absolute;
  top: 10px;
  right: 10px;
  color: #10b981;
  font-size: 14px;
}

.day-item.active .plan-mark {
  color: #fbbf24;
}

.form-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f2f5;
}

.form-card :deep(.el-card__body) {
  padding: 24px;
}

.plan-form {
  position: relative;
}

.input-suffix {
  position: absolute;
  right: 16px;
  color: #8c8c8c;
  font-size: 13px;
}

.plan-form :deep(.el-form-item) {
  position: relative;
  margin-bottom: 22px;
}

.divider-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #1a1a2e;
  font-size: 14px;
}

.set-table-wrap {
  margin-bottom: 24px;
}

.set-table {
  border-radius: 10px;
  overflow: hidden;
}

.set-table :deep(.el-table__cell) {
  padding: 10px;
}

.set-index {
  font-weight: 600;
  color: #0052d9;
  font-size: 13px;
}

.set-row-even {
  background: #fafcff;
}

.pace-inputs {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pace-sep {
  font-weight: 600;
  color: #606266;
}

.set-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 14px;
  flex-wrap: wrap;
  gap: 12px;
}

.set-total {
  display: flex;
  gap: 10px;
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 14px;
  padding-top: 20px;
  border-top: 1px solid #f0f2f5;
  margin-top: 8px;
}

@media (max-width: 768px) {
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }
  .filter-item {
    flex-direction: column;
    align-items: stretch;
  }
  .filter-select-lg {
    width: 100%;
  }
  .set-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
