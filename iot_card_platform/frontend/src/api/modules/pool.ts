/**
 * 流量池管理 API
 */

import request from '@/utils/request'
import type {
  Pool,
  PoolListParams,
  PoolUpdateData,
  PoolStats,
  PoolAddCardsRequest,
  PoolRemoveCardsRequest,
  PoolUsageTrend,
  PoolPackage,
  PoolRechargeRequest,
  PoolRechargeLog,
  PoolDetail
} from '@/types/pool'
import type { PageResponse } from '@/types/common'

/**
 * 获取流量池列表
 */
export function getPoolList(params: PoolListParams) {
  return request.get<PageResponse<Pool>>('/pools', { params })
}

/**
 * 获取流量池详情
 */
export function getPoolDetail(id: number) {
  return request.get<PoolDetail>(`/pools/${id}`)
}

/**
 * 更新流量池（只能修改告警阈值、停卡阈值、备注）
 */
export function updatePool(id: number, data: PoolUpdateData) {
  return request.put<Pool>(`/pools/${id}`, data)
}

/**
 * 删除流量池
 */
export function deletePool(id: number) {
  return request.delete(`/pools/${id}`)
}

/**
 * 启用/禁用流量池
 */
export function togglePoolStatus(id: number, status: 'enable' | 'disable') {
  return request.put(`/pools/${id}/status`, { status })
}

/**
 * 获取流量池统计
 */
export function getPoolStats() {
  return request.get<PoolStats>('/pools/stats')
}

/**
 * 添加卡片到流量池
 */
export function addCardsToPool(data: PoolAddCardsRequest) {
  return request.post(`/pools/${data.pool_id}/cards`, {
    card_ids: data.card_ids,
    iccids: data.iccids
  })
}

/**
 * 从流量池移除卡片
 */
export function removeCardsFromPool(data: PoolRemoveCardsRequest) {
  return request.delete(`/pools/${data.pool_id}/cards`, {
    data: {
      card_ids: data.card_ids,
      iccids: data.iccids
    }
  })
}

/**
 * 获取流量池用量趋势（最近30天）
 */
export function getPoolUsageTrend(id: number, days = 30) {
  return request.get<PoolUsageTrend[]>(`/pools/${id}/usage/trend`, {
    params: { days }
  })
}

/**
 * 获取流量池内的卡片列表
 */
export function getPoolCards(id: number, params?: { page?: number; page_size?: number }) {
  return request.get<PageResponse<any>>(`/pools/${id}/cards`, { params })
}

/**
 * 获取加油包列表
 */
export function getPoolPackages(carrier?: string) {
  return request.get<PoolPackage[]>('/pools/packages', {
    params: { carrier }
  })
}

/**
 * 充值加油包
 */
export function rechargePool(data: PoolRechargeRequest) {
  return request.post(`/pools/${data.pool_id}/recharge`, {
    package_id: data.package_id
  })
}

/**
 * 获取充值记录
 */
export function getRechargeLog(poolId: number, params?: { page?: number; page_size?: number }) {
  return request.get<PageResponse<PoolRechargeLog>>(`/pools/${poolId}/recharge-logs`, { params })
}

/**
 * 导出流量池列表
 */
export function exportPools(params?: PoolListParams) {
  return request.post('/pools/export', params, {
    responseType: 'blob'
  })
}

