/**
 * 卡片相关类型定义
 */

// 运营商类型
export type Carrier = 'cmcc' | 'cucc' | 'ctcc'

// 周期类型
export type PeriodType = 'monthly' | 'yearly'

// 卡片状态
export type CardStatus = 'stock' | 'testing' | 'silent' | 'activated' | 'expired' | 'suspended' | 'cancelled'

// 停卡类型
export type SuspendType = 'none' | 'manual' | 'expired' | 'pool_exceed' | 'card_exceed'

// 卡片信息
export interface Card {
  id: number
  iccid: string
  imsi?: string
  msisdn?: string
  user_id?: number
  supplier_id?: number
  batch_id?: number
  sale_package_id?: number
  carrier: Carrier
  flow_size: number
  period_type: PeriodType
  test_expire_date?: string
  silent_expire_date?: string
  activated_at?: string
  expired_at?: string
  data_used: number
  data_total: number
  data_sync_at?: string
  status: CardStatus
  suspend_type?: SuspendType
  suspend_at?: string
  suspend_reason?: string
  pool_id?: number
  is_pool_member: boolean
  remark?: string
  stock_in_at?: string
  stock_out_at?: string
  created_at: string
  updated_at?: string
  // 前端计算字段
  usage_percent?: number
  pool_name?: string
}

// 卡片列表查询参数
export interface CardListParams {
  page?: number
  page_size?: number
  iccid?: string
  msisdn?: string
  carrier?: Carrier
  status?: CardStatus
  period_type?: PeriodType
  user_id?: number
  pool_id?: number
  is_pool_member?: boolean
  keyword?: string
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

// 批量查询请求
export interface CardBatchQueryRequest {
  iccids: string[]
}

// 卡片划拨请求
export interface CardTransferRequest {
  card_ids: number[]
  to_user_id: number
  remark?: string
}

// 卡片备注请求
export interface CardRemarkRequest {
  card_ids: number[]
  remark: string
}

// 批量续费请求
export interface CardBatchRenewRequest {
  card_ids: number[]
  renew_period: 1 | 3 | 6 | 12
}

// 批量停机请求
export interface CardBatchSuspendRequest {
  card_ids: number[]
  reason?: string
}

// 卡片导出参数
export interface CardExportParams {
  card_ids?: number[]
  iccid?: string
  msisdn?: string
  carrier?: Carrier
  status?: CardStatus
  user_id?: number
}

