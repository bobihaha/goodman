/**
 * 路由守卫
 */

import type { Router } from 'vue-router'
import { useAuthStore } from '@/stores'
import { ElMessage } from 'element-plus'

export function setupRouterGuards(router: Router): void {
  // 全局前置守卫
  router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore()

    // 设置页面标题
    if (to.meta.title) {
      document.title = `${to.meta.title} - ${import.meta.env.VITE_APP_TITLE}`
    }

    // 判断是否需要登录
    if (to.meta.requiresAuth) {
      if (authStore.isLoggedIn) {
        // 已登录，检查菜单权限
        if (to.path !== '/dashboard' && to.path !== '/') {
          // 确保菜单已加载
          if (!authStore.menus || authStore.menus.length === 0) {
            try {
              await authStore.loadUserMenus()
            } catch (error) {
              console.error('加载菜单失败:', error)
            }
          }

          // 检查用户是否有权限访问该路径
          const hasPermission = checkMenuPermission(authStore.menus, to.path)

          if (!hasPermission) {
            ElMessage.warning('您没有权限访问该页面')
            // 如果是从其他页面跳转过来的，返回上一页
            if (from.path !== '/') {
              next(false)
            } else {
              // 否则跳转到首页
              next('/dashboard')
            }
            return
          }
        }

        next()
      } else {
        // 未登录，跳转到登录页
        next({
          path: '/login',
          query: { redirect: to.fullPath }
        })
      }
    } else {
      // 如果已登录且访问登录页，跳转到首页
      if (to.path === '/login' && authStore.isLoggedIn) {
        next('/dashboard')
      } else {
        next()
      }
    }
  })

  // 全局后置钩子
  router.afterEach(() => {
    // 可以在这里添加页面加载完成后的逻辑
  })
}

/**
 * 详情页/子页面到父模块的路径映射
 * 当访问详情页时，检查用户是否有对应列表页的权限
 */
const DETAIL_TO_LIST_MAP: Record<string, string[]> = {
  '/cards/detail': ['/cards/list', '/card/list', '/card'],
  '/pools/detail': ['/pools/list', '/pool/list', '/pool'],
  '/records/purchases': ['/renewal/management']
}

/**
 * 检查菜单权限
 * @param menus 用户菜单列表
 * @param path 要访问的路径
 */
function checkMenuPermission(menus: any[], path: string): boolean {
  if (!menus || menus.length === 0) {
    return false
  }

  // 收集所有菜单路径（递归展平）
  function collectMenuPaths(menuList: any[]): string[] {
    const paths: string[] = []
    for (const menu of menuList) {
      if (menu.path) {
        paths.push(menu.path)
      }
      if (menu.children && menu.children.length > 0) {
        paths.push(...collectMenuPaths(menu.children))
      }
    }
    return paths
  }

  const allMenuPaths = collectMenuPaths(menus)

  // 直接匹配：精确匹配或前缀匹配
  if (allMenuPaths.some(mp => mp === path || path.startsWith(mp + '/'))) {
    return true
  }

  // 详情页/子页面匹配：检查是否属于已授权的父模块
  for (const [detailPrefix, parentPaths] of Object.entries(DETAIL_TO_LIST_MAP)) {
    if (path.startsWith(detailPrefix)) {
      if (parentPaths.some(pp => allMenuPaths.includes(pp))) {
        return true
      }
    }
  }

  return false
}
