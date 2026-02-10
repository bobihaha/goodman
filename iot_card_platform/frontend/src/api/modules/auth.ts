/**
 * 认证相关 API
 */

import { post, get } from '@/utils/request'
import type { LoginRequest, LoginResponse, User } from '@/types/user'

export const authApi = {
  // 登录
  login(data: LoginRequest): Promise<LoginResponse> {
    return post<LoginResponse>('/auth/login', data)
  },

  // 登出
  logout(): Promise<void> {
    return post<void>('/auth/logout')
  },

  // 获取当前用户信息
  getProfile(): Promise<User> {
    return get<User>('/auth/profile')
  },

  // 刷新 Token
  refreshToken(refreshToken: string): Promise<{ access_token: string }> {
    return post<{ access_token: string }>('/auth/refresh', { refresh_token: refreshToken })
  }
}



