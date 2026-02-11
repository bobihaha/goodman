/**
 * 全局指令注册
 */
import type { App } from 'vue'
import { permission, permissionAll } from './permission'

export function setupDirectives(app: App) {
  // 权限指令
  app.directive('permission', permission)
  app.directive('permission-all', permissionAll)
}


