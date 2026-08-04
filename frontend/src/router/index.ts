import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/login/LoginView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/change-password',
      name: 'ChangePassword',
      component: () => import('../views/auth/ChangePasswordView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/',
      component: () => import('../layouts/MainLayout.vue'),
      meta: { requiresAuth: true },
      redirect: '/student/dashboard',
      children: [
        // 首页（按角色跳转）
        {
          path: 'home',
          name: 'Home',
          component: () => import('../views/HomeView.vue'),
        },
        // super_admin 页面
        {
          path: 'admin/users',
          name: 'Users',
          component: () => import('../views/admin/UsersView.vue'),
          meta: { roles: ['super_admin'] },
        },
        {
          path: 'admin/users/import',
          name: 'ImportUsers',
          component: () => import('../views/admin/ImportView.vue'),
          meta: { roles: ['super_admin'] },
        },
        {
          path: 'admin/audit-logs',
          name: 'AuditLogs',
          component: () => import('../views/admin/AuditLogsView.vue'),
          meta: { roles: ['super_admin'] },
        },
        {
          path: 'admin/settings',
          name: 'Settings',
          component: () => import('../views/PlaceholderView.vue'),
          meta: { roles: ['super_admin'] },
        },
        // admin 页面（校级管理员）
        {
          path: 'admin/pending',
          name: 'AdminPending',
          component: () => import('../views/PlaceholderView.vue'),
          meta: { roles: ['admin'] },
        },
        {
          path: 'admin/statistics',
          name: 'AdminStatistics',
          component: () => import('../views/PlaceholderView.vue'),
          meta: { roles: ['admin'] },
        },
        {
          path: 'admin/projects',
          name: 'AdminProjects',
          component: () => import('../views/teacher/PoliciesView.vue'),
          meta: { roles: ['admin'] },
        },
        // teacher 页面（辅导员）
        {
          path: 'teacher/upload',
          name: 'TeacherUpload',
          component: () => import('../views/teacher/UploadView.vue'),
          meta: { roles: ['teacher'] },
        },
        {
          path: 'teacher/pending-review',
          name: 'TeacherReview',
          component: () => import('../views/PlaceholderView.vue'),
          meta: { roles: ['teacher'] },
        },
        {
          path: 'teacher/pending-final',
          name: 'TeacherFinal',
          component: () => import('../views/PlaceholderView.vue'),
          meta: { roles: ['teacher'] },
        },
        {
          path: 'teacher/statistics',
          name: 'TeacherStats',
          component: () => import('../views/PlaceholderView.vue'),
          meta: { roles: ['teacher'] },
        },
        {
          path: 'teacher/policies',
          name: 'TeacherPolicies',
          component: () => import('../views/teacher/PoliciesView.vue'),
          meta: { roles: ['teacher'] },
        },
        // student 页面（学生）
        {
          path: 'student/dashboard',
          name: 'StudentDashboard',
          component: () => import('../views/student/DashboardView.vue'),
          meta: { roles: ['student'] },
        },
        {
          path: 'student/favorites',
          name: 'StudentFavorites',
          component: () => import('../views/PlaceholderView.vue'),
          meta: { roles: ['student'] },
        },
        {
          path: 'student/applications',
          name: 'StudentApplications',
          component: () => import('../views/PlaceholderView.vue'),
          meta: { roles: ['student'] },
        },
        {
          path: 'student/qa',
          name: 'StudentQA',
          component: () => import('../views/PlaceholderView.vue'),
          meta: { roles: ['student'] },
        },
      ],
    },
  ],
})

// 角色默认首页映射
const defaultHome: Record<string, string> = {
  super_admin: '/admin/users',
  admin: '/admin/pending',
  teacher: '/teacher/upload',
  student: '/student/dashboard',
}

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()

  // 未登录 → 跳转登录页
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next('/login')
    return
  }

  // 已登录且是首次登录 → 强制跳转修改密码页
  if (authStore.isLoggedIn && authStore.needChangePassword && to.path !== '/change-password') {
    next('/change-password')
    return
  }

  // 已登录且访问登录页 → 跳转角色首页
  if (to.path === '/login' && authStore.isLoggedIn) {
    next(defaultHome[authStore.user?.role || ''] || '/home')
    return
  }

  // 根路径 / → 跳转角色首页
  if (to.path === '/' && authStore.isLoggedIn) {
    next(defaultHome[authStore.user?.role || ''] || '/home')
    return
  }

  // 角色权限校验
  if (to.meta.roles) {
    const requiredRoles = to.meta.roles as string[]
    if (!requiredRoles.includes(authStore.user?.role || '')) {
      next(defaultHome[authStore.user?.role || ''] || '/home')
      return
    }
  }

  next()
})

export default router