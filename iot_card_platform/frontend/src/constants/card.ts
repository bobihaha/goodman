/**
 * 卡片管理相关常量
 */

// 运营商映射
export const CARRIER_MAP = {
  cmcc: '中国移动',
  cucc: '中国联通',
  ctcc: '中国电信'
} as const

// 运营商选项
export const CARRIER_OPTIONS = [
  { label: '中国移动', value: 'cmcc' },
  { label: '中国联通', value: 'cucc' },
  { label: '中国电信', value: 'ctcc' }
]

// 卡片状态映射
export const CARD_STATUS_MAP = {
  stock: { label: '库存', type: 'info', color: '#909399' },
  testing: { label: '测试期', type: 'warning', color: '#E6A23C' },
  silent: { label: '沉默期', type: '', color: '#F56C6C' },
  activated: { label: '已激活', type: 'success', color: '#67C23A' },
  expired: { label: '已到期', type: 'danger', color: '#F56C6C' },
  suspended: { label: '已停机', type: 'danger', color: '#C03639' },
  cancelled: { label: '已销卡', type: 'info', color: '#909399' }
} as const

// 卡片状态选项
export const CARD_STATUS_OPTIONS = [
  { label: '库存', value: 'stock' },
  { label: '测试期', value: 'testing' },
  { label: '沉默期', value: 'silent' },
  { label: '已激活', value: 'activated' },
  { label: '已到期', value: 'expired' },
  { label: '已停机', value: 'suspended' },
  { label: '已销卡', value: 'cancelled' }
]

// 周期类型映射
export const PERIOD_TYPE_MAP = {
  monthly: '月包',
  yearly: '年包'
} as const

// 周期类型选项
export const PERIOD_TYPE_OPTIONS = [
  { label: '月包', value: 'monthly' },
  { label: '年包', value: 'yearly' }
]

// 停卡类型映射
export const SUSPEND_TYPE_MAP = {
  none: '未停卡',
  manual: '手动停卡',
  expired: '到期停卡',
  pool_exceed: '流量池超限',
  card_exceed: '单卡超量'
} as const

// 续费周期选项
export const RENEW_PERIOD_OPTIONS = [
  { label: '1个月', value: 1 },
  { label: '3个月', value: 3 },
  { label: '6个月', value: 6 },
  { label: '12个月', value: 12 }
]

// 批量查询最大数量
export const BATCH_QUERY_MAX_COUNT = 10000

// 流量单位转换阈值（MB）
export const FLOW_UNIT_THRESHOLD = 1024


