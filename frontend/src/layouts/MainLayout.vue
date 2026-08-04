<template>
  <div class="layout">
    <!-- 侧边栏 -->
    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapse"
      class="sidebar"
      background-color="#1a1a2e"
      text-color="#b0b0c0"
      active-text-color="#fff"
      router
    >
      <div class="sidebar-header">
        <span v-if="!isCollapse" class="sidebar-title">校事通</span>
        <span v-else class="sidebar-title-mini">校</span>
      </div>

      <template v-for="item in menuItems" :key="item.path">
        <el-menu-item v-if="!item.children" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.label }}</template>
        </el-menu-item>
        <el-sub-menu v-else :index="item.label">
          <template #title>
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
          </template>
          <el-menu-item v-for="child in item.children" :key="child.path" :index="child.path">
            {{ child.label }}
          </el-menu-item>
        </el-sub-menu>
      </template>
    </el-menu>

    <!-- 主内容区 -->
    <div class="main-area">
      <!-- 顶部导航 -->
      <header class="topbar">
        <div class="topbar-left">
          <el-button link @click="isCollapse = !isCollapse" style="font-size: 18px; color: #666;">
            {{ isCollapse ? '☰' : '✕' }}
          </el-button>
        </div>
        <div class="topbar-right">
          <el-badge :value="0" :hidden="true" class="notification-badge">
            <el-icon size="20" style="color: #666; cursor: pointer;"><Bell /></el-icon>
          </el-badge>
          <el-dropdown trigger="click">
            <span class="user-info">
              <el-avatar :size="32" style="background: #409eff;">
                {{ userName?.charAt(0) || '?' }}
              </el-avatar>
              <span class="user-name">{{ userName || '未知' }}</span>
              <span class="user-role-tag">{{ roleLabel }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="content">
        <router-view />
      </main>
    </div>

    <!-- 智能问答悬浮按钮 -->
    <AgentDialog />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { Bell } from '@element-plus/icons-vue'
import AgentDialog from '../components/AgentDialog.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const isCollapse = ref(false)

const userName = computed(() => authStore.user?.name)
const userRole = computed(() => authStore.user?.role || '')

const roleLabel = computed(() => {
  const map: Record<string, string> = {
    super_admin: '超级管理员',
    admin: '校级管理员',
    teacher: '辅导员',
    student: '学生',
  }
  return map[userRole.value] || userRole.value
})

const activeMenu = computed(() => route.path)

const menuItems = computed(() => {
  const role = userRole.value
  const all = [
    // super_admin 菜单
    {
      role: 'super_admin',
      items: [
        { path: '/admin/users', label: '用户管理', icon: 'User' },
        { path: '/admin/users/import', label: '批量导入', icon: 'Upload' },
        { path: '/admin/audit-logs', label: '审计日志', icon: 'Document' },
        { path: '/admin/settings', label: '系统配置', icon: 'Setting' },
      ],
    },
    // admin 菜单（校级管理员）
    {
      role: 'admin',
      items: [
        { path: '/admin/pending', label: '待审批', icon: 'Clock' },
        { path: '/admin/statistics', label: '全校统计', icon: 'DataAnalysis' },
        { path: '/admin/projects', label: '政策管理', icon: 'Folder' },
      ],
    },
    // teacher 菜单（辅导员）
    {
      role: 'teacher',
      items: [
        { path: '/teacher/upload', label: '上传政策', icon: 'Upload' },
        { path: '/teacher/pending-review', label: '待初审', icon: 'Edit' },
        { path: '/teacher/pending-final', label: '待终核', icon: 'Finished' },
        { path: '/teacher/statistics', label: '数据统计', icon: 'DataAnalysis' },
        { path: '/teacher/policies', label: '政策管理', icon: 'Folder' },
      ],
    },
    // student 菜单（学生）
    {
      role: 'student',
      items: [
        { path: '/student/dashboard', label: '信息看板', icon: 'HomeFilled' },
        { path: '/student/favorites', label: '我的关注', icon: 'Star' },
        { path: '/student/applications', label: '我的申请', icon: 'List' },
        { path: '/student/qa', label: '智能问答', icon: 'ChatDotSquare' },
      ],
    },
  ]
  const found = all.find(m => m.role === role)
  return found ? found.items : []
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 220px;
  min-height: 100vh;
  border-right: none;
  overflow-y: auto;
  transition: width 0.3s;
}

.sidebar:not(.el-menu--collapse) {
  width: 220px;
}

.el-menu--collapse {
  width: 64px;
}

.sidebar-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-title {
  color: #fff;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 2px;
}

.sidebar-title-mini {
  color: #fff;
  font-size: 18px;
  font-weight: 700;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f5f7fb;
}

.topbar {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
}

.user-info:hover {
  background: #f0f0f0;
}

.user-name {
  font-size: 14px;
  color: #333;
}

.user-role-tag {
  font-size: 12px;
  color: #999;
  background: #f0f0f0;
  padding: 2px 8px;
  border-radius: 4px;
}

.notification-badge {
  line-height: 1;
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}
</style>