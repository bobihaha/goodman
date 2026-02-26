/**
 * 供应商模块类型定义
 */

// 供应商类型
export type SupplierType = 'cmcc' | 'cucc' | 'ctcc' | 'mvno' | 'other'

// 供应商状态
export type SupplierStatus = 'enable' | 'disable'

// 供应商信息
export interface Supplier {
  id: number
  name: string
  code: string
  type: SupplierType
  contact_name?: string
  contact_phone?: string
  contact_email?: string
  api_url?: string
  has_api_key?: boolean
  has_api_secret?: boolean
  api_config?: Record<string, any>
  remark?: string
  status: SupplierStatus
  created_at?: string
  updated_at?: string
}

// 创建供应商请求
export interface CreateSupplierRequest {
  name: string
  code: string
  type: SupplierType
  contact_name?: string
  contact_phone?: string
  contact_email?: string
  api_url?: string
  api_key?: string
  api_secret?: string
  api_config?: Record<string, any>
  remark?: string
}

// 更新供应商请求
export interface UpdateSupplierRequest {
  name?: string
  type?: SupplierType
  contact_name?: string
  contact_phone?: string
  contact_email?: string
  api_url?: string
  api_key?: string
  api_secret?: string
  api_config?: Record<string, any>
  remark?: string
  status?: SupplierStatus
}

// 供应商查询参数
export interface SupplierQueryParams {
  keyword?: string
  type?: SupplierType
  status?: SupplierStatus
  page?: number
  page_size?: number
}

// 供应商列表响应
export interface SupplierListResponse {
  list: Supplier[]
  total: number
  page: number
  page_size: number
}

// API测试结果
export interface ApiTestResult {
  success: boolean
  message: string
  response_time?: number
}







