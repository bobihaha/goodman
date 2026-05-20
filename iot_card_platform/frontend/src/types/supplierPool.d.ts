export interface SupplierTrafficPool {
  id: number
  supplier_id: number
  supplier_name?: string
  supplier_pool_code: string
  supplier_pool_name?: string
  carrier?: string
  pool_specification?: number
  total_flow: number
  used_flow: number
  remaining_flow: number
  package_flow: number
  usage_percent: number
  total_card_count: number
  active_card_count: number
  suspended_card_count: number
  stock_card_count: number
  testing_card_count: number
  cancelled_card_count: number
  activation_ready_count: number
  alert_threshold?: number
  alert_thresholds?: string
  alert_emails?: string
  last_alert_at?: string
  last_alert_usage_percent?: number
  last_alert_threshold?: number
  estimated_monthly_used_flow?: number | null
  estimated_month_end_remaining_flow?: number | null
  estimated_usage_percent?: number | null
  estimate_used_days?: number | null
  estimate_month_days?: number | null
  last_sync_at?: string
  sync_status: string
  sync_error?: string
}

export interface SupplierTrafficPoolQuery {
  supplier_name?: string
  carrier?: string
  pool_specification?: number
  order_by?: string
  order_dir?: string
  page?: number
  page_size?: number
}

export interface SupplierTrafficPoolAlertUpdate {
  alert_threshold?: number | null
  alert_thresholds?: number[]
  alert_emails?: string
}

export interface SupplierTrafficPoolHistory {
  id: number
  supplier_pool_id: number
  supplier_id: number
  supplier_name?: string
  supplier_pool_code: string
  supplier_pool_name?: string
  record_month: string
  carrier?: string
  pool_specification?: number
  total_flow: number
  used_flow: number
  remaining_flow: number
  package_flow: number
  usage_percent: number
  estimated_monthly_used_flow?: number | null
  estimated_month_end_remaining_flow?: number | null
  estimated_usage_percent?: number | null
  estimate_used_days?: number | null
  estimate_month_days?: number | null
  total_card_count: number
  active_card_count: number
  sync_at?: string
}

export interface SupplierTrafficPoolDetail {
  pool: SupplierTrafficPool
  histories: SupplierTrafficPoolHistory[]
}
