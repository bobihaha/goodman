/**
 * 菜单相关 API
 */

import { get, put } from '@/utils/request'
import type { Menu } from '@/types/user'

export const menuApi = {
  // 获取所有菜单列表（超级管理员）
  getAllMenus(): Promise<Menu[]> {
    return get<Menu[]>('/menus')
  },

  // 获取用户的菜单ID列表
  getUserMenuIds(userId: number): Promise<number[]> {
    return get<number[]>(`/menus/user/${userId}`)
  },

  // 设置用户菜单权限
  setUserMenus(userId: number, menuIds: number[]): Promise<void> {
    return put<void>(`/menus/user/${userId}`, menuIds)
  }
}
