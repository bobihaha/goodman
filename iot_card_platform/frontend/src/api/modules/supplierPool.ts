import request from '@/utils/request'
import type {
  SupplierTrafficPool,
  SupplierTrafficPoolAlertUpdate,
  SupplierTrafficPoolDetail,
  SupplierTrafficPoolQuery
} from '@/types/supplierPool'

interface SupplierTrafficPoolPageResponse {
  total: number
  items: SupplierTrafficPool[]
  page: number
  page_size: number
}

export function getSupplierTrafficPools(params: SupplierTrafficPoolQuery) {
  return request.get<SupplierTrafficPoolPageResponse>('/supplier-traffic-pools', { params })
}

export function syncSupplierTrafficPools(supplierId?: number) {
  return request.post('/supplier-traffic-pools/sync', { supplier_id: supplierId })
}

export function updateSupplierTrafficPoolAlert(id: number, data: SupplierTrafficPoolAlertUpdate) {
  return request.put<SupplierTrafficPool>(`/supplier-traffic-pools/${id}/alert`, data)
}

export function getSupplierTrafficPoolDetail(id: number, months = 12) {
  return request.get<SupplierTrafficPoolDetail>(`/supplier-traffic-pools/${id}`, { params: { months } })
}

export function exportSupplierTrafficPoolHistories(id: number, months = 36) {
  return request.post<Record<string, any>[]>(`/supplier-traffic-pools/${id}/histories/export`, undefined, {
    params: { months }
  })
}
