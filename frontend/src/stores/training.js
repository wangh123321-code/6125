import { defineStore } from 'pinia'
import request from '@/utils/request'

export const useTrainingStore = defineStore('training', {
  state: () => ({
    trainingPlans: [],
    trainingDataList: [],
    monthlyReports: [],
    currentPlan: null,
    currentReport: null
  }),
  getters: {
    getPlansByAthlete: (state) => (athleteId) => {
      return state.trainingPlans.filter(plan => plan.athleteId === athleteId)
    },
    getDataByAthlete: (state) => (athleteId) => {
      return state.trainingDataList.filter(data => data.athleteId === athleteId)
    }
  },
  actions: {
    async fetchTrainingPlans(params) {
      const res = await request.get('/api/training/plans', { params })
      this.trainingPlans = res.data || []
      return res
    },
    async createTrainingPlan(data) {
      const res = await request.post('/api/training/plans', data)
      this.trainingPlans.push(res.data)
      return res
    },
    async updateTrainingPlan(id, data) {
      const res = await request.put(`/api/training/plans/${id}`, data)
      const index = this.trainingPlans.findIndex(p => p.id === id)
      if (index !== -1) {
        this.trainingPlans[index] = res.data
      }
      return res
    },
    async deleteTrainingPlan(id) {
      await request.delete(`/api/training/plans/${id}`)
      this.trainingPlans = this.trainingPlans.filter(p => p.id !== id)
    },
    async fetchTrainingData(params) {
      const res = await request.get('/api/training/data', { params })
      this.trainingDataList = res.data || []
      return res
    },
    async addTrainingData(data) {
      const res = await request.post('/api/training/data', data)
      this.trainingDataList.push(res.data)
      return res
    },
    async fetchMonthlyReports(params) {
      const res = await request.get('/api/training/reports', { params })
      this.monthlyReports = res.data || []
      return res
    },
    async createMonthlyReport(data) {
      const res = await request.post('/api/training/reports', data)
      this.monthlyReports.push(res.data)
      return res
    },
    async generateReport(id) {
      const res = await request.get(`/api/training/reports/${id}/generate`, { responseType: 'blob' })
      return res
    },
    setCurrentPlan(plan) {
      this.currentPlan = plan
    },
    setCurrentReport(report) {
      this.currentReport = report
    }
  }
})
