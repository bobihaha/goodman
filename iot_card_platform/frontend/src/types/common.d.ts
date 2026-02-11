/**
 * 通用类型定义
 */

// 统一响应结构
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// 分页请求参数
export interface PageParams {
  page: number
  page_size: number
}

// 分页响应结构
export interface PageResponse<T = any> {
  total: number
  list: T[]
  page: number
  page_size: number
}

// 分页响应结构（别名）
export type PaginationResponse<T = any> = PageResponse<T>

// 运营商类型
export type Carrier = 'cmcc' | 'cucc' | 'ctcc'

// 卡片状态
export type CardStatus = 'stock' | 'testing' | 'silent' | 'activated' | 'expired' | 'suspended' | 'cancelled'

// 套餐周期类型
export type PeriodType = 'monthly' | 'yearly'

// 卡片类型
export type CardType = 'single' | 'pool'

// 用户状态
export type UserStatus = 'enable' | 'disable'

// 用户级别
export type UserLevel = 1 | 2 | 3

// 选项类型
export interface Option {
  label: string
  value: string | number
}


