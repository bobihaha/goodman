/**
 * 认证状态管理
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '@/api'
import { storage } from '@/utils/storage'
import type { User, LoginRequest } from '@/types/user'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string>(storage.get('access_token') || '')
  const refreshToken = ref<string>(storage.get('refresh_token') || '')
  const userInfo = ref<User | null>(null)

  // 是否已登录
  const isLoggedIn = ref<boolean>(!!token.value)

  // 登录
  const login = async (loginData: LoginRequest): Promise<void> => {
    try {
      const response = await authApi.login(loginData)
      
      // 保存 token
      token.value = response.access_token
      refreshToken.value = response.refresh_token
      storage.set('access_token', response.access_token)
      storage.set('refresh_token', response.refresh_token)
      
      // 保存用户信息
      userInfo.value = response.user
      isLoggedIn.value = true
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }

  // 登出
  const logout = async (): Promise<void> => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('登出失败:', error)
    } finally {
      // 清除本地数据
      token.value = ''
      refreshToken.value = ''
      userInfo.value = null
      isLoggedIn.value = false
      storage.remove('access_token')
      storage.remove('refresh_token')
    }
  }

  // 获取用户信息
  const getUserInfo = async (): Promise<void> => {
    try {
      const user = await authApi.getProfile()
      userInfo.value = user
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  }

  return {
    token,
    refreshToken,
    userInfo,
    isLoggedIn,
    login,
    logout,
    getUserInfo
  }
})



