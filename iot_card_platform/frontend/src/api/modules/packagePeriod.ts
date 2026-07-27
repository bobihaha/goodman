import { get, post } from '@/utils/request'
import type { SalePackage } from '@/types/package'

export interface PackagePeriodBatchResult {
  success: number
  failed: number
  success_list: Array<Record<string, any>>
  failed_list: Array<{ iccid: string; error: string }>
  pool_check_warnings?: Array<{ pool_id: number; error: string }>
  supplier_synced?: boolean
}

export interface PackagePeriodLogRecord {
  id: number
  action: 'force_activate' | 'cancel_period' | 'change_package'
  operation_time?: string
  card_no?: string
  operator_name?: string
  detail?: string
}

export interface PackagePeriodLogResult {
  items: PackagePeriodLogRecord[]
  total: number
  page: number
  page_size: number
}

export const packagePeriodApi = {
  batchForceActivate(data: { iccids: string[]; reason?: string }) {
    return post<PackagePeriodBatchResult>('/package-period/force-activate', data)
  },

  batchCancelPeriod(data: { iccids: string[]; cancel_count: number; reason?: string }) {
    return post<PackagePeriodBatchResult>('/package-period/cancel-period', data)
  },

  getPackageOptions() {
    return get<SalePackage[]>('/package-period/package-options')
  },

  batchChangePackage(data: { iccids: string[]; target_sale_package_id: number; reason?: string }) {
    return post<PackagePeriodBatchResult>('/package-period/change-package', data)
  },

  getLogs(params: {
    action: 'force_activate' | 'cancel_period' | 'change_package'
    start_time?: string
    end_time?: string
    page: number
    page_size: number
  }) {
    return get<PackagePeriodLogResult>('/package-period/logs', { params })
  }
}
