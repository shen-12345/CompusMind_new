import request from './request'

export interface LoginResponse {
  code: number
  message: string
  data: {
    access_token: string
    refresh_token: string
    token_type: string
    expires_in: number
    user: {
      user_id: number
      username: string
      name: string
      role: string
      department: string
      is_first_login: boolean
    }
  }
}

export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

export function login(username: string, password: string): Promise<LoginResponse> {
  return request.post('/auth/login', { username, password })
}

export function getMe(): Promise<ApiResponse> {
  return request.get('/auth/me')
}

export function refreshToken(refresh_token: string): Promise<ApiResponse> {
  return request.post('/auth/refresh', { refresh_token })
}

export function changePassword(old_password: string, new_password: string): Promise<ApiResponse> {
  return request.post('/auth/change-password', { old_password, new_password })
}