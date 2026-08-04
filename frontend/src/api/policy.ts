import request from './request'
import type { ApiResponse } from '../auth'

export interface PolicyItem {
  policy_id: number
  title: string
  department: string
  education_level: string
  applicable_grades: string[]
  project_category: string
  status: string
  version: number
  created_by: number
  created_at: string | null
  published_at: string | null
}

export interface PolicyMetadata {
  metadata_id: number
  policy_id: number
  project_name: string
  deadline: string | null
  prerequisites: string[]
  mutually_exclusive: string[]
  material_list: string[]
  review_process: string | null
  contact_info: string | null
  confidence_score: string | null
}

export function uploadPolicy(formData: FormData): Promise<ApiResponse<{
  policy_id: number
  title: string
  status: string
  message: string
  chunks_count: number
}>> {
  return request.post('/policies/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function extractMetadata(policyId: number): Promise<ApiResponse<PolicyMetadata>> {
  return request.post(`/policies/${policyId}/extract`)
}

export function getPolicyList(params: {
  page?: number
  page_size?: number
  status?: string
  department?: string
}): Promise<ApiResponse<{ items: PolicyItem[]; total: number; page: number; page_size: number }>> {
  return request.get('/policies', { params })
}

export function getPolicyDetail(policyId: number): Promise<ApiResponse<{ policy: PolicyItem; metadata: PolicyMetadata | null }>> {
  return request.get(`/policies/${policyId}`)
}

export function publishPolicy(policyId: number, metadata?: Record<string, any>): Promise<ApiResponse<PolicyItem>> {
  return request.post(`/policies/${policyId}/publish`, metadata || {})
}