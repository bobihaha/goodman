/**
 * 流量池管理相关常量
 */

// 流量池状态映射
export const POOL_STATUS_MAP = {
  enable: { label: '启用', type: 'success', color: '#67C23A' },
  disable: { label: '禁用', type: 'info', color: '#909399' }
} as const

// 流量池状态选项
export const POOL_STATUS_OPTIONS = [
  { label: '启用', value: 'enable' },
  { label: '禁用', value: 'disable' }
]

// 默认告警阈值（%）
export const DEFAULT_ALERT_THRESHOLD = 80

// 默认停卡阈值（%）
export const DEFAULT_STOP_THRESHOLD = 100

// 告警阈值选项
export const ALERT_THRESHOLD_OPTIONS = [
  { label: '60%', value: 60 },
  { label: '70%', value: 70 },
  { label: '80%', value: 80 },
  { label: '90%', value: 90 },
  { label: '95%', value: 95 }
]

// 停卡阈值选项
export const STOP_THRESHOLD_OPTIONS = [
  { label: '90%', value: 90 },
  { label: '95%', value: 95 },
  { label: '100%', value: 100 },
  { label: '105%', value: 105 },
  { label: '110%', value: 110 }
]

// 加油包规格选项（MB）
export const RECHARGE_PACKAGE_OPTIONS = [
  { label: '1GB', value: 1024 },
  { label: '5GB', value: 5120 },
  { label: '10GB', value: 10240 },
  { label: '20GB', value: 20480 },
  { label: '50GB', value: 51200 }
]

