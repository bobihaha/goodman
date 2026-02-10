# 物联网卡管理平台 - 前端项目

基于 Vue 3 + TypeScript + Element Plus 的现代化物联网卡管理系统前端。

## 技术栈

- **框架**: Vue 3.4+ (Composition API + `<script setup>`)
- **语言**: TypeScript 5.x (严格模式)
- **UI 组件**: Element Plus 2.5+
- **状态管理**: Pinia 2.1+
- **路由**: Vue Router 4.x
- **HTTP 客户端**: Axios 1.6+
- **构建工具**: Vite 5.x
- **样式**: SCSS
- **工具库**: @vueuse/core, dayjs

## 项目结构

```
frontend/
├── src/
│   ├── api/                    # API 接口
│   │   └── modules/            # 按模块划分的 API
│   ├── assets/                 # 静态资源
│   │   └── styles/             # 全局样式
│   ├── components/             # 组件
│   │   ├── common/             # 通用组件
│   │   ├── layout/             # 布局组件
│   │   └── business/           # 业务组件
│   ├── composables/            # 组合式函数
│   ├── directives/             # 自定义指令
│   ├── router/                 # 路由配置
│   ├── stores/                 # Pinia 状态管理
│   │   └── modules/            # 按模块划分的 Store
│   ├── types/                  # TypeScript 类型定义
│   ├── utils/                  # 工具函数
│   ├── views/                  # 页面视图
│   ├── App.vue                 # 根组件
│   └── main.ts                 # 入口文件
├── .env.development            # 开发环境变量
├── .env.production             # 生产环境变量
├── index.html                  # HTML 模板
├── package.json                # 项目依赖
├── tsconfig.json               # TypeScript 配置
└── vite.config.ts              # Vite 配置
```

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## 环境变量

### 开发环境 (.env.development)

```
VITE_APP_TITLE=物联网卡管理平台
VITE_API_BASE_URL=/api/v1
VITE_APP_PORT=3000
```

### 生产环境 (.env.production)

```
VITE_APP_TITLE=物联网卡管理平台
VITE_API_BASE_URL=/api/v1
```

## 已完成功能

### ✅ Phase 0: 项目初始化
- [x] Vue 3 + TypeScript + Vite 项目搭建
- [x] Element Plus UI 组件库集成
- [x] Vue Router 路由配置
- [x] Pinia 状态管理
- [x] Axios 请求封装（含拦截器、错误处理）
- [x] TypeScript 严格模式配置
- [x] 全局样式和主题配置

### ✅ Phase 1: 登录模块
- [x] 登录页面 UI（美观的渐变背景）
- [x] 表单验证（用户名、密码）
- [x] 登录 API 对接
- [x] Token 存储和管理
- [x] 路由守卫（登录验证）
- [x] 自动跳转功能

### ✅ Phase 2: 仪表盘模块
- [x] 仪表盘页面布局
- [x] 统计卡片组件（卡片总数、流量池、用户、告警）
- [x] 运营商卡片分布统计
- [x] 账户余额显示（含预警提示）
- [x] 本月到期卡明细（表格展示）
- [x] 超套餐用量卡明细（表格展示）
- [x] 流量池用量实时百分比（进度条展示）
- [x] 告警消息列表
- [x] 数据格式化工具（日期、流量、金额等）
- [x] 响应式布局

## 开发规范

### 代码规范

1. **TypeScript 严格模式**：禁止使用 `any`，所有变量必须明确类型
2. **组件命名**：PascalCase（如 `StatCard.vue`）
3. **文件命名**：kebab-case（如 `user-list.ts`）
4. **变量/函数命名**：camelCase（如 `getUserList`）
5. **常量命名**：UPPER_SNAKE_CASE（如 `API_BASE_URL`）

### 组件开发规范

```vue
<template>
  <!-- 模板内容 -->
</template>

<script setup lang="ts">
// 1. 导入依赖
import { ref, computed, onMounted } from 'vue'

// 2. 定义 Props 和 Emits
interface Props {
  title: string
}
const props = defineProps<Props>()

// 3. 响应式数据
const loading = ref(false)

// 4. 计算属性
const displayTitle = computed(() => props.title)

// 5. 方法
const handleClick = () => {
  // 处理逻辑
}

// 6. 生命周期
onMounted(() => {
  // 初始化逻辑
})
</script>

<style scoped lang="scss">
// 样式
</style>
```

### API 调用规范

```typescript
// ✅ 正确：使用 try-catch + loading 状态
const fetchData = async () => {
  loading.value = true
  try {
    const data = await api.getData()
    list.value = data
  } catch (error) {
    console.error('获取数据失败:', error)
    // 错误已在 request.ts 中统一处理
  } finally {
    loading.value = false
  }
}
```

## 注意事项

1. **禁止使用 Mock 数据**：所有数据必须通过后端 API 获取
2. **错误处理**：所有 API 调用必须有 try-catch
3. **加载状态**：所有异步操作必须有 loading 状态
4. **类型安全**：禁止使用 `any`，必须明确类型定义
5. **代码复用**：相同逻辑抽取为组合式函数（composables）

## 测试账号

开发环境测试账号（需要后端配置）：

```
用户名: admin
密码: admin123
```

## 浏览器支持

- Chrome 90+
- Edge 90+
- Firefox 88+
- Safari 14+

## 下一步开发计划

- [ ] 主布局框架（侧边栏、顶部栏、面包屑）
- [ ] 用户管理模块
- [ ] 套餐管理模块
- [ ] 库存管理模块
- [ ] 卡片管理模块
- [ ] 流量池管理模块
- [ ] 停卡管理模块
- [ ] 系统设置模块

## 问题反馈

如遇到问题，请检查：

1. Node.js 版本是否 >= 16
2. 依赖是否正确安装
3. 后端服务是否启动（http://localhost:8000）
4. 环境变量是否正确配置

## License

Copyright © 2026 物联网卡管理平台
