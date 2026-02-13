/**
 * 供应商模块常量
 */

// 供应商类型选项
export const SUPPLIER_TYPE_OPTIONS = [
  { label: '中国移动', value: 'cmcc' },
  { label: '中国联通', value: 'cucc' },
  { label: '中国电信', value: 'ctcc' },
  { label: '虚拟运营商', value: 'mvno' },
  { label: '其他', value: 'other' }
]

// 供应商类型映射
export const SUPPLIER_TYPE_MAP: Record<string, string> = {
  cmcc: '中国移动',
  cucc: '中国联通',
  ctcc: '中国电信',
  mvno: '虚拟运营商',
  other: '其他'
}

// 供应商状态选项
export const SUPPLIER_STATUS_OPTIONS = [
  { label: '启用', value: 'enable' },
  { label: '禁用', value: 'disable' }
]

// 供应商状态映射
export const SUPPLIER_STATUS_MAP: Record<string, { label: string; type: string }> = {
  enable: { label: '启用', type: 'success' },
  disable: { label: '禁用', type: 'info' }
}







