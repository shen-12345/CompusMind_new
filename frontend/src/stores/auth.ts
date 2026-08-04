import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getMe } from '../api/auth'

export interface UserInfo {
  user_id: number
  username: string
  name: string
  role: string
  department: string
  is_first_login: boolean
}

// 从 localStorage 恢复用户信息（同步，供路由守卫使用）
function loadUser(): UserInfo | null {
  const raw = localStorage.getItem('user_info')
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  const user = ref<UserInfo | null>(loadUser())
  const needChangePassword = ref(localStorage.getItem('need_change_password') === 'true')

  const isLoggedIn = computed(() => !!accessToken.value)

  function saveUser(u: UserInfo) {
    user.value = u
    localStorage.setItem('user_info', JSON.stringify(u))
    needChangePassword.value = u.is_first_login
    localStorage.setItem('need_change_password', u.is_first_login ? 'true' : 'false')
  }

  function clearUser() {
    user.value = null
    needChangePassword.value = false
    localStorage.removeItem('user_info')
    localStorage.removeItem('need_change_password')
  }

  async function login(username: string, password: string) {
    const res = await loginApi(username, password)
    if (res.code !== 0) {
      throw new Error(res.message)
    }
    const data = res.data
    accessToken.value = data.access_token
    refreshToken.value = data.refresh_token
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    saveUser(data.user)
    return data
  }

  function logout() {
    accessToken.value = ''
    refreshToken.value = ''
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    clearUser()
  }

  function markPasswordChanged() {
    if (user.value) {
      user.value.is_first_login = false
      saveUser(user.value)
    }
  }

  async function fetchUser() {
    try {
      const res = await getMe()
      if (res.code === 0) {
        saveUser(res.data)
      }
    } catch {
      logout()
    }
  }

  return {
    accessToken, refreshToken, user, isLoggedIn, needChangePassword,
    login, logout, fetchUser, markPasswordChanged,
  }
})