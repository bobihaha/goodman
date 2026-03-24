/**
 * 套餐管理 API
 */

import { get, post, put, del } from '@/utils/request'
import type {
  SupplierPackage,
  SalePackage,
  SupplierPackageListParams,
  SalePackageListParams,
  CreateSupplierPackageRequest,
  CreateSalePackageRequest,
  Supplier,
  SupplierListParams
} from '@/types/package'
import type { PaginationResponse } from '@/types/common'

// ==================== 底层套餐（供应商套餐）API ====================

export const supplierPackageApi = {
  // 获取底层套餐列表
  getList(params: SupplierPackageListParams): Promise<PaginationResponse<SupplierPackage>> {
    return get<PaginationResponse<SupplierPackage>>('/packages/supplier', { params })
  },

  // 获取底层套餐详情
  getDetail(id: number): Promise<SupplierPackage> {
    return get<SupplierPackage>(`/packages/supplier/${id}`)
  },

  // 创建底层套餐
  create(data: CreateSupplierPackageRequest): Promise<SupplierPackage> {
    return post<SupplierPackage>('/packages/supplier', data)
  },

  // 更新底层套餐
  update(id: number, data: Partial<CreateSupplierPackageRequest>): Promise<SupplierPackage> {
    return put<SupplierPackage>(`/packages/supplier/${id}`, data)
  },

  // 删除底层套餐
  delete(id: number): Promise<void> {
    return del<void>(`/packages/supplier/${id}`)
  },

  // 启用/禁用底层套餐
  updateStatus(id: number, status: 'enable' | 'disable'): Promise<void> {
    return put<void>(`/packages/supplier/${id}`, { status })
  },

  // 获取供应商的套餐选项（用于下拉选择）
  getBySupplier(supplierId: number): Promise<SupplierPackage[]> {
    return get<SupplierPackage[]>(`/packages/supplier/options/${supplierId}`)
  },

  // 获取所有启用的底层套餐（用于下拉选择）
  getEnabled(): Promise<SupplierPackage[]> {
    return get<SupplierPackage[]>('/packages/supplier/options')
  }
}

// ==================== 销售套餐 API ====================

export const salePackageApi = {
  // 获取销售套餐列表
  getList(params: SalePackageListParams): Promise<PaginationResponse<SalePackage>> {
    return get<PaginationResponse<SalePackage>>('/packages/sale', { params })
  },

  // 获取销售套餐详情
  getDetail(id: number): Promise<SalePackage> {
    return get<SalePackage>(`/packages/sale/${id}`)
  },

  // 创建销售套餐
  create(data: CreateSalePackageRequest): Promise<SalePackage> {
    return post<SalePackage>('/packages/sale', data)
  },

  // 更新销售套餐
  update(id: number, data: Partial<CreateSalePackageRequest>): Promise<SalePackage> {
    return put<SalePackage>(`/packages/sale/${id}`, data)
  },

  // 删除销售套餐
  delete(id: number): Promise<void> {
    return del<void>(`/packages/sale/${id}`)
  },

  // 启用/禁用销售套餐
  updateStatus(id: number, status: 'enable' | 'disable'): Promise<void> {
    return put<void>(`/packages/sale/${id}`, { status })
  },

  // 获取所有启用的销售套餐（用于下拉选择）
  getEnabled(): Promise<SalePackage[]> {
    return get<SalePackage[]>('/packages/sale/options')
  }
}

// ==================== 供应商 API ====================

export const supplierApi = {
  // 获取供应商列表
  getList(params: SupplierListParams): Promise<PaginationResponse<Supplier>> {
    return get<PaginationResponse<Supplier>>('/suppliers', { params })
  },

  // 获取所有启用的供应商（用于下拉选择）
  getEnabled(): Promise<Supplier[]> {
    return get<Supplier[]>('/suppliers/options')
  },

  // 获取供应商详情
  getDetail(id: number): Promise<Supplier> {
    return get<Supplier>(`/suppliers/${id}`)
  }
}

// ==================== 统一导出（兼容旧代码）====================

export const packageApi = {
  // 底层套餐相关
  getSupplierPackages(params: any): Promise<any> {
    return supplierPackageApi.getList(params)
  },
  
  // 销售套餐相关
  getSalePackages(params: any): Promise<any> {
    return salePackageApi.getList(params)
  },
  
  // 获取底层套餐详情
  getSupplierPackageDetail(id: number): Promise<any> {
    return supplierPackageApi.getDetail(id)
  },
  
  // 获取销售套餐详情
  getSalePackageDetail(id: number): Promise<any> {
    return salePackageApi.getDetail(id)
  }
}
