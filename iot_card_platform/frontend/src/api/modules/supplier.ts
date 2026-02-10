/**
 * 供应商 API
 */
import request from '@/utils/request'
import type {
  Supplier,
  CreateSupplierRequest,
  UpdateSupplierRequest,
  SupplierQueryParams,
  SupplierListResponse,
  ApiTestResult
} from '@/types/supplier'

/**
 * 获取供应商列表
 */
export function getSupplierList(params: SupplierQueryParams) {
  return request.get<SupplierListResponse>('/suppliers', { params })
}

/**
 * 获取供应商选项（用于下拉选择）
 */
export function getSupplierOptions() {
  return request.get<Supplier[]>('/suppliers/options')
}

/**
 * 获取所有启用的供应商（用于下拉选择）
 */
export function getEnabledSuppliers() {
  return request.get<Supplier[]>('/suppliers/options')
}

/**
 * 获取供应商详情
 */
export function getSupplierDetail(id: number) {
  return request.get<Supplier>(`/suppliers/${id}`)
}

/**
 * 创建供应商
 */
export function createSupplier(data: CreateSupplierRequest) {
  return request.post<Supplier>('/suppliers', data)
}

/**
 * 更新供应商
 */
export function updateSupplier(id: number, data: UpdateSupplierRequest) {
  return request.put<Supplier>(`/suppliers/${id}`, data)
}

/**
 * 删除供应商
 */
export function deleteSupplier(id: number) {
  return request.delete(`/suppliers/${id}`)
}

/**
 * 测试API连接
 */
export function testApiConnection(id: number) {
  return request.post<ApiTestResult>(`/suppliers/${id}/test`)
}

// 导出为 supplierApi 对象（保持与其他模块一致）
export const supplierApi = {
  getList: getSupplierList,
  getOptions: getSupplierOptions,
  getEnabled: getEnabledSuppliers,
  getDetail: getSupplierDetail,
  create: createSupplier,
  update: updateSupplier,
  delete: deleteSupplier,
  testConnection: testApiConnection
}

export default {
  getSupplierList,
  getSupplierOptions,
  getEnabledSuppliers,
  getSupplierDetail,
  createSupplier,
  updateSupplier,
  deleteSupplier,
  testApiConnection
}

