/**
 * 流量池相关类型定义
 */

import type { Carrier, PeriodType } from './card'

// 流量池状态
export type PoolStatus = 'enable' | 'disable'

// 流量池信息
export interface Pool {
  id: number
  name: string
  user_id: number
  sale_package_id: number        // 销售套餐ID（组池依据）
  carrier: Carrier
  flow_size: number              // 单卡流量(MB)
  period_type: PeriodType        // 固定为 monthly（月包）
  card_count: number             // 卡片数量
  data_total: number             // 总流量(MB)
  data_used: number              // 已用流量(MB)
  data_remaining: number         // 剩余流量(MB)
  package_flow?: number          // 套餐流量(MB)
  addon_flow?: number            // 叠加流量(MB)
  usage_percent: number          // 使用率(%)
  alert_threshold_1?: number     // 第一次告警阈值(%)
  alert_threshold_2?: number     // 第二次告警阈值(%)
  alert_threshold_3?: number     // 第三次告警阈值(%)
  is_alert: boolean              // 是否触发告警
  status: PoolStatus
  remark?: string
  last_sync_at?: string          // 最近同步时间
  created_at: string
  updated_at?: string
  // 关联信息
  user_name?: string
  sale_package_name?: string     // 销售套餐名称
  can_self_topup?: boolean
  // 卡片统计
  card_stats?: {
    activated: number            // 已激活
    suspended: number            // 已停卡
    stock: number                // 库存
    testing: number              // 测试期
    silent: number               // 沉默期
    expired?: number             // 已到期
    cancelled: number            // 已销卡
  }
}

// 流量池列表查询参数
export interface PoolListParams {
  page?: number
  page_size?: number
  name?: string
  carrier?: Carrier
  sale_package_id?: number
  status?: PoolStatus
  user_id?: number
  is_alert?: boolean
  keyword?: string
}

// 流量池更新请求（只能修改告警阈值、备注）
export interface PoolUpdateData {
  alert_threshold_1?: number
  alert_threshold_2?: number
  alert_threshold_3?: number
  remark?: string
}

// 流量池统计
export interface PoolStats {
  total: number
  enabled: number
  disabled: number
  alert_count: number            // 告警数量
  total_cards: number            // 总卡片数
  total_flow: number             // 总流量(MB)
  used_flow: number              // 已用流量(MB)
  by_carrier: {
    cmcc: number
    cucc: number
    ctcc: number
  }
}

// 添加卡片到流量池请求
export interface PoolAddCardsRequest {
  pool_id: number
  card_ids?: number[]            // 卡片ID数组（二选一）
  iccids?: string[]              // ICCID数组（二选一）
}

// 从流量池移除卡片请求
export interface PoolRemoveCardsRequest {
  pool_id: number
  card_ids?: number[]            // 卡片ID数组（二选一）
  iccids?: string[]              // ICCID数组（二选一）
}

// 流量池用量趋势数据
export interface PoolUsageTrend {
  date: string                   // 日期
  data_used: number              // 当日已用流量(MB)
  data_total: number             // 当日总流量(MB)
  usage_percent: number          // 使用率(%)
}

// 流量池加油包
export interface PoolPackage {
  id: number
  name: string                   // 加油包名称，如：1GB加油包
  flow_size: number              // 流量大小(MB)
  price: number                  // 价格（元）
  valid_days: number             // 有效天数
  carrier: Carrier               // 运营商
  status: 'enable' | 'disable'
}

// 充值加油包请求
export interface PoolRechargeRequest {
  pool_id: number
  added_flow_mb: number          // 增加流量(MB)
  remark?: string
}

// 充值记录
export interface PoolRechargeLog {
  id: number
  pool_id: number
  pool_name: string
  package_id: number
  package_name: string
  flow_size: number              // 充值流量(MB)
  price: number                  // 价格（元）
  valid_days: number             // 有效天数
  expire_at: string              // 过期时间
  status: 'active' | 'expired'   // 状态：active-生效中，expired-已过期
  created_at: string
  created_by: number
  created_by_name?: string
}

// 流量池本地停卡状态修复结果
export interface PoolRepairSuspendStatusResult {
  checked: number
  repaired: number
  skipped: number
  repaired_iccids: string[]
  skipped_list: Array<{
    iccid: string
    reason: string
  }>
  usage_percent: number
  stop_threshold: number
}

// 流量池详情（包含卡片列表）
export interface PoolDetail extends Pool {
  cards?: Array<{
    id: number
    iccid: string
    msisdn?: string
    status: string
    data_used: number
    data_total: number
    usage_percent: number
    activated_at?: string
    expired_at?: string
  }>
}
