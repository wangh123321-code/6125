import { defineStore } from 'pinia'
import { getToken, setToken, removeToken, getUserInfo, setUserInfo, removeUserInfo } from '@/utils/auth'
import { login } from '@/utils/request'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: getToken() || '',
    userInfo: getUserInfo() || null
  }),
  getters: {
    role: (state) => state.userInfo?.role || '',
    username: (state) => state.userInfo?.username || state.userInfo?.full_name || '',
    userId: (state) => state.userInfo?.id || '',
    name: (state) => state.userInfo?.full_name || state.userInfo?.username || ''
  },
  actions: {
    async loginAction(loginForm) {
      try {
        const res = await login(loginForm)
        const { access_token, user } = res.data
        this.token = access_token
        this.userInfo = user
        setToken(access_token)
        setUserInfo(user)
        return { data: { token: access_token, userInfo: user } }
      } catch (error) {
        throw error
      }
    },
    async logoutAction() {
      this.token = ''
      this.userInfo = null
      removeToken()
      removeUserInfo()
    },
    setUser(userInfo) {
      this.userInfo = userInfo
      setUserInfo(userInfo)
    }
  }
})
