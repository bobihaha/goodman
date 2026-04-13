/**
 * 用户相关类型定义
 */

import type { UserStatus } from './common'

export interface UserH5Config {
  enabled: boolean
  slug?: string
  title?: string
  logo?: string
  banner?: string
  notice?: string
  contact_phone?: string
  contact_wechat?: string
  theme?: Record<string, any>
  allow_suspend: boolean
  allow_resume: boolean
  allow_remark: boolean
  require_verify: boolean
  status: 'enabled' | 'disabled' | 'expired'
  last_reset_at?: string
}

export interface UserOpenApiCredential {
  enabled: boolean
  app_id?: string
  app_secret_masked?: string
  has_app_secret: boolean
  last_reset_at?: string
}

export interface UserOpenApiCredentialResetResponse {
  enabled: boolean
  app_id: string
  app_secret: string
  last_reset_at: string
}

// 用户信息（与后端数据库字段对应）
export interface User {
  id: number
  account: string       // 账号
  name: string          // 姓名
  phone?: string        // 手机号
  email?: string        // 邮箱
  avatar?: string       // 头像
  parent_id?: number    // 父级用户ID
  user_level: number    // 用户级别：1-超管，2-用户，3-子用户
  status: UserStatus    // 状态：enable/disable
  remark?: string       // 备注
  alert_notify?: {      // 告警通知设置
    sms: boolean
    email: boolean
  }
  quota?: {             // 配额设置
    max_cards: number
    max_sub_users: number
    pool_stop_threshold?: number  // 流量池停卡阈值(%)，如120表示用量达120%时全池停卡
    account_balance?: number
    balance_alert_threshold?: number
    last_grant_at?: string
    last_grant_amount?: number
  }
  permissions?: string[]     // 用户权限列表
  h5?: UserH5Config
  open_api?: UserOpenApiCredential
  is_super_login?: boolean   // 是否超级登录模式
  original_user_id?: number  // 原用户ID（超级登录时）
  created_at: string
  updated_at?: string
}

// 登录请求（后端期望的字段）
export interface LoginRequest {
  account: string       // 后端字段是 account
  password: string
}

// 登录响应
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

// 创建用户请求
export interface UserCreateRequest {
  name: string          // 姓名（必填）
  account: string       // 账号（必填）
  password: string      // 密码（必填）
  phone?: string        // 手机号（可选）
  email?: string        // 邮箱（可选）
  alert_notify?: {      // 告警通知设置
    sms: boolean
    email: boolean
  }
  quota?: {             // 配额设置
    max_cards: number
    max_sub_users: number
    pool_stop_threshold?: number  // 流量池停卡阈值(%)
    account_balance?: number
    balance_alert_threshold?: number
  }
  remark?: string       // 备注
  status?: UserStatus   // 状态（默认enable）
}

// 更新用户请求
export interface UserUpdateRequest {
  name?: string
  phone?: string
  email?: string
  alert_notify?: {
    sms: boolean
    email: boolean
  }
  quota?: {
    max_cards: number
    max_sub_users: number
    pool_stop_threshold?: number  // 流量池停卡阈值(%)
    account_balance?: number
    balance_alert_threshold?: number
  }
  remark?: string
  status?: UserStatus
}

export interface UserH5ConfigUpdateRequest {
  title?: string
  logo?: string
  banner?: string
  notice?: string
  contact_phone?: string
  contact_wechat?: string
  theme?: Record<string, any>
  allow_suspend?: boolean
  allow_resume?: boolean
  allow_remark?: boolean
  require_verify?: boolean
  status?: 'enabled' | 'disabled' | 'expired'
}

// 用户列表查询参数
export interface UserListParams {
  page?: number
  page_size?: number
  keyword?: string      // 关键词搜索（账号、姓名、手机号）
  status?: UserStatus   // 状态筛选
  user_level?: number   // 用户级别筛选
}

// 用户权限
export type Permission = string

// 用户菜单（与后端sys_menus表对应）
export interface Menu {
  id: number
  parent_id: number
  user_level: number
  code: string
  name: string
  type: 'directory' | 'menu' | 'button'
  icon?: string
  path?: string
  component?: string
  permission?: string
  sort_order: number
  is_visible?: number
  status?: string
  children?: Menu[]
}
