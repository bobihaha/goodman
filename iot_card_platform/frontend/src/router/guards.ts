/**
 * 路由守卫
 */

import type { Router } from 'vue-router'
import { useAuthStore } from '@/stores'

export function setupRouterGuards(router: Router): void {
  // 全局前置守卫
  router.beforeEach((to, from, next) => {
    const authStore = useAuthStore()
    
    // 设置页面标题
    if (to.meta.title) {
      document.title = `${to.meta.title} - ${import.meta.env.VITE_APP_TITLE}`
    }

    // 判断是否需要登录
    if (to.meta.requiresAuth) {
      if (authStore.isLoggedIn) {
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



