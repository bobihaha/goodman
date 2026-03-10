// 出入库记录类型定义

export interface CardStockRecordItem {
  record_type: 'in' | 'out'
  record_id: number
  iccid: string
  operator?: string
  created_at: string
  test_expire_date?: string
  silent_expire_date?: string
  supplier_name?: string
  base_package_name?: string
  sale_package_name?: string
  target_user_name?: string
  carrier?: string
  flow_size?: number
  period_type?: string
}

export interface CardStockRecordResponse {
  total: number
  records: CardStockRecordItem[]
}
