/**
 * 用户管理 API
 */

import request from '@/utils/request'
import type { User, UserCreateRequest, UserUpdateRequest, UserListParams } from '@/types/user'
import type { PaginationResponse } from '@/types/common'

export const userApi = {
  /**
   * 获取用户列表
   */
  getList(params: UserListParams): Promise<PaginationResponse<User>> {
    return request.get<PaginationResponse<User>>('/users', { params })
  },

  /**
   * 获取用户详情
   */
  getDetail(id: number): Promise<User> {
    return request.get<User>(`/users/${id}`)
  },

  /**
   * 创建用户
   */
  create(data: UserCreateRequest): Promise<User> {
    return request.post<User>('/users', data)
  },

  /**
   * 更新用户
   */
  update(id: number, data: UserUpdateRequest): Promise<User> {
    return request.put<User>(`/users/${id}`, data)
  },

  /**
   * 删除用户
   */
  delete(id: number): Promise<void> {
    return request.delete<void>(`/users/${id}`)
  },

  /**
   * 修改用户状态
   */
  updateStatus(id: number, status: 'enable' | 'disable'): Promise<void> {
    return request.put<void>(`/users/${id}/status`, { status })
  },

  /**
   * 修改用户密码
   */
  updatePassword(id: number, password: string): Promise<void> {
    return request.put<void>(`/users/${id}/password`, { new_password: password })
  }
}

