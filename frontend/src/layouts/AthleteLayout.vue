<template>
  <el-container class="layout-container">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="layout-aside">
      <div class="logo">
        <img src="/vite.svg" alt="logo" />
        <span v-show="!isCollapse" class="logo-text">训练管理</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        class="layout-menu"
        router
        background-color="#0052d9"
        text-color="#ffffff"
        active-text-color="#ffd04b"
      >
        <el-menu-item index="/athlete/my-plan">
          <el-icon><Calendar /></el-icon>
          <template #title>我的计划</template>
        </el-menu-item>
        <el-menu-item index="/athlete/my-data">
          <el-icon><PieChart /></el-icon>
          <template #title>我的数据</template>
        </el-menu-item>
        <el-menu-item index="/athlete/my-report">
          <el-icon><Document /></el-icon>
          <template #title>我的报告</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon class="collapse-icon" @click="toggleCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/" class="layout-breadcrumb">
            <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path">{{ item.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" class="user-avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <span class="user-name">{{ userStore.userInfo?.name || userStore.username }}</span>
              <span class="user-role-badge">运动员</span>
              <el-icon class="arrow-icon"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人中心
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="layout-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import {
  Calendar, PieChart, Document,
  Fold, Expand, ArrowDown, SwitchButton, User
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isCollapse = ref(false)
const activeMenu = computed(() => route.path)

const breadcrumbs = computed(() => {
  const crumbs = [{ title: '首页', path: '/athlete/my-plan' }]
  if (route.meta.title) {
    crumbs.push({ title: route.meta.title, path: route.path })
  }
  return crumbs
})

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const handleCommand = async (command) => {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      await userStore.logoutAction()
      ElMessage.success('退出成功')
      router.push('/login')
    } catch {}
  } else if (command === 'profile') {
    ElMessage.info('个人中心功能开发中')
  }
}
</script>

<style scoped>
.layout-container {
  width: 100%;
  height: 100vh;
}

.layout-aside {
  background: #0052d9;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: #003d9e;
  overflow: hidden;
}

.logo img {
  width: 32px;
  height: 32px;
}

.logo-text {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}

.layout-menu {
  border-right: none;
  height: calc(100vh - 60px);
}

.layout-menu :deep(.el-menu-item) {
  height: 50px;
  line-height: 50px;
}

.layout-menu :deep(.el-menu-item.is-active) {
  background: #003d9e;
}

.layout-header {
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-icon {
  font-size: 20px;
  cursor: pointer;
  color: #606266;
  transition: color 0.2s;
}

.collapse-icon:hover {
  color: #0052d9;
}

.layout-breadcrumb {
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 0 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.user-info:hover {
  background: #f5f7fa;
}

.user-avatar {
  background: #e6f1ff;
  color: #0052d9;
}

.user-name {
  color: #303133;
  font-size: 14px;
}

.user-role-badge {
  font-size: 12px;
  padding: 2px 6px;
  background: #e6f1ff;
  color: #0052d9;
  border-radius: 4px;
}

.arrow-icon {
  font-size: 12px;
  color: #909399;
}

.layout-main {
  background: #f0f2f5;
  padding: 20px;
  overflow: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
