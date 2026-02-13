/**
 * 认证状态管理
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi, menuApi } from '@/api'
import { storage } from '@/utils/storage'
import type { User, LoginRequest, Menu } from '@/types/user'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string>(storage.get('access_token') || '')
  const refreshToken = ref<string>(storage.get('refresh_token') || '')
  const userInfo = ref<User | null>(null)
  const permissions = ref<string[]>([])
  const menus = ref<Menu[]>([])

  // 是否已登录
  const isLoggedIn = ref<boolean>(!!token.value)

  // 是否超级登录模式
  const isSuperLogin = ref<boolean>(false)
  const originalUserInfo = ref<User | null>(null)

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
      permissions.value = response.user.permissions || []
      isLoggedIn.value = true
      isSuperLogin.value = false
      originalUserInfo.value = null

      // 加载用户菜单
      await loadUserMenus()
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }

  // 超级登录
  const superLogin = async (targetUserId: number): Promise<void> => {
    try {
      // 保存原用户信息
      if (userInfo.value && !isSuperLogin.value) {
        originalUserInfo.value = { ...userInfo.value }
        storage.set('original_user_info', JSON.stringify(originalUserInfo.value))
        storage.set('original_access_token', token.value)
        storage.set('original_refresh_token', refreshToken.value)
      }

      const response = await authApi.superLogin(targetUserId)
      
      // 更新 token
      token.value = response.access_token
      refreshToken.value = response.refresh_token
      storage.set('access_token', response.access_token)
      storage.set('refresh_token', response.refresh_token)
      
      // 更新用户信息
      userInfo.value = response.user
      permissions.value = response.user.permissions || []
      isSuperLogin.value = true

      // 加载目标用户的菜单
      await loadUserMenus()
    } catch (error) {
      console.error('超级登录失败:', error)
      throw error
    }
  }

  // 退出超级登录
  const exitSuperLogin = async (): Promise<void> => {
    try {
      const response = await authApi.exitSuperLogin()
      
      // 更新 token
      token.value = response.access_token
      refreshToken.value = response.refresh_token
      storage.set('access_token', response.access_token)
      storage.set('refresh_token', response.refresh_token)
      
      // 恢复原用户信息
      userInfo.value = response.user
      permissions.value = response.user.permissions || []
      isSuperLogin.value = false
      originalUserInfo.value = null
      
      // 清除保存的原用户信息
      storage.remove('original_user_info')
      storage.remove('original_access_token')
      storage.remove('original_refresh_token')

      // 重新加载原用户的菜单
      await loadUserMenus()
    } catch (error) {
      console.error('退出超级登录失败:', error)
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
      permissions.value = []
      menus.value = []
      isLoggedIn.value = false
      isSuperLogin.value = false
      originalUserInfo.value = null
      storage.remove('access_token')
      storage.remove('refresh_token')
      storage.remove('original_user_info')
      storage.remove('original_access_token')
      storage.remove('original_refresh_token')
    }
  }

  // 获取用户信息
  const getUserInfo = async (): Promise<void> => {
    try {
      const user = await authApi.getProfile()
      userInfo.value = user
      permissions.value = user.permissions || []
      isSuperLogin.value = user.is_super_login || false
      
      // 如果是超级登录模式，尝试恢复原用户信息
      if (isSuperLogin.value) {
        const savedOriginalUser = storage.get('original_user_info')
        if (savedOriginalUser) {
          originalUserInfo.value = JSON.parse(savedOriginalUser)
        }
      }

      // 获取用户菜单
      await loadUserMenus()
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  }

  // 加载用户菜单
  const loadUserMenus = async (): Promise<void> => {
    if (!userInfo.value) {
      console.warn('用户信息为空，无法加载菜单')
      return
    }
    
    console.log('开始加载用户菜单，用户ID:', userInfo.value.id)
    
    try {
      // 获取用户的菜单ID列表
      console.log('调用 getUserMenuIds，参数:', userInfo.value.id)
      const menuIds = await menuApi.getUserMenuIds(userInfo.value.id)
      console.log('用户菜单ID列表:', menuIds)
      
      // 获取所有菜单
      const allMenus = await menuApi.getAllMenus()
      console.log('所有菜单:', allMenus)
      
      // 过滤出用户有权限的菜单
      const userMenus = allMenus.filter(menu => menuIds.includes(menu.id))
      console.log('用户有权限的菜单:', userMenus)
      
      // 构建菜单树
      menus.value = buildMenuTree(userMenus)
      console.log('构建的菜单树:', menus.value)
    } catch (error: any) {
      console.error('加载用户菜单失败:', error)
      console.error('错误详情:', error.response?.data || error.message)
      // 如果加载失败，使用空菜单
      menus.value = []
    }
  }

  // 构建菜单树
  const buildMenuTree = (menuList: Menu[]): Menu[] => {
    const menuMap = new Map<number, Menu>()
    const rootMenus: Menu[] = []

    // 先将所有菜单放入Map
    menuList.forEach(menu => {
      menuMap.set(menu.id, { ...menu, children: [] })
    })

    // 构建树形结构
    menuList.forEach(menu => {
      const menuItem = menuMap.get(menu.id)
      if (!menuItem) return

      if (menu.parent_id === 0) {
        // 根菜单
        rootMenus.push(menuItem)
      } else {
        // 子菜单
        const parent = menuMap.get(menu.parent_id)
        if (parent) {
          if (!parent.children) {
            parent.children = []
          }
          parent.children.push(menuItem)
        }
      }
    })

    return rootMenus
  }

  // 检查权限
  const hasPermission = (permission: string | string[]): boolean => {
    if (!permissions.value || permissions.value.length === 0) {
      return false
    }
    
    if (Array.isArray(permission)) {
      return permission.some(p => permissions.value.includes(p))
    }
    
    return permissions.value.includes(permission)
  }

  return {
    token,
    refreshToken,
    userInfo,
    permissions,
    menus,
    isLoggedIn,
    isSuperLogin,
    originalUserInfo,
    login,
    superLogin,
    exitSuperLogin,
    logout,
    getUserInfo,
    loadUserMenus,
    hasPermission
  }
})
