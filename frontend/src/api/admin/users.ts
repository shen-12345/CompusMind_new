import request from '../request'
import type { ApiResponse } from './auth'

export interface UserItem {
  user_id: number
  username: string
  name: string
  role: string
  department: string
  education_level: string | null
  grade: string | null
  admin_scope: string | null
  school_id: string | null
  email: string | null
  is_active: boolean
  is_first_login: boolean
  last_login: string | null
  created_at: string | null
}

export interface UserListData {
  items: UserItem[]
  total: number
  page: number
  page_size: number
}

export function getUsers(params: {
  page?: number
  page_size?: number
  keyword?: string
  role?: string
  is_active?: boolean
}): Promise<ApiResponse<UserListData>> {
  return request.get('/admin/users', { params })
}

export function createUser(data: {
  username: string
  name: string
  role: string
  department: string
  education_level?: string
  grade?: string
  admin_scope?: string
  school_id?: string
  email?: string
}): Promise<ApiResponse<{ user: UserItem; default_password: string }>> {
  return request.post('/admin/users', data)
}

export function updateUser(userId: number, data: {
  name?: string
  department?: string
  education_level?: string
  grade?: string
  admin_scope?: string
  email?: string
}): Promise<ApiResponse<UserItem>> {
  return request.put(`/admin/users/${userId}`, data)
}

export function toggleUserActive(userId: number): Promise<ApiResponse<UserItem>> {
  return request.put(`/admin/users/${userId}/toggle-active`)
}