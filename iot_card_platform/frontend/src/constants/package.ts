/**
 * 套餐管理常量定义
 */

import type { Carrier, PeriodType } from '@/types/common'

// 运营商选项
export const CARRIER_OPTIONS = [
  { label: '中国移动', value: 'cmcc' as Carrier },
  { label: '中国联通', value: 'cucc' as Carrier },
  { label: '中国电信', value: 'ctcc' as Carrier }
]

// 运营商映射
export const CARRIER_MAP: Record<Carrier, string> = {
  cmcc: '中国移动',
  cucc: '中国联通',
  ctcc: '中国电信'
}

// 周期类型选项
export const PERIOD_TYPE_OPTIONS = [
  { label: '月包', value: 'monthly' as PeriodType },
  { label: '年包', value: 'yearly' as PeriodType }
]

// 周期类型映射
export const PERIOD_TYPE_MAP: Record<PeriodType, string> = {
  monthly: '月包',
  yearly: '年包'
}

// 状态选项
export const STATUS_OPTIONS = [
  { label: '启用', value: 'enable' },
  { label: '禁用', value: 'disable' }
]

// 状态映射
export const STATUS_MAP: Record<'enable' | 'disable', { label: string; type: string }> = {
  enable: { label: '启用', type: 'success' },
  disable: { label: '禁用', type: 'info' }
}

// 流量单位选项
export const FLOW_UNIT_OPTIONS = [
  { label: 'MB', value: 1 },
  { label: 'GB', value: 1024 }
]

// 常用流量规格（MB）
export const COMMON_FLOW_SIZES = [
  { label: '100MB', value: 100 },
  { label: '500MB', value: 500 },
  { label: '1GB', value: 1024 },
  { label: '2GB', value: 2048 },
  { label: '3GB', value: 3072 },
  { label: '5GB', value: 5120 },
  { label: '10GB', value: 10240 },
  { label: '20GB', value: 20480 },
  { label: '30GB', value: 30720 },
  { label: '50GB', value: 51200 },
  { label: '100GB', value: 102400 }
]

// 常用有效天数（旧字段兼容，年包实际按 12 个计费月计算）
export const COMMON_VALID_DAYS = [
  { label: '30天（月包）', value: 30 },
  { label: '90天（季包）', value: 90 },
  { label: '180天（半年包）', value: 180 },
  { label: '12个月（年包）', value: 360 }
]







