/**
 * 用户相关类型定义
 */

import type { UserStatus } from './common'

// 用户信息（与后端数据库字段对应）
export interface User {
  id: number
  account: string       // 账号
  name: string          // 姓名
  phone?: string        // 手机号
  email?: string        // 邮箱
  parent_id?: number    // 父级用户ID
  status: UserStatus    // 状态：enable/disable
  remark?: string       // 备注
  alert_notify?: {      // 告警通知设置
    sms: boolean
    email: boolean
  }
  quota?: {             // 配额设置
    max_cards: number
    max_sub_users: number
  }
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
  }
  remark?: string
  status?: UserStatus
}

// 用户列表查询参数
export interface UserListParams {
  page?: number
  page_size?: number
  keyword?: string      // 关键词搜索（账号、姓名、手机号）
  status?: UserStatus   // 状态筛选
}

// 用户权限
export type Permission = string

// 用户菜单
export interface Menu {
  id: string
  name: string
  path: string
  icon?: string
  children?: Menu[]
}
