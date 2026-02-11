/**
 * 卡片管理 API
 */

import { get, post, put } from '@/utils/request'
import type {
  Card,
  CardListParams,
  CardStats,
  CardTransferRequest,
  CardRemarkRequest,
  CardExportParams,
  CardBatchQueryRequest,
  CardBatchRenewRequest,
  CardBatchSuspendRequest
} from '@/types/card'
import type { PaginationResponse } from '@/types/common'

export const cardApi = {
  // 获取卡片列表
  getList(params: CardListParams): Promise<PaginationResponse<Card>> {
    return get<PaginationResponse<Card>>('/cards', { params })
  },

  // 获取卡片详情
  getDetail(id: number): Promise<Card> {
    return get<Card>(`/cards/${id}`)
  },

  // 快速搜索（后6位）
  search(keyword: string, limit = 10): Promise<Card[]> {
    return get<Card[]>('/cards/search', { params: { keyword, limit } })
  },

  // 获取卡片统计
  getStats(): Promise<CardStats> {
    return get<CardStats>('/cards/stats')
  },

  // 批量查询
  batchQuery(data: CardBatchQueryRequest): Promise<{ found: Card[]; not_found: string[] }> {
    return post<{ found: Card[]; not_found: string[] }>('/cards/batch-query', data.iccids)
  },

  // 单卡划拨
  transfer(id: number, targetUserId: number, remark?: string): Promise<void> {
    return post<void>(`/cards/${id}/transfer`, { target_user_id: targetUserId, remark })
  },

  // 批量划拨
  batchTransfer(data: CardTransferRequest): Promise<{ success: number; failed: number }> {
    return post<{ success: number; failed: number }>('/cards/batch/transfer', data)
  },

  // 通过ICCID批量划拨
  batchTransferByIccids(data: { iccids: string[]; to_user_id: number; remark?: string }): Promise<any> {
    return post('/cards/batch/transfer-by-iccids', data)
  },

  // 单卡备注
  updateRemark(id: number, remark: string): Promise<void> {
    return put<void>(`/cards/${id}/remark`, { remark })
  },

  // 批量备注
  batchRemark(data: CardRemarkRequest): Promise<{ success: number; failed: number }> {
    return put<{ success: number; failed: number }>('/cards/batch/remark', data)
  },

  // 通过ICCID批量备注
  batchRemarkByIccids(data: { iccids: string[]; remark: string }): Promise<any> {
    return post('/cards/batch/remark-by-iccids', data)
  },

  // 批量续费
  batchRenew(data: CardBatchRenewRequest): Promise<{ success: number; failed: number }> {
    return post<{ success: number; failed: number }>('/cards/batch-renew', data)
  },

  // 通过ICCID批量续费
  batchRenewByIccids(data: { iccids: string[]; renew_months: number }): Promise<any> {
    return post('/cards/batch/renew-by-iccids', data)
  },

  // 批量停机
  batchSuspend(data: CardBatchSuspendRequest): Promise<{ success: number; failed: number }> {
    return post<{ success: number; failed: number }>('/cards/batch-suspend', data)
  },

  // 通过ICCID批量停机
  batchSuspendByIccids(data: { iccids: string[]; reason?: string }): Promise<any> {
    return post('/cards/batch/suspend-by-iccids', data)
  },

  // 批量复机
  batchResume(cardIds: number[], reason?: string): Promise<{ success: number; failed: number }> {
    return post<{ success: number; failed: number }>('/cards/batch-resume', { card_ids: cardIds, reason })
  },

  // 通过ICCID批量复机
  batchResumeByIccids(data: { iccids: string[] }): Promise<any> {
    return post('/cards/batch/resume-by-iccids', data)
  },

  // 获取划拨记录
  getTransfers(cardId: number, page = 1, pageSize = 20): Promise<PaginationResponse<any>> {
    return get<PaginationResponse<any>>(`/cards/${cardId}/transfers`, { params: { page, page_size: pageSize } })
  },

  // 导出卡片
  export(params: CardExportParams): Promise<Blob> {
    return post<Blob>('/cards/export', params, { responseType: 'blob' })
  }
}

