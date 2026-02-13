/**
 * 权限管理类型定义
 */

// 权限对象
export interface Permission {
  id: number
  code: string
  name: string
  module: string
  module_name: string
  description?: string
  created_at: string
  updated_at: string
}

// 权限模块
export interface PermissionModule {
  module: string
  module_name: string
  permissions: Permission[]
}

// 用户权限关联
export interface UserPermission {
  id: number
  user_id: number
  permission_id: number
  permission?: Permission
  assigned_at: string
  assigned_by?: number
}

// 权限列表查询参数
export interface PermissionListParams {
  page?: number
  page_size?: number
  module?: string
  keyword?: string
}

// 权限列表响应
export interface PermissionListResponse {
  items: Permission[]
  total: number
  page: number
  page_size: number
  pages: number
}





