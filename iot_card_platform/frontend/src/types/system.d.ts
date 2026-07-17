/**
 * 系统设置相关类型定义
 */

/** 系统配置 */
export interface SystemConfig {
  id: number
  config_key: string
  config_value: string | null
  config_type: string // string/number/json/boolean
  description: string | null
  is_public: boolean
  created_at: string | null
  updated_at: string | null
}

/** 创建配置参数 */
export interface ConfigCreateParams {
  config_key: string
  config_value?: string
  config_type?: string
  description?: string
  is_public?: boolean
}

/** 更新配置参数 */
export interface ConfigUpdateParams {
  config_value?: string
  description?: string
  is_public?: boolean
}

/** 登录日志 */
export interface LoginLog {
  id: number
  user_id: number | null
  account: string | null
  login_type: string | null
  login_type_name: string | null
  operator_id: number | null
  is_success: boolean
  fail_reason: string | null
  ip: string | null
  user_agent: string | null
  created_at: string | null
}

/** 登录日志查询参数 */
export interface LoginLogParams {
  user_id?: number
  account?: string
  is_success?: boolean
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

/** 操作日志 */
export interface OperationLog {
  id: number
  user_id: number | null
  user_name: string | null
  original_user_id: number | null
  module: string
  action: string
  target_type: string | null
  target_id: number | null
  target_name: string | null
  detail: string | null
  ip: string | null
  is_success: boolean
  error_msg: string | null
  created_at: string | null
}

/** 操作日志查询参数 */
export interface OperationLogParams {
  user_id?: number
  module?: string
  action?: string
  target_type?: string
  is_success?: boolean
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

/** 告警规则 */
export interface AlertRules {
  warning_threshold: number
  critical_threshold: number
  stop_threshold: number
  expired_days: number
  auto_suspend: boolean
  auto_notify: boolean
}

/** 更新告警规则参数 */
export interface AlertRulesUpdateParams {
  warning_threshold?: number
  critical_threshold?: number
  stop_threshold?: number
  expired_days?: number
  auto_suspend?: boolean
  auto_notify?: boolean
}

/** 通知模板 */
export interface NotifyTemplate {
  id: number
  code: string
  name: string
  type: string
  type_name: string
  title: string | null
  content: string
  variables: string[]
  is_enabled: boolean
  remark: string | null
  created_by: number | null
  created_at: string | null
  updated_at: string | null
}

/** 创建通知模板参数 */
export interface NotifyTemplateCreateParams {
  code: string
  name: string
  type: string
  title?: string
  content: string
  variables?: string[]
  is_enabled?: boolean
  remark?: string
}

/** 更新通知模板参数 */
export interface NotifyTemplateUpdateParams {
  name?: string
  title?: string
  content?: string
  variables?: string[]
  is_enabled?: boolean
  remark?: string
}

/** 通知模板查询参数 */
export interface NotifyTemplateParams {
  type?: string
  is_enabled?: boolean
  keyword?: string
  page?: number
  page_size?: number
}
