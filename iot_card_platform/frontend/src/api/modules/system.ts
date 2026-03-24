/**
 * 系统设置 API
 */
import request from '@/utils/request'

export const systemApi = {
  // ============ 系统配置 ============

  /** 获取所有系统配置 */
  getConfigs() {
    return request.get('/system/configs')
  },

  /** 获取公开配置 */
  getPublicConfigs() {
    return request.get('/system/configs/public')
  },

  /** 获取单个配置 */
  getConfig(configKey: string) {
    return request.get(`/system/configs/${configKey}`)
  },

  /** 创建配置 */
  createConfig(data: any) {
    return request.post('/system/configs', data)
  },

  /** 更新配置 */
  updateConfig(configKey: string, data: any) {
    return request.put(`/system/configs/${configKey}`, data)
  },

  /** 批量更新配置 */
  batchUpdateConfigs(data: any) {
    return request.put('/system/configs', data)
  },

  /** 删除配置 */
  deleteConfig(configKey: string) {
    return request.delete(`/system/configs/${configKey}`)
  },

  // ============ 登录日志 ============

  /** 获取登录日志 */
  getLoginLogs(params: any) {
    return request.get('/system/logs/login', { params })
  },

  // ============ 操作日志 ============

  /** 获取操作日志 */
  getOperationLogs(params: any) {
    return request.get('/system/logs/operation', { params })
  },

  /** 获取购买记录 */
  getPurchaseLogs(params: any) {
    return request.get('/system/logs/operation', {
      params: {
        ...params,
        module: 'orders'
      }
    })
  },

  /** 获取余额变动记录 */
  getBalanceLogs(params: any) {
    return request.get('/system/logs/operation', {
      params: {
        ...params,
        module: 'balance'
      }
    })
  },

  // ============ 告警规则 ============

  /** 获取告警规则 */
  getAlertRules() {
    return request.get('/system/alerts/rules')
  },

  /** 更新告警规则 */
  updateAlertRules(data: any) {
    return request.put('/system/alerts/rules', data)
  },

  // ============ 通知模板 ============

  /** 获取通知模板列表 */
  getNotifyTemplates(params: any) {
    return request.get('/system/notify/templates', { params })
  },

  /** 获取通知模板详情 */
  getNotifyTemplate(id: number) {
    return request.get(`/system/notify/templates/${id}`)
  },

  /** 创建通知模板 */
  createNotifyTemplate(data: any) {
    return request.post('/system/notify/templates', data)
  },

  /** 更新通知模板 */
  updateNotifyTemplate(id: number, data: any) {
    return request.put(`/system/notify/templates/${id}`, data)
  },

  /** 删除通知模板 */
  deleteNotifyTemplate(id: number) {
    return request.delete(`/system/notify/templates/${id}`)
  }
}
