/**
 * 套餐管理类型定义
 */

import type { Carrier, PeriodType, PageParams } from './common'

// 底层套餐（供应商套餐）
export interface SupplierPackage {
  id: number
  code: string                    // 套餐编码（后端字段名）
  name: string                    // 套餐名称
  carrier: Carrier                // 运营商
  flow_size: number               // 流量大小(MB)
  period_type: PeriodType         // 周期类型
  effective_days: number          // 有效天数
  price_cost: number              // 采购成本（元）
  supplier_id: number             // 供应商ID
  supplier_name?: string          // 供应商名称（关联查询）
  remark?: string                 // 备注
  status: 'enable' | 'disable'    // 状态
  created_at?: string             // 创建时间
  updated_at?: string             // 更新时间
}

// 销售套餐
export interface SalePackage {
  id: number
  code: string                    // 套餐编码（后端字段名）
  name: string                    // 销售套餐名称
  base_package_id?: number        // 关联的底层套餐ID（后端字段名）
  base_package_name?: string      // 关联的底层套餐名称（关联查询）
  carrier: Carrier                // 运营商
  flow_size: number               // 流量大小(MB)
  period_type: PeriodType         // 周期类型
  effective_days: number          // 有效天数
  price_cost: number              // 成本价（元）
  price_sale: number              // 销售价格（元）
  profit_margin?: number          // 利润率(%) - 前端计算
  is_public?: boolean             // 是否公开
  sort_order?: number             // 排序
  status: 'enable' | 'disable'    // 状态
  remark?: string                 // 备注
  created_at?: string             // 创建时间
  updated_at?: string             // 更新时间
}

// 底层套餐列表查询参数
export interface SupplierPackageListParams extends PageParams {
  carrier?: Carrier               // 运营商筛选
  period_type?: PeriodType        // 周期类型筛选
  supplier_id?: number            // 供应商筛选
  status?: 'enable' | 'disable'   // 状态筛选
  keyword?: string                // 关键词搜索（套餐名称/package_id）
}

// 销售套餐列表查询参数
export interface SalePackageListParams extends PageParams {
  supplier_package_id?: number    // 底层套餐筛选
  status?: 'enable' | 'disable'   // 状态筛选
  keyword?: string                // 关键词搜索
}

// 创建底层套餐请求
export interface CreateSupplierPackageRequest {
  code: string                    // 套餐编码
  name: string                    // 套餐名称
  carrier: Carrier                // 运营商
  flow_size: number               // 流量大小(MB)
  period_type: PeriodType         // 周期类型
  effective_days?: number         // 有效天数（可选，后端有默认值）
  price_cost: number              // 采购成本（元）
  supplier_id: number             // 供应商ID
  remark?: string                 // 备注
  status?: 'enable' | 'disable'   // 状态（默认enable）
}

// 更新底层套餐请求
export interface UpdateSupplierPackageRequest extends Partial<CreateSupplierPackageRequest> {
  id: number
}

// 创建销售套餐请求
export interface CreateSalePackageRequest {
  code: string                    // 套餐编码
  name: string                    // 销售套餐名称
  base_package_id?: number        // 关联的底层套餐ID（可选）
  carrier: Carrier                // 运营商
  flow_size: number               // 流量大小(MB)
  period_type: PeriodType         // 周期类型
  effective_days?: number         // 有效天数（可选）
  price_cost: number              // 成本价（元）
  price_sale: number              // 销售价格（元）
  is_public?: boolean             // 是否公开（默认false）
  sort_order?: number             // 排序（默认0）
  status?: 'enable' | 'disable'   // 状态
  remark?: string                 // 备注
}

// 更新销售套餐请求
export interface UpdateSalePackageRequest extends Partial<CreateSalePackageRequest> {
  id: number
}

// 供应商信息（简化版）
export interface Supplier {
  id: number
  name: string
  contact?: string
  phone?: string
  status: 'enable' | 'disable'
}

// 供应商列表查询参数
export interface SupplierListParams extends PageParams {
  status?: 'enable' | 'disable'
  keyword?: string
}

