<template>
  <div class="login-container">
    <div class="login-bg">
      <div class="bg-decoration bg-decoration-1"></div>
      <div class="bg-decoration bg-decoration-2"></div>
      <div class="bg-decoration bg-decoration-3"></div>
    </div>
    <div class="login-wrapper">
      <div class="login-left">
        <div class="brand-section">
          <div class="brand-logo">
            <el-icon :size="48"><SwimLane /></el-icon>
          </div>
          <h1 class="brand-title">游泳训练管理系统</h1>
          <p class="brand-subtitle">Swimming Training Management Platform</p>
        </div>
        <div class="features-section">
          <div class="feature-item">
            <el-icon :size="24"><DataAnalysis /></el-icon>
            <span>科学数据分析</span>
          </div>
          <div class="feature-item">
            <el-icon :size="24"><Calendar /></el-icon>
            <span>智能训练计划</span>
          </div>
          <div class="feature-item">
            <el-icon :size="24"><Document /></el-icon>
            <span>专业月度报告</span>
          </div>
        </div>
      </div>
      <div class="login-right">
        <el-card class="login-card" shadow="hover">
          <div class="card-header">
            <h2 class="card-title">欢迎登录</h2>
            <p class="card-desc">请选择角色并输入账号密码</p>
          </div>
          <el-tabs v-model="activeRole" class="role-tabs" @tab-change="handleRoleChange">
            <el-tab-pane label="运动员" name="athlete">
              <el-icon><User /></el-icon>
            </el-tab-pane>
            <el-tab-pane label="教练" name="coach">
              <el-icon><Avatar /></el-icon>
            </el-tab-pane>
            <el-tab-pane label="总教练" name="headcoach">
              <el-icon><Management /></el-icon>
            </el-tab-pane>
          </el-tabs>
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            class="login-form"
            @keyup.enter="handleSubmit"
          >
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="请输入用户名"
                size="large"
                :prefix-icon="User"
                clearable
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                :prefix-icon="Lock"
                show-password
                @keyup.enter="handleSubmit"
              />
            </el-form-item>
            <el-form-item>
              <el-checkbox v-model="rememberMe">记住我</el-checkbox>
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="submit-btn"
                :loading="loading"
                @click="handleSubmit"
              >
                {{ loading ? '登录中...' : '登 录' }}
              </el-button>
            </el-form-item>
          </el-form>
          <el-alert
            :title="defaultAccountTip"
            type="info"
            :closable="false"
            show-icon
            class="tip-alert"
          />
        </el-card>
      </div>
    </div>
    <div class="login-footer">
      <span>© 2024 游泳训练管理系统 | 专业 · 高效 · 科学</span>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, SwimLane, DataAnalysis, Calendar, Document, Avatar, Management } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref(null)
const activeRole = ref('athlete')
const loading = ref(false)
const rememberMe = ref(false)

const defaultAccounts = {
  athlete: { username: 'athlete001', password: '123456', tip: '运动员测试账号：athlete001 / 123456' },
  coach: { username: 'coach001', password: '123456', tip: '教练测试账号：coach001 / 123456' },
  headcoach: { username: 'headcoach', password: '123456', tip: '总教练测试账号：headcoach / 123456' }
}

const loginForm = reactive({
  username: 'athlete001',
  password: '123456',
  role: 'athlete'
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ]
}

const defaultAccountTip = computed(() => defaultAccounts[activeRole.value].tip)

const handleRoleChange = (role) => {
  loginForm.role = role
  loginForm.username = defaultAccounts[role].username
  loginForm.password = defaultAccounts[role].password
}

const handleSubmit = async () => {
  if (!loginFormRef.value) return
  try {
    await loginFormRef.value.validate()
    loading.value = true
    const res = await userStore.loginAction({
      username: loginForm.username,
      password: loginForm.password,
    })
    ElMessage.success('登录成功')
    const role = userStore.role
    if (role === 'athlete') {
      router.push('/athlete/my-plan')
    } else {
      router.push('/coach/dashboard')
    }
  } catch (error) {
    if (error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(135deg, #001f5c 0%, #003d9e 50%, #0052d9 100%);
}

.login-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.bg-decoration {
  position: absolute;
  border-radius: 50%;
  opacity: 0.1;
  background: radial-gradient(circle, #ffffff 0%, transparent 70%);
}

.bg-decoration-1 {
  width: 600px;
  height: 600px;
  top: -200px;
  right: -100px;
  animation: float 8s ease-in-out infinite;
}

.bg-decoration-2 {
  width: 400px;
  height: 400px;
  bottom: -100px;
  left: -50px;
  animation: float 10s ease-in-out infinite reverse;
}

.bg-decoration-3 {
  width: 300px;
  height: 300px;
  top: 40%;
  left: 30%;
  animation: float 12s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(30px, -30px) scale(1.1); }
}

.login-wrapper {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 80px;
  padding: 0 80px;
}

.login-left {
  flex: 1;
  max-width: 500px;
  color: #fff;
}

.brand-section {
  margin-bottom: 60px;
}

.brand-logo {
  width: 80px;
  height: 80px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  margin-bottom: 24px;
}

.brand-title {
  font-size: 42px;
  font-weight: 700;
  margin: 0 0 12px 0;
  letter-spacing: 2px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.brand-subtitle {
  font-size: 18px;
  opacity: 0.8;
  margin: 0;
  letter-spacing: 1px;
}

.features-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 16px 24px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  font-size: 16px;
  transition: all 0.3s;
}

.feature-item:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateX(8px);
}

.login-right {
  width: 440px;
  flex-shrink: 0;
}

.login-card {
  border-radius: 20px;
  border: none;
  overflow: hidden;
}

.login-card :deep(.el-card__body) {
  padding: 40px 36px;
}

.card-header {
  text-align: center;
  margin-bottom: 32px;
}

.card-title {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 8px 0;
}

.card-desc {
  font-size: 14px;
  color: #8c8c8c;
  margin: 0;
}

.role-tabs {
  margin-bottom: 28px;
}

.role-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 2px;
  background-color: #eef1f6;
}

.role-tabs :deep(.el-tabs__item) {
  height: 48px;
  line-height: 48px;
  font-size: 15px;
  font-weight: 500;
}

.role-tabs :deep(.el-tabs__item.is-active) {
  color: #0052d9;
}

.role-tabs :deep(.el-tabs__active-bar) {
  background-color: #0052d9;
  height: 3px;
}

.role-tabs :deep(.el-tabs__item .el-icon) {
  margin-right: 6px;
}

.login-form :deep(.el-input__wrapper) {
  border-radius: 10px;
  padding: 4px 12px;
  box-shadow: 0 0 0 1px #e0e6ed inset;
  transition: all 0.3s;
}

.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #0052d9 inset;
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #0052d9 inset;
}

.submit-btn {
  width: 100%;
  height: 48px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 4px;
  background: linear-gradient(135deg, #003d9e 0%, #0052d9 100%);
  border: none;
  transition: all 0.3s;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 82, 217, 0.4);
}

.tip-alert {
  margin-top: 20px;
  border-radius: 10px;
}

.login-footer {
  position: absolute;
  bottom: 24px;
  left: 0;
  right: 0;
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
  z-index: 1;
}
</style>
