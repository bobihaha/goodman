/**
 * 仪表盘相关 API
 */

import { get, post } from '@/utils/request'

// 账户余额信息
export interface AccountBalance {
  balance: number
  alert_threshold: number
  is_alert: boolean
  last_recharge_at: string | null
  last_recharge_amount: number
}

// 卡片统计
export interface CardStats {
  total: number
  stock: number
  testing: number
  silent: number
  activated: number
  expired: number
  suspended: number
  cancelled: number
  by_carrier: {
    cmcc: number
    cucc: number
    ctcc: number
  }
}

// 到期卡片
export interface ExpiringCard {
  id: number
  iccid: string
  msisdn: string
  carrier: string
  expired_at: string
  days_left: number
  user_name: string
  package_name: string
}

// 超量卡片
export interface OverUsageCard {
  id: number
  iccid: string
  msisdn: string
  carrier: string
  data_used: number
  data_total: number
  usage_percent: number
  over_usage: number
  user_name: string
}

// 流量池用量
export interface PoolUsage {
  id: number
  name: string
  carrier: string
  data_total: number
  data_used: number
  usage_percent: number
  card_count: number
  is_alert: boolean
}

// 流量趋势数据
export interface UsageTrend {
  date: string
  usage: number
}

// 告警信息
export interface Alert {
  id: number
  type: string
  title: string
  content: string
  level: 'info' | 'warning' | 'error'
  created_at: string
  is_read: boolean
}

export const dashboardApi = {
  // 获取概览数据
  getOverview(): Promise<{
    card_stats: CardStats
    pool_count: number
    user_count: number
    alert_count: number
  }> {
    return get('/dashboard/overview')
  },

  // 获取账户余额
  getAccountBalance(): Promise<AccountBalance> {
    return get('/dashboard/account/balance')
  },

  // 获取本月到期卡
  getExpiringCards(): Promise<ExpiringCard[]> {
    return get('/dashboard/cards/expiring')
  },

  // 获取超量卡
  getOverUsageCards(): Promise<OverUsageCard[]> {
    return get('/dashboard/cards/over-usage')
  },

  // 获取流量池用量百分比
  getPoolsUsagePercent(): Promise<PoolUsage[]> {
    return get('/dashboard/pools/usage-percent')
  },

  // 获取流量使用趋势
  getUsageTrend(days: number = 7): Promise<UsageTrend[]> {
    return get('/dashboard/usage/trend', { params: { days } })
  },

  // 获取告警列表
  getAlerts(limit: number = 10): Promise<Alert[]> {
    return get('/dashboard/alerts', { params: { limit } })
  }
}






