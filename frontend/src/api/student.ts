import request from './request'
import type { ApiResponse } from './auth'

export function getStudentPolicies(params: {
  page?: number
  page_size?: number
}): Promise<ApiResponse<{ items: any[]; total: number }>> {
  return request.get('/student/policies', { params })
}