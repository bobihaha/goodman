/**
 * 出入库管理 API
 */
import request from '@/utils/request'

export const stockApi = {
  // ============ 批次管理 ============

  /**
   * 创建采购批次
   */
  createBatch(data: any) {
    return request.post('/stock/batches', data)
  },

  // ============ 入库 ============

  /**
   * 批量入库
   */
  stockIn(data: any) {
    return request.post('/stock/in', data)
  },

  /**
   * 获取入库记录
   */
  getStockInRecords(params: any) {
    return request.get('/stock/in/records', { params })
  },

  /**
   * 获取入库记录详情
   */
  getStockInDetail(id: number) {
    return request.get(`/stock/in/records/${id}`)
  },

  /**
   * 导出入库记录
   */
  exportStockInRecords(params: any) {
    return request.post('/stock/in/records/export', params)
  },

  // ============ 出库 ============

  /**
   * 批量出库
   */
  stockOut(data: any) {
    return request.post('/stock/out', data)
  },

  /**
   * 下载Excel出库模板
   */
  downloadStockOutTemplate() {
    return request.get('/stock/out/template')
  },

  /**
   * Excel批量出库
   */
  batchStockOutImport(data: any) {
    return request.post('/stock/out/batch-import', data)
  },

  /**
   * 获取出库记录
   */
  getStockOutRecords(params: any) {
    return request.get('/stock/out/records', { params })
  },

  /**
   * 获取出库记录详情
   */
  getStockOutDetail(id: number) {
    return request.get(`/stock/out/records/${id}`)
  },

  /**
   * 导出出库记录
   */
  exportStockOutRecords(params: any) {
    return request.post('/stock/out/records/export', params)
  },

  // ============ 卡片回收 ============

  /**
   * 卡片回收
   */
  recycleCards(data: any) {
    return request.post('/stock/recycle', data)
  },

  /**
   * 通过ICCID批量回收
   */
  recycleByIccids(data: { iccids: string[]; recycle_reason: string; remark?: string }) {
    return request.post('/stock/recycle/by-iccids', data)
  },

  /**
   * 获取回收记录
   */
  getRecycleRecords(params: any) {
    return request.get('/stock/recycle/records', { params })
  },

  // ============ 库存管理 ============

  /**
   * 获取库存统计
   */
  getSummary() {
    return request.get('/stock/summary')
  },

  /**
   * 获取库存卡片列表
   */
  getInventory(params: any) {
    return request.get('/stock/inventory', { params })
  },

  /**
   * 批量查询卡片
   */
  batchQuery(data: any) {
    return request.post('/stock/inventory/batch-query', data)
  },

  /**
   * 导出库存数据
   */
  exportInventory(params: any) {
    return request.post('/stock/inventory/export', params)
  },

  // ============ Excel模板 ============

  /**
   * 下载Excel导入模板
   */
  downloadTemplate() {
    return request.get('/stock/import-template', { responseType: 'blob' })
  }
}
