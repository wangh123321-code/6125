import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/coach',
    component: () => import('@/layouts/CoachLayout.vue'),
    meta: { roles: ['coach', 'headcoach'] },
    children: [
      {
        path: 'dashboard',
        name: 'CoachDashboard',
        component: () => import('@/views/coach/Dashboard.vue'),
        meta: { title: '仪表盘', roles: ['coach', 'headcoach'] }
      },
      {
        path: 'athletes',
        name: 'CoachAthletes',
        component: () => import('@/views/coach/Athletes.vue'),
        meta: { title: '运动员管理', roles: ['coach', 'headcoach'] }
      },
      {
        path: 'training-plan',
        name: 'CoachTrainingPlan',
        component: () => import('@/views/coach/TrainingPlan.vue'),
        meta: { title: '训练计划', roles: ['coach', 'headcoach'] }
      },
      {
        path: 'training-data',
        name: 'CoachTrainingData',
        component: () => import('@/views/coach/TrainingData.vue'),
        meta: { title: '训练数据', roles: ['coach', 'headcoach'] }
      },
      {
        path: 'monthly-report',
        name: 'CoachMonthlyReport',
        component: () => import('@/views/coach/MonthlyReport.vue'),
        meta: { title: '月度报告', roles: ['coach', 'headcoach'] }
      },
      {
        path: 'all-data',
        name: 'HeadCoachAllData',
        component: () => import('@/views/headcoach/AllData.vue'),
        meta: { title: '全部数据', roles: ['headcoach'] }
      }
    ]
  },
  {
    path: '/athlete',
    component: () => import('@/layouts/AthleteLayout.vue'),
    meta: { roles: ['athlete'] },
    children: [
      {
        path: 'my-plan',
        name: 'AthleteMyPlan',
        component: () => import('@/views/athlete/MyPlan.vue'),
        meta: { title: '我的计划', roles: ['athlete'] }
      },
      {
        path: 'my-data',
        name: 'AthleteMyData',
        component: () => import('@/views/athlete/MyData.vue'),
        meta: { title: '我的数据', roles: ['athlete'] }
      },
      {
        path: 'my-report',
        name: 'AthleteMyReport',
        component: () => import('@/views/athlete/MyReport.vue'),
        meta: { title: '我的报告', roles: ['athlete'] }
      }
    ]
  },
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const token = userStore.token

  if (to.path === '/login') {
    if (token) {
      if (userStore.role === 'athlete') {
        next('/athlete/my-plan')
      } else {
        next('/coach/dashboard')
      }
    } else {
      next()
    }
  } else {
    if (!token) {
      next('/login')
    } else {
      if (to.meta.roles && !to.meta.roles.includes(userStore.role)) {
        if (userStore.role === 'athlete') {
          next('/athlete/my-plan')
        } else {
          next('/coach/dashboard')
        }
      } else {
        next()
      }
    }
  }
})

export default router
