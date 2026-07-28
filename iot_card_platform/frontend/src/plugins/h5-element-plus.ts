import type { App } from 'vue'
import {
  ElButton,
  ElCard,
  ElCollapse,
  ElCollapseItem,
  ElDialog,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElLoading,
  ElProgress,
  ElTag
} from 'element-plus'

import 'element-plus/theme-chalk/base.css'
import 'element-plus/theme-chalk/el-button.css'
import 'element-plus/theme-chalk/el-card.css'
import 'element-plus/theme-chalk/el-collapse.css'
import 'element-plus/theme-chalk/el-dialog.css'
import 'element-plus/theme-chalk/el-form.css'
import 'element-plus/theme-chalk/el-form-item.css'
import 'element-plus/theme-chalk/el-icon.css'
import 'element-plus/theme-chalk/el-input.css'
import 'element-plus/theme-chalk/el-loading.css'
import 'element-plus/theme-chalk/el-message.css'
import 'element-plus/theme-chalk/el-message-box.css'
import 'element-plus/theme-chalk/el-overlay.css'
import 'element-plus/theme-chalk/el-progress.css'
import 'element-plus/theme-chalk/el-tag.css'

const components = [
  ElButton,
  ElCard,
  ElCollapse,
  ElCollapseItem,
  ElDialog,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElProgress,
  ElTag
]

export const setupH5ElementPlus = (app: App) => {
  components.forEach(component => app.use(component))
  app.use(ElLoading)
}
