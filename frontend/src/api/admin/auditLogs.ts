import request from '../request'
import type { ApiResponse } from '../auth'

export interface AuditLogItem {
  log_id: number
  operator_id: number
  operator_name: string
  action: string
  resource_type: string
  resource_id: number | null
  detail: any
  ip_address: string | null
  user_agent: string | null
  created_at: string | null
}

export interface AuditLogListData {
  items: AuditLogItem[]
  total: number
  page: number
  page_size: number
}

export function getAuditLogs(params: {
  page?: number
  page_size?: number
  action?: string
  operator_name?: string
  resource_type?: string
  start_time?: string
  end_time?: string
}): Promise<ApiResponse<AuditLogListData>> {
  return request.get('/admin/audit-logs', { params })
}