/**
 * 应用入口文件
 */

import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import '@/assets/styles/global.scss'

const isH5Route = /^\/h5\/[^/]+\/?$/.test(window.location.pathname)

const bootstrap = async () => {
  const app = createApp(App)

  if (isH5Route) {
    const [{ setupH5ElementPlus }] = await Promise.all([
      import('@/plugins/h5-element-plus'),
      import('@/views/h5/index.vue')
    ])
    setupH5ElementPlus(app)
  } else {
    const [
      { createPinia },
      { default: ElementPlus },
      { default: zhCn },
      { setupDirectives },
      { setupRouterGuards }
    ] = await Promise.all([
      import('pinia'),
      import('element-plus'),
      import('element-plus/es/locale/lang/zh-cn'),
      import('@/directives'),
      import('@/router/guards'),
      import('element-plus/dist/index.css'),
      import('element-plus/theme-chalk/dark/css-vars.css')
    ])

    app.use(createPinia())
    setupRouterGuards(router)
    app.use(ElementPlus, {
      locale: zhCn,
      size: 'default'
    })
    setupDirectives(app)
  }

  app.use(router)
  app.mount('#app')
}

void bootstrap()
