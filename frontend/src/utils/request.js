import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, removeToken, removeUserInfo } from '@/utils/auth'
import router from '@/router'

const service = axios.create({
  baseURL: '/',
  timeout: 30000
})

service.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

service.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response) {
      const status = error.response.status
      if (status === 401) {
        ElMessage.error('登录已过期，请重新登录')
        removeToken()
        removeUserInfo()
        router.push('/login')
      } else if (status === 403) {
        ElMessage.error('没有权限访问')
      } else if (status === 404) {
        ElMessage.error('请求资源不存在')
      } else if (status >= 500) {
        ElMessage.error('服务器错误，请稍后重试')
      } else {
        const msg = error.response.data?.detail || error.response.data?.message || error.message
        ElMessage.error(msg || '请求失败')
      }
    } else {
      ElMessage.error('网络连接失败，请检查网络')
    }
    return Promise.reject(error)
  }
)

export function login(data) {
  return service.post('/api/auth/login', data)
}

export function logout() {
  return Promise.resolve()
}

export default service
