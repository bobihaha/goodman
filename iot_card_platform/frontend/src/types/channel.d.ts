export interface ChannelPartner {
  id: number
  name: string
  contact_name: string
  phone: string
  account: string
  h5_slug: string
  h5_path: string
  registration_enabled: boolean
  status: 'enable' | 'disable'
  stock_out_rate_override: number | null
  renewal_rate_override: number | null
  effective_stock_out_rate: number
  effective_renewal_rate: number
  customer_count: number
  last_login_at?: string | null
  remark?: string | null
  created_at?: string | null
}

export interface ChannelPointItem {
  id: number
  channel_id: number
  channel_name?: string | null
  customer_name: string
  customer_phone: string
  entry_type: 'credit' | 'reversal'
  order_type: 'stock_out' | 'renewal'
  source_order_no: string
  card_id: number
  iccid: string
  base_amount: number
  rate_percent: number
  points: number
  status: 'pending' | 'settled'
  settled_at?: string | null
  created_at?: string | null
}

export interface ChannelPointSummary {
  customer_count: number
  total_points: number
  pending_points: number
  settled_points: number
  consumed_points: number
  remaining_points: number
  month_points: number
}

export interface ChannelCustomerItem {
  id: number
  user_id: number
  customer_name: string
  customer_phone: string
  customer_profile?: string | null
  registered_at?: string | null
  point_count: number
  total_points: number
  consumed_points: number
  remaining_points: number
}
