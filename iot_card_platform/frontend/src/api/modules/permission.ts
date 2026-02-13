import request from '@/utils/request'
import type { 
  Permission, 
  PermissionModule, 
  UserPermission,
  PermissionListParams,
  PermissionListResponse 
} from '@/types/permission'

/**
 * 权限管理 API
 */

// 获取权限列表（分页）
export const getPermissionList = (params: PermissionListParams) => {
  return request.get<PermissionListResponse>('/permissions', { params })
}

// 获取所有权限（不分页）
export const getAllPermissions = () => {
  return request.get<Permission[]>('/permissions/all')
}

// 按模块分组获取权限
export const getPermissionsByModule = () => {
  return request.get<PermissionModule[]>('/permissions/modules')
}

// 获取单个权限详情
export const getPermissionDetail = (id: number) => {
  return request.get<Permission>(`/permissions/${id}`)
}

// 创建权限
export const createPermission = (data: Partial<Permission>) => {
  return request.post<Permission>('/permissions', data)
}

// 更新权限
export const updatePermission = (id: number, data: Partial<Permission>) => {
  return request.put<Permission>(`/permissions/${id}`, data)
}

// 删除权限
export const deletePermission = (id: number) => {
  return request.delete(`/permissions/${id}`)
}

// 获取用户权限列表
export const getUserPermissions = (userId: number) => {
  return request.get<UserPermission[]>(`/permissions/user/${userId}`)
}

// 获取用户权限ID列表
export const getUserPermissionIds = (userId: number) => {
  return request.get<number[]>(`/permissions/user/${userId}/ids`)
}

// 获取用户权限代码列表
export const getUserPermissionCodes = (userId: number) => {
  return request.get<string[]>(`/permissions/user/${userId}/codes`)
}

// 分配用户权限（覆盖）
export const assignUserPermissions = (userId: number, permissionIds: number[]) => {
  return request.post(`/permissions/user/${userId}/assign`, { permission_ids: permissionIds })
}

// 添加用户权限（追加）
export const addUserPermissions = (userId: number, permissionIds: number[]) => {
  return request.post(`/permissions/user/${userId}/add`, { permission_ids: permissionIds })
}

// 移除用户权限
export const removeUserPermissions = (userId: number, permissionIds: number[]) => {
  return request.post(`/permissions/user/${userId}/remove`, { permission_ids: permissionIds })
}

// 检查用户是否拥有某个权限
export const checkUserPermission = (userId: number, permissionCode: string) => {
  return request.get<boolean>(`/permissions/user/${userId}/check/${permissionCode}`)
}





