import request from './request'
import type { ApiResponse } from './auth'

export function withdrawPolicy(policyId: number): Promise<ApiResponse<any>> {
  return request.post(`/policies/${policyId}/withdraw`)
}

export function deletePolicy(policyId: number): Promise<ApiResponse<any>> {
  return request.delete(`/policies/${policyId}`)
}