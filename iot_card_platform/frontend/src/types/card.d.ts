/**
 * 卡片相关类型定义
 */

// 运营商类型
export type Carrier = 'cmcc' | 'cucc' | 'ctcc'

// 周期类型
export type PeriodType = 'monthly' | 'yearly'

// 卡片类型
export type CardType = 'single' | 'pool'

// 卡片状态
export type CardStatus = 'stock' | 'testing' | 'silent' | 'activated' | 'expired' | 'suspended' | 'cancelled'
export type SortOrder = 'asc' | 'desc'

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
  batch_id?: string
  sale_package_id?: number
  sale_price?: number
  carrier: Carrier
  carrier_name?: string
  flow_size: number
  flow_size_display?: string
  period_type: PeriodType
  period_name?: string
  spec_name?: string
  card_type: CardType             // 卡片类型
  card_type_name?: string         // 卡片类型名称
  test_expire_date?: string       // 测试期到期日（格式：26/1/31）
  silent_expire_date?: string     // 沉默期到期日（格式：26/1/31）
  activated_at?: string           // 激活日期（格式：26/1/31）
  expired_at?: string             // 到期日期（格式：26/1/31）
  data_used: number               // 已用流量
  data_total: number              // 套餐总量
  data_used_month: number         // 本月用量
  data_remain?: number
  data_usage_percent?: number
  data_sync_at?: string
  status: CardStatus
  status_name?: string
  suspend_type?: SuspendType
  suspend_type_name?: string
  suspend_at?: string
  suspend_reason?: string
  pool_id?: number
  is_pool_member: boolean
  remark?: string
  stock_in_at?: string            // 入库时间（ISO格式）
  stock_out_at?: string           // 出库时间（ISO格式）
  stock_out_date?: string         // 出库日期
  stock_out_no?: string           // 出库单号
  created_at: string
  updated_at?: string
  // 前端计算字段
  usage_percent?: number
  pool_name?: string
  related_user_name?: string
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
  over_usage?: boolean
  keyword?: string
  // 高级搜索
  remark?: string
  customer_id?: number
  batch_id?: string
  stock_out_start?: string
  stock_out_end?: string
  activated_start?: string
  activated_end?: string
  expired_start?: string
  expired_end?: string
  sort_by?: string
  sort_order?: SortOrder
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
  keyword?: string
  iccid?: string
  msisdn?: string
  carrier?: Carrier
  status?: CardStatus
  period_type?: PeriodType
  user_id?: number
  is_pool_member?: boolean
  over_usage?: boolean
  remark?: string
  customer_id?: number
  batch_id?: string
  stock_out_start?: string
  stock_out_end?: string
  activated_start?: string
  activated_end?: string
  expired_start?: string
  expired_end?: string
}

// 用量历史记录
export interface UsageHistory {
  id: number
  card_id: number
  iccid: string
  data_used: number
  daily_used?: number
  data_total: number
  period_type: string
  snapshot_date: string
  snapshot_type: string
  snapshot_month: string
  created_at: string
}

export interface CardDiagnostics {
  card_id: number
  iccid: string
  msisdn?: string
  supplier_id?: number
  supplier_name?: string
  power_status?: string
  power_status_msg?: string
  work_status?: string
  work_status_msg?: string
}
