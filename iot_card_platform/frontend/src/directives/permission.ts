import type { Directive, DirectiveBinding } from 'vue'
import { useAuthStore } from '@/stores/modules/auth'

/**
 * 权限指令
 * 用法：v-permission="'card:view'" 或 v-permission="['card:view', 'card:edit']"
 */
export const permission: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    const { value } = binding
    const authStore = useAuthStore()
    const userPermissions = authStore.permissions || []

    if (value) {
      let hasPermission = false

      if (Array.isArray(value)) {
        // 数组：需要拥有其中任意一个权限
        hasPermission = value.some(permission => userPermissions.includes(permission))
      } else if (typeof value === 'string') {
        // 字符串：需要拥有该权限
        hasPermission = userPermissions.includes(value)
      }

      if (!hasPermission) {
        // 没有权限，移除元素
        el.parentNode?.removeChild(el)
      }
    }
  }
}

/**
 * 权限指令（严格模式）
 * 用法：v-permission-all="['card:view', 'card:edit']"
 * 需要同时拥有所有权限
 */
export const permissionAll: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    const { value } = binding
    const authStore = useAuthStore()
    const userPermissions = authStore.permissions || []

    if (value && Array.isArray(value)) {
      const hasPermission = value.every(permission => userPermissions.includes(permission))

      if (!hasPermission) {
        // 没有权限，移除元素
        el.parentNode?.removeChild(el)
      }
    }
  }
}

export default {
  permission,
  permissionAll
}


