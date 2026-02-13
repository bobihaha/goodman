/**
 * 停卡管理 API
 */

import { get, post, put, del } from '@/utils/request'

/**
 * 停卡策略类型
 */
export interface SuspendPolicy {
  id: number
  name: string
  policy_type: 'expired' | 'pool_exceed' | 'card_exceed'
  description: string
  warning_threshold?: number
  critical_threshold?: number
  stop_threshold?: number
  user_id?: number
  pool_id?: number
  auto_suspend: boolean
  auto_resume: boolean
  notify_warning: boolean
  notify_critical: boolean
  notify_suspend: boolean
  is_enabled: boolean
  created_by?: number
  created_at: string
  updated_at: string
}

/**
 * 停卡记录类型
 */
export interface SuspendLog {
  id: number
  card_id: number
  iccid: string
  action: 'suspend' | 'resume'
  action_name: string
  suspend_type: string
  policy_id?: number
  pool_id?: number
  reason: string
  api_called: boolean
  api_result?: string
  operator_id?: number
  operator_name?: string
  created_at: string
}

/**
 * 告警记录类型
 */
export interface SuspendAlert {
  id: number
  target_type: string
  target_type_name: string
  target_id: number
  target_name?: string
  alert_level: string
  alert_level_name: string
  usage_percent: number
  threshold: number
  policy_id?: number
  user_id?: number
  notified: boolean
  notified_at?: string
  handled: boolean
  handled_at?: string
  handled_by?: number
  handle_remark?: string
  created_at: string
}

/** 分页响应 */
interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// ============ 停卡策略 ============

/** 获取停卡策略列表 */
export function getPolicies(params?: {
  policy_type?: string
  is_enabled?: boolean
  page?: number
  page_size?: number
}) {
  return get<PageResult<SuspendPolicy>>('/suspend/policies', { params })
}

/** 创建停卡策略 */
export function createPolicy(data: Partial<SuspendPolicy>) {
  return post<SuspendPolicy>('/suspend/policies', data)
}

/** 更新停卡策略 */
export function updatePolicy(id: number, data: Partial<SuspendPolicy>) {
  return put<SuspendPolicy>(`/suspend/policies/${id}`, data)
}

/** 删除停卡策略 */
export function deletePolicy(id: number) {
  return del(`/suspend/policies/${id}`)
}

// ============ 手动停卡/复机 ============

/** 批量停卡 */
export function batchSuspend(data: {
  card_ids: number[]
  reason?: string
}) {
  return post('/suspend/cards/suspend', data)
}

/** 批量复机 */
export function batchResume(data: {
  card_ids: number[]
  reason?: string
}) {
  return post('/suspend/cards/resume', data)
}

/** 批量强制激活（超级管理员） */
export function batchForceActivate(data: {
  card_ids: number[]
  reason?: string
}) {
  return post('/suspend/cards/force-activate', data)
}

// ============ 停卡记录 ============

/** 获取停卡记录列表 */
export function getSuspendLogs(params: {
  page: number
  page_size: number
  card_id?: number
  action?: string
  suspend_type?: string
  pool_id?: number
  start_time?: string
  end_time?: string
}) {
  return get<PageResult<SuspendLog>>('/suspend/logs', { params })
}

// ============ 告警管理 ============

/** 获取告警列表 */
export function getAlerts(params?: {
  target_type?: string
  alert_level?: string
  handled?: boolean
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}) {
  return get<PageResult<SuspendAlert>>('/suspend/alerts', { params })
}

/** 获取未处理告警统计 */
export function getAlertStats() {
  return get('/suspend/alerts/stats')
}

/** 处理告警 */
export function handleAlert(alertId: number, data?: { handle_remark?: string }) {
  return post(`/suspend/alerts/${alertId}/handle`, data || {})
}
