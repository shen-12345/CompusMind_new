import request from './request'
import type { ApiResponse } from './auth'

export function askQuestion(
  question: string,
  history: { role: string; content: string }[]
): Promise<ApiResponse<{ answer: string; sources: { policy_id: number; title: string }[]; chunks_count: number }>> {
  return request.post('/agent/ask', { question, history })
}

export function reindexEmbeddings(): Promise<ApiResponse<{ indexed: number; total: number }>> {
  return request.post('/agent/reindex')
}