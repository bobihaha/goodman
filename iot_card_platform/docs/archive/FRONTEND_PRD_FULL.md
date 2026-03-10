# 物联网卡管理平台 - 前端PRD文档（优化版）

> **优化目标**：稳定少bug、交互友好、用户体验优先

---

## ⚠️ 重要规则（必读）

### 🚫 严禁使用模拟数据（Mock Data）

**强制要求**：
1. ❌ **禁止**在代码中硬编码任何业务数据
2. ❌ **禁止**使用 Mock.js 或任何模拟数据工具
3. ❌ **禁止**在组件中写死测试数据
4. ✅ **必须**所有数据通过后端API获取
5. ✅ **必须**确保后端API可用后再开发对应前端功能
6. ✅ **必须**使用真实的API响应数据结构
7. ✅ **必须**前端代码字段名称格式等要和后端一致
8. ✅ **必须**原则上不许修改后端代码，可以询问得到许可在修改

**违规示例（禁止）**：
```typescript
// ❌ 错误：硬编码数据
const cardList = [
  { iccid: '89860123456789012345', status: 'activated' },
  { iccid: '89860123456789012346', status: 'silent' }
]

// ❌ 错误：使用Mock数据
import Mock from 'mockjs'
Mock.mock('/api/cards', { data: [...] })
```

**正确示例（必须）**：
```typescript
// ✅ 正确：从API获取数据
const { data: cardList } = await cardApi.getList()

// ✅ 正确：处理加载和错误状态
const loading = ref(false)
const fetchData = async () => {
  loading.value = true
  try {
    const data = await cardApi.getList()
    cardList.value = data
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}
```

**开发流程**：
1. 先确认后端API已开发完成
2. 查看API文档，确认请求/响应格式
3. 使用Postman/Apifox测试API
4. 前端对接真实API
5. 处理加载、错误、空状态

---

## 📌 项目概述

基于 **Vue 3.4+ / TypeScript 5.x / Element Plus** 的物联网卡管理平台前端，支持三级多租户 SaaS 架构。

### 🔄 卡片状态自动更新机制 (2026-03-04 新增)

**功能说明**：系统通过定时任务自动同步供应商流量数据，并在同步时自动更新卡片状态和日期。

**自动转换规则**：
1. **testing → silent**：当前日期 > test_expire_date
2. **testing/silent → activated**：检测到流量使用（data_used > 0）
   - 自动设置 activated_at = 当前日期
   - 自动计算 expired_at = activated_at + 套餐周期
3. **activated → suspended**：当前日期 > expired_at（到期停机）
4. **修复规则**：已激活但缺少日期的卡片自动补全日期
5. **沉默期超期规则** (2026-03-06 修复)：当前日期 > silent_expire_date 且有流量使用 → 自动转为 activated

**同步间隔配置**：
- 供应商管理页面可设置同步间隔（单位：分钟）
- 默认值：60分钟
- 支持随时修改，自动重新加载定时任务

**前端显示**：
- 激活日期（activated_at）和到期日期（expired_at）自动显示
- 日期格式：26/1/31
- 过期日期显示为红色

**已知问题修复** (2026-03-06)：
- 修复生命周期同步时未调用状态检查逻辑，导致超沉默期卡片状态未及时更新为已激活的问题
- 修复销售套餐编辑时专属客户字段显示为空的问题（异步加载客户信息时序问题）
- 修复销售套餐创建 500 错误（后端 schema 缺少 user_id 字段）
- 修复出库权限漏洞（超级管理员给用户 B 出库时可选用户 A 的专属套餐）
- 新增销售套餐客户搜索功能（按客户名称/账户筛选套餐）
- 修复卡片划拨 422 错误（前后端字段名不一致：target_user_id vs to_user_id）
- 新增卡片划拨权限校验（验证目标用户存在且为直属子用户）
- 代码质量优化（类型安全、错误处理、重置逻辑完善）

**技术栈**：
- Vue 3.4+ (Composition API + `<script setup>`)
- TypeScript 5.x (严格模式)
- Element Plus 2.5+ (UI组件库)
- Pinia 2.1+ (状态管理)
- Vue Router 4.x (路由管理)
- Axios 1.6+ (HTTP请求)
- Vite 5.x (构建工具)
- ECharts 5.4+ (数据可视化)
- VueUse 10.7+ (组合式工具库)
- Day.js 1.11+ (日期处理)

**核心优化策略**：
1. ✅ **类型安全**：100% TypeScript覆盖，杜绝any
2. ✅ **错误边界**：全局错误捕获 + 组件级错误处理
3. ✅ **防抖节流**：所有搜索/提交操作防抖
4. ✅ **乐观更新**：关键操作即时反馈
5. ✅ **离线提示**：网络状态监控
6. ✅ **数据校验**：前后端双重验证
7. ✅ **加载状态**：骨架屏 + 进度条
8. ✅ **空状态设计**：友好的空数据提示

---

## 🎨 设计原则（优化版）

### 视觉设计
- **主题色**：
  - 主色：#1890ff (蓝色，专业稳重)
  - 成功：#52c41a (绿色)
  - 警告：#faad14 (橙色)
  - 危险：#ff4d4f (红色)
  - 信息：#1890ff (蓝色)
- **字体**：
  - 标题：-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei'
  - 正文：同上（系统字体优先，性能更好）
  - 代码/ICCID：'Monaco', 'Menlo', 'Consolas', monospace
- **布局**：
  - 侧边栏宽度：200px（收起）/ 240px（展开）
  - 内容区最大宽度：1600px（居中）
  - 卡片间距：16px
  - 表单标签宽度：120px

### 交互原则（用户体验优先）

#### 1. 防错设计
- ✅ 危险操作二次确认（停卡、批量操作）
- ✅ 表单离开前未保存提示
- ✅ 批量操作前显示影响范围
- ✅ 输入框实时校验 + 错误提示
- ✅ 禁用状态明确提示原因

#### 2. 反馈机制
- ✅ 操作成功：Toast提示（3秒自动关闭）
- ✅ 操作失败：详细错误信息 + 解决建议
- ✅ 加载状态：骨架屏（首次）+ Spin（刷新）
- ✅ 进度反馈：上传/导入显示进度条
- ✅ 乐观更新：立即更新UI，失败后回滚

#### 3. 性能优化
- ✅ 表格虚拟滚动（>100条数据）
- ✅ 图片懒加载
- ✅ 路由懒加载
- ✅ 防抖：搜索（500ms）、窗口resize（300ms）
- ✅ 节流：滚动事件（100ms）
- ✅ 请求取消：切换页面取消未完成请求

#### 4. 易用性
- ✅ 快捷键：Ctrl+K（全局搜索）、Ctrl+R（刷新）、Esc（关闭弹窗）
- ✅ 记住筛选条件（localStorage）
- ✅ 表格列宽可调整 + 记忆
- ✅ 批量操作支持全选/反选/跨页选择
- ✅ 导出前预览数据范围

#### 5. 容错处理
- ✅ 网络断开提示 + 自动重连
- ✅ Token过期自动刷新
- ✅ API错误统一处理
- ✅ 组件渲染错误边界
- ✅ 空状态友好提示

---

## 🏗️ 系统架构（优化版）

```
┌─────────────────────────────────────────────────────────────────┐
│                     前端应用架构（分层设计）                      │
├─────────────────────────────────────────────────────────────────┤
│  视图层 (Views) - 页面组件                                       │
│  ├── 登录页 (防暴力破解：验证码 + 登录限制)                       │
│  ├── 仪表盘 (数据缓存 + 自动刷新)                                │
│  ├── 用户管理 (树形结构 + 权限可视化)                             │
│  ├── 套餐管理 (规格标准化展示)                                    │
│  ├── 出入库管理 (批量导入 + 进度反馈)                             │
│  ├── 卡片管理 (虚拟滚动 + 高级筛选)                               │
│  ├── 流量池管理 (实时用量 + 告警提示)                             │
│  ├── 停卡管理 (操作确认 + 原因记录)                               │
│  └── 系统设置 (配置校验 + 日志查询)                               │
├─────────────────────────────────────────────────────────────────┤
│  组件层 (Components) - 可复用组件                                │
│  ├── 布局组件 (Layout/Sidebar/Header/Breadcrumb)                │
│  ├── 业务组件 (CardTable/PoolChart/UserSelector)                │
│  ├── 表单组件 (FormDialog/SearchBar/FilterPanel)                │
│  └── 通用组件 (DataTable/StatusTag/EmptyState/ErrorBoundary)    │
├─────────────────────────────────────────────────────────────────┤
│  状态管理 (Pinia Stores) - 全局状态                              │
│  ├── authStore (认证状态/Token管理/权限缓存)                      │
│  ├── appStore (应用配置/主题/网络状态/全局Loading)                │
│  ├── userStore (用户列表/当前用户/菜单权限)                       │
│  ├── cardStore (卡片列表/筛选条件/选中项)                         │
│  └── poolStore (流量池列表/用量统计)                              │
├─────────────────────────────────────────────────────────────────┤
│  路由层 (Vue Router) - 路由管理                                  │
│  ├── 路由守卫 (登录验证/权限校验/页面标题)                        │
│  ├── 动态路由 (根据用户权限动态加载)                              │
│  ├── 路由懒加载 (按需加载页面组件)                                │
│  └── 路由缓存 (keep-alive优化)                                   │
├─────────────────────────────────────────────────────────────────┤
│  服务层 (API Services) - 接口封装                                │
│  ├── authApi (登录/登出/刷新Token/超级登录)                       │
│  ├── userApi (用户CRUD/权限管理)                                 │
│  ├── cardApi (卡片查询/划拨/备注/导出)                            │
│  ├── poolApi (流量池CRUD/添加移除卡片)                            │
│  ├── packageApi (套餐管理)                                       │
│  ├── stockApi (出入库管理)                                       │
│  └── dashboardApi (仪表盘数据)                                   │
├─────────────────────────────────────────────────────────────────┤
│  工具层 (Utils) - 工具函数                                       │
│  ├── request.ts (Axios封装/拦截器/错误处理/请求取消)              │
│  ├── storage.ts (localStorage/sessionStorage封装)               │
│  ├── permission.ts (权限判断/按钮权限指令)                        │
│  ├── formatter.ts (日期/流量/金额格式化)                          │
│  ├── validator.ts (表单验证规则)                                 │
│  ├── debounce.ts (防抖节流)                                      │
│  └── errorHandler.ts (全局错误处理)                              │
├─────────────────────────────────────────────────────────────────┤
│  类型层 (Types) - TypeScript类型定义                             │
│  ├── api.d.ts (API请求/响应类型)                                 │
│  ├── user.d.ts (用户相关类型)                                    │
│  ├── card.d.ts (卡片相关类型)                                    │
│  ├── pool.d.ts (流量池相关类型)                                   │
│  └── common.d.ts (通用类型/枚举)                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 架构优势
1. **分层清晰**：视图、组件、状态、服务、工具分离
2. **类型安全**：100% TypeScript，编译时发现错误
3. **可维护性**：单一职责，易于测试和扩展
4. **可复用性**：组件化设计，减少重复代码
5. **性能优化**：懒加载、缓存、虚拟滚动

---

## 📁 项目目录结构（优化版）

```
iot-card-frontend/
├── public/
│   ├── favicon.ico
│   └── loading.svg                # 首屏加载动画
├── src/
│   ├── assets/                    # 静态资源
│   │   ├── images/
│   │   │   ├── empty/             # 空状态插图
│   │   │   ├── error/             # 错误状态插图
│   │   │   └── logo/              # Logo资源
│   │   ├── icons/                 # SVG图标
│   │   │   ├── carrier/           # 运营商图标
│   │   │   └── status/            # 状态图标
│   │   └── styles/
│   │       ├── variables.scss     # CSS变量（主题色、间距等）
│   │       ├── mixins.scss        # SCSS混合（常用样式）
│   │       ├── reset.scss         # 样式重置
│   │       └── global.scss        # 全局样式
│   ├── components/                # 组件
│   │   ├── layout/                # 布局组件
│   │   │   ├── AppLayout.vue      # 主布局
│   │   │   ├── Sidebar.vue        # 侧边栏（可折叠）
│   │   │   ├── Header.vue         # 顶部栏（用户信息/通知）
│   │   │   ├── Breadcrumb.vue     # 面包屑导航
│   │   │   ├── TabsView.vue       # 多标签页
│   │   │   └── Footer.vue         # 页脚
│   │   ├── common/                # 通用组件
│   │   │   ├── DataTable.vue      # 数据表格（虚拟滚动）
│   │   │   ├── SearchBar.vue      # 搜索栏（防抖）
│   │   │   ├── FilterPanel.vue    # 筛选面板
│   │   │   ├── FormDialog.vue     # 表单弹窗
│   │   │   ├── StatusTag.vue      # 状态标签
│   │   │   ├── EmptyState.vue     # 空状态
│   │   │   ├── ErrorBoundary.vue  # 错误边界
│   │   │   ├── LoadingSkeleton.vue # 骨架屏
│   │   │   ├── ConfirmDialog.vue  # 确认对话框
│   │   │   └── ExportDialog.vue   # 导出对话框
│   │   └── business/              # 业务组件
│   │       ├── CardTable.vue      # 卡片表格
│   │       ├── CardDetail.vue     # 卡片详情卡片
│   │       ├── PoolCard.vue       # 流量池卡片
│   │       ├── UsageProgress.vue  # 流量使用进度条
│   │       ├── UserSelector.vue   # 用户选择器
│   │       ├── PackageSelector.vue # 套餐选择器
│   │       ├── SupplierSelector.vue # 供应商选择器
│   │       ├── ICCIDInput.vue     # ICCID输入框
│   │       ├── DateFormatter.vue  # 日期格式化显示
│   │       └── ExcelImporter.vue  # Excel导入组件
│   ├── views/                     # 页面视图
│   │   ├── login/
│   │   │   └── index.vue          # 登录页
│   │   ├── dashboard/
│   │   │   ├── index.vue          # 仪表盘
│   │   │   └── components/
│   │   │       ├── StatCard.vue   # 统计卡片
│   │   │       ├── TrendChart.vue # 趋势图表
│   │   │       └── AlertList.vue  # 告警列表
│   │   ├── user/
│   │   │   ├── index.vue          # 用户列表
│   │   │   ├── detail.vue         # 用户详情
│   │   │   └── components/
│   │   │       ├── UserForm.vue   # 用户表单
│   │   │       └── UserTree.vue   # 用户树
│   │   ├── package/
│   │   │   ├── supplier.vue       # 底层套餐
│   │   │   ├── sale.vue           # 销售套餐
│   │   │   └── components/
│   │   │       └── PackageForm.vue
│   │   ├── stock/
│   │   │   ├── in.vue             # 入库
│   │   │   ├── out.vue            # 出库
│   │   │   ├── inventory.vue      # 库存
│   │   │   └── components/
│   │   │       ├── ImportDialog.vue
│   │   │       └── StockStats.vue
│   │   ├── card/
│   │   │   ├── index.vue          # 卡片列表
│   │   │   ├── detail.vue         # 卡片详情
│   │   │   └── components/
│   │   │       ├── CardFilter.vue
│   │   │       ├── TransferDialog.vue
│   │   │       └── RemarkDialog.vue
│   │   ├── pool/
│   │   │   ├── index.vue          # 流量池列表
│   │   │   ├── detail.vue         # 流量池详情
│   │   │   └── components/
│   │   │       ├── PoolForm.vue
│   │   │       ├── AddCardDialog.vue
│   │   │       └── UsageChart.vue
│   │   ├── suspend/
│   │   │   ├── policy.vue         # 停卡策略
│   │   │   ├── logs.vue           # 停卡记录
│   │   │   └── alerts.vue         # 告警管理
│   │   └── system/
│   │       ├── config.vue         # 系统配置
│   │       ├── login-logs.vue     # 登录日志
│   │       └── operation-logs.vue # 操作日志
│   ├── router/                    # 路由
│   │   ├── index.ts               # 路由实例
│   │   ├── routes.ts              # 路由配置
│   │   └── guards.ts              # 路由守卫
│   ├── stores/                    # Pinia状态管理
│   │   ├── modules/
│   │   │   ├── auth.ts            # 认证状态
│   │   │   ├── user.ts            # 用户状态
│   │   │   ├── app.ts             # 应用状态
│   │   │   ├── card.ts            # 卡片状态
│   │   │   └── pool.ts            # 流量池状态
│   │   └── index.ts               # Store入口
│   ├── api/                       # API服务
│   │   ├── modules/
│   │   │   ├── auth.ts            # 认证接口
│   │   │   ├── user.ts            # 用户接口
│   │   │   ├── card.ts            # 卡片接口
│   │   │   ├── pool.ts            # 流量池接口
│   │   │   ├── package.ts         # 套餐接口
│   │   │   ├── stock.ts           # 出入库接口
│   │   │   ├── suspend.ts         # 停卡接口
│   │   │   └── dashboard.ts       # 仪表盘接口
│   │   └── index.ts               # API入口
│   ├── types/                     # TypeScript类型定义
│   │   ├── api.d.ts               # API类型
│   │   ├── user.d.ts              # 用户类型
│   │   ├── card.d.ts              # 卡片类型
│   │   ├── pool.d.ts              # 流量池类型
│   │   ├── package.d.ts           # 套餐类型
│   │   ├── common.d.ts            # 通用类型
│   │   └── enums.ts               # 枚举定义
│   ├── utils/                     # 工具函数
│   │   ├── request.ts             # Axios封装
│   │   ├── storage.ts             # 本地存储
│   │   ├── permission.ts          # 权限判断
│   │   ├── formatter.ts           # 数据格式化
│   │   ├── validator.ts           # 表单验证
│   │   ├── debounce.ts            # 防抖节流
│   │   ├── errorHandler.ts        # 错误处理
│   │   └── download.ts            # 文件下载
│   ├── composables/               # 组合式函数
│   │   ├── useTable.ts            # 表格逻辑
│   │   ├── useForm.ts             # 表单逻辑
│   │   ├── usePagination.ts       # 分页逻辑
│   │   ├── usePermission.ts       # 权限逻辑
│   │   ├── useLoading.ts          # 加载状态
│   │   └── useNetwork.ts          # 网络状态
│   ├── directives/                # 自定义指令
│   │   ├── permission.ts          # 权限指令
│   │   ├── loading.ts             # 加载指令
│   │   └── debounce.ts            # 防抖指令
│   ├── constants/                 # 常量定义
│   │   ├── carrier.ts             # 运营商常量
│   │   ├── status.ts              # 状态常量
│   │   └── config.ts              # 配置常量
│   ├── hooks/                     # 业务Hooks
│   │   ├── useCardManagement.ts   # 卡片管理
│   │   └── usePoolManagement.ts   # 流量池管理
│   ├── App.vue
│   └── main.ts
├── .env.development               # 开发环境变量
├── .env.production                # 生产环境变量
├── .eslintrc.js                   # ESLint配置
├── .prettierrc.js                 # Prettier配置
├── vite.config.ts                 # Vite配置
├── tsconfig.json                  # TypeScript配置
├── package.json
└── README.md
```

---

## 🎯 核心功能模块

### 1. 登录与认证

**页面**: `/login`

**功能**：
- 用户名/密码登录
- 记住密码（本地存储）
- JWT Token 管理
- Token 自动刷新
- 登录失败提示

**API**：
```typescript
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
GET  /api/v1/auth/profile
```

---

### 2. 仪表盘

**页面**: `/dashboard`

**功能**：
- 卡片数量统计（按状态/运营商）
- 流量使用趋势图（ECharts折线图）
- 用户数量统计
- 流量池统计
- **账户余额显示**（含充值入口、余额预警）
- **本月到期卡明细**（列表展示，支持一键续费）
- **超套餐用量卡明细**（超量卡片列表，支持批量处理）
- **销售底套餐流量池用量实时百分比**（可视化展示各流量池使用情况）
- 告警消息列表
- 最近活动日志

**组件**：
- `StatCard.vue` - 统计卡片
- `UsageTrendChart.vue` - 流量趋势图
- `AlertList.vue` - 告警列表
- `ActivityLog.vue` - 活动日志
- `AccountBalance.vue` - 账户余额卡片
- `ExpiringCardList.vue` - 到期卡明细
- `OverUsageCardList.vue` - 超量卡明细
- `PoolUsageChart.vue` - 流量池用量百分比图表

**账户余额功能**：
```typescript
{
  balance: number              // 当前余额（元）
  alert_threshold: number      // 预警阈值（元）
  is_alert: boolean           // 是否触发预警
  last_recharge_at: string    // 最后充值时间
  last_recharge_amount: number // 最后充值金额
}
```

**本月到期卡明细**：
- 显示本月即将到期的卡片列表
- 支持按到期日期排序
- 支持批量续费操作
- 显示续费所需金额

**超套餐用量卡明细**：
- 显示流量使用超过套餐的卡片
- 显示超量百分比和超量流量
- 支持批量停机或加油包充值

**流量池用量百分比**：
- 以进度条或饼图展示各流量池使用情况
- 按使用率从高到低排序
- 超过告警阈值的流量池高亮显示
- 点击可跳转到流量池详情

**API**：
```typescript
GET /api/v1/dashboard/overview
GET /api/v1/dashboard/cards/stats
GET /api/v1/dashboard/usage/trend
GET /api/v1/dashboard/pools/stats
GET /api/v1/dashboard/alerts
GET /api/v1/dashboard/account/balance        // 获取账户余额
GET /api/v1/dashboard/cards/expiring         // 获取本月到期卡
GET /api/v1/dashboard/cards/over-usage       // 获取超量卡
GET /api/v1/dashboard/pools/usage-percent    // 获取流量池用量百分比
POST /api/v1/account/recharge                // 账户充值
```

---

### 3. 用户管理与权限系统

**页面**: `/user`

**权限**: 超级管理员、用户（管理子用户）

#### 3.1 角色体系设计

**角色层级结构**：
```
超级管理员 (user_level = 1)
    ├── 可以管理所有用户
    ├── 可以超级登录到任何下级账号
    ├── 拥有所有权限
    └── 可以为下级用户分配权限
    
普通用户 (user_level = 2)
    ├── 可以管理自己的子用户
    ├── 可以超级登录到子用户账号
    ├── 可以为子用户分配权限（不超过自己的权限范围）
    └── 可以查看自己和子用户的数据
    
子用户 (user_level = 3)
    ├── 只能查看自己的数据
    ├── 不能创建下级用户
    ├── 权限由上级用户分配
    └── 不能超级登录
```

**新增特殊角色**：
- **售后服务角色** (`after_sales`): 可查看卡片和供应商信息，但看不到客户信息
- **仓库管理角色** (`warehouse`): 可查看仓库出入库管理，但看不到客户信息

#### 3.2 基础用户管理功能

**功能**：
- 用户列表（树形结构）
- 创建用户（用户/子用户）
- 编辑用户信息
- 修改密码
- 启用/禁用用户
- 超级登录（切换到下级账号）
- 权限管理（为下级用户分配权限）

**表单字段**（与后端API一致）：
```typescript
{
  username: string              // 用户名（唯一）
  password: string              // 密码（创建时必填）
  real_name: string             // 真实姓名
  phone?: string                // 手机号（可选）
  email?: string                // 邮箱（可选）
  user_level: 1 | 2 | 3         // 用户级别：1-超管，2-用户，3-子用户
  role_type?: 'user' | 'after_sales' | 'warehouse'  // 角色类型（可选）
  parent_id?: number            // 父级用户ID（创建子用户时必填）
  status: 'enable' | 'disable'  // 状态
  remark?: string               // 备注（可选）
}
```

**字段说明**：
- `user_level`：超级管理员只能创建level=2的用户，用户只能创建level=3的子用户
- `role_type`：特殊角色类型，用于区分售后服务、仓库管理等角色
- `parent_id`：创建子用户时必须指定父级用户ID
- `password`：创建时必填，编辑时可选（不修改密码时不传）

**二级用户默认配置** (2026-03-10)：
- **默认权限模块**：dashboard, user, card, package, pool, system
- **默认菜单**：dashboard, users, cards, renewal, pools, system_config
- **默认通知**：`alert_notify: { sms: true, email: true }`
- **默认配额**：`quota: { max_cards: 100, max_sub_users: 5, pool_stop_threshold: 100 }`
- 详细配置文档：`USER_MODULE_CONFIG.md`

#### 3.3 超级登录功能

**功能流程**：
1. 上级用户在用户列表中点击"超级登录"按钮
2. 系统验证上级用户是否有 `user:super_login` 权限
3. 系统验证目标用户是否是上级用户的下级
4. 后端生成新的 Token（包含原用户ID和目标用户ID）
5. 前端保存原用户Token，切换到目标用户Token
6. 页面刷新，以目标用户身份登录
7. 顶部显示"超级登录模式"提示和"退出超级登录"按钮
8. 点击"退出超级登录"恢复到原用户身份

**超级登录提示横幅**：
```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ 当前处于超级登录模式，正在以 [张三] 的身份操作            │
│                                    [退出超级登录] 按钮        │
└─────────────────────────────────────────────────────────────┘
```

**数据结构**：
```typescript
// 超级登录Token结构
interface SuperLoginToken {
  access_token: string
  refresh_token: string
  original_user_id: number      // 原用户ID
  current_user_id: number       // 当前登录的用户ID
  is_super_login: boolean       // 是否超级登录模式
  super_login_at: string        // 超级登录时间
}

// 超级登录记录
interface SuperLoginLog {
  id: number
  original_user_id: number      // 原用户ID
  target_user_id: number        // 目标用户ID
  login_at: string              // 登录时间
  logout_at?: string            // 退出时间
  ip: string                    // IP地址
  user_agent: string            // 浏览器信息
}
```

#### 3.4 权限管理系统

**权限模块划分**：
```typescript
const PermissionModules = {
  // 卡片管理
  CARD: {
    VIEW: 'card:view',           // 查看卡片
    CREATE: 'card:create',       // 创建卡片
    EDIT: 'card:edit',          // 编辑卡片
    ACTIVATE: 'card:activate',   // 激活卡片
    SUSPEND: 'card:suspend',     // 停用卡片
    EXPORT: 'card:export',       // 导出卡片
    VIEW_CUSTOMER: 'card:view_customer'  // 查看客户信息
  },
  
  // 流量池管理
  POOL: {
    VIEW: 'pool:view',
    CREATE: 'pool:create',
    EDIT: 'pool:edit',
    VIEW_CUSTOMER: 'pool:view_customer'
  },
  
  // 用户管理
  USER: {
    VIEW: 'user:view',
    CREATE: 'user:create',
    EDIT: 'user:edit',
    RESET_PASSWORD: 'user:reset_password',
    SUPER_LOGIN: 'user:super_login',      // 超级登录权限
    MANAGE_PERMISSION: 'user:manage_permission'  // 管理权限
  },
  
  // 套餐管理
  PACKAGE: {
    VIEW: 'package:view',
    CREATE: 'package:create',
    EDIT: 'package:edit',
    VIEW_SUPPLIER: 'package:view_supplier'  // 查看供应商信息
  },
  
  // 库存管理
  STOCK: {
    VIEW: 'stock:view',
    IN: 'stock:in',              // 入库
    OUT: 'stock:out',            // 出库
    EDIT: 'stock:edit',
    VIEW_CUSTOMER: 'stock:view_customer'
  },
  
  // 停复机管理
  SUSPEND: {
    VIEW: 'suspend:view',
    CREATE: 'suspend:create',
    EDIT: 'suspend:edit'
  },
  
  // 系统管理
  SYSTEM: {
    VIEW: 'system:view',
    CONFIG: 'system:config',
    LOGS: 'system:logs'
  }
}
```

**角色权限模板**：
```typescript
// 售后服务角色权限
const AfterSalesPermissions = [
  'card:view',              // 可以查看卡片
  'card:export',            // 可以导出卡片
  'package:view',           // 可以查看套餐
  'package:view_supplier',  // 可以查看供应商信息
  'pool:view',              // 可以查看流量池
  // 注意：没有 card:view_customer, pool:view_customer
]

// 仓库管理角色权限
const WarehousePermissions = [
  'stock:view',             // 可以查看库存
  'stock:in',               // 可以入库
  'stock:out',              // 可以出库
  'stock:edit',             // 可以编辑库存
  'card:view',              // 可以查看卡片（仅基本信息）
  // 注意：没有 stock:view_customer, card:view_customer
]

// 普通用户权限
const UserPermissions = [
  'card:view',
  'card:view_customer',     // 可以查看客户信息
  'pool:view',
  'pool:view_customer',
  'pool:create',
  'pool:edit',
  'user:view',              // 可以查看子用户
  'user:create',            // 可以创建子用户
  'user:super_login',       // 可以超级登录到子用户
  'user:manage_permission', // 可以管理子用户权限
  // ... 其他权限
]
```

**权限配置界面**：
```
用户详情 > 权限管理标签页

┌─────────────────────────────────────┐
│ 权限配置                              │
├─────────────────────────────────────┤
│                                      │
│ 使用角色模板:                         │
│ ○ 自定义权限                          │
│ ○ 售后服务角色                        │
│ ○ 仓库管理角色                        │
│                                      │
│ 菜单权限:                             │
│ ☑ 数据概览                            │
│ ☑ 卡片管理                            │
│   ☑ 卡片列表                          │
│   ☐ 查看客户信息                      │
│ ☑ 流量池管理                          │
│   ☐ 查看客户信息                      │
│ ☑ 套餐管理                            │
│   ☑ 查看供应商信息                    │
│ ☑ 库存管理                            │
│   ☑ 入库管理                          │
│   ☑ 出库管理                          │
│   ☐ 查看客户信息                      │
│ ☐ 用户管理                            │
│ ☐ 系统管理                            │
│                                      │
│ [保存配置] [重置]                     │
└─────────────────────────────────────┘
```

#### 3.5 数据过滤策略

**客户信息隐藏规则**：
```typescript
// 需要隐藏客户信息的字段
const CustomerSensitiveFields = [
  'user_id',        // 用户ID
  'user_name',      // 用户名称
  'user_phone',     // 用户电话
  'user_email',     // 用户邮箱
  'user_address',   // 用户地址
  'user_company',   // 用户公司
]

// 前端数据过滤
function filterCustomerInfo(data: any, hasPermission: boolean) {
  if (hasPermission) {
    return data
  }
  
  const filtered = { ...data }
  CustomerSensitiveFields.forEach(field => {
    if (field in filtered) {
      filtered[field] = '***'  // 或者直接删除
    }
  })
  
  return filtered
}
```

**组件级权限控制**：
```vue
<!-- 卡片详情页面 -->
<template>
  <div class="card-detail">
    <!-- 基本信息 -->
    <el-descriptions title="卡片信息">
      <el-descriptions-item label="ICCID">{{ cardInfo.iccid }}</el-descriptions-item>
      
      <!-- 客户信息 - 根据权限显示 -->
      <el-descriptions-item 
        v-if="hasPermission('card:view_customer')" 
        label="所属客户"
      >
        {{ cardInfo.user_name }}
      </el-descriptions-item>
      
      <!-- 供应商信息 - 售后服务可见 -->
      <el-descriptions-item 
        v-if="hasPermission('package:view_supplier')" 
        label="供应商"
      >
        {{ cardInfo.supplier_name }}
      </el-descriptions-item>
    </el-descriptions>
  </div>
</template>
```

#### 3.6 需要创建的文件

**组件文件**：
- `src/views/user/index.vue` - 用户列表页
- `src/views/user/components/UserForm.vue` - 用户表单
- `src/views/user/components/PermissionConfig.vue` - 权限配置组件
- `src/components/layout/Header.vue` - 扩展超级登录提示横幅

**API文件**：
- `src/api/modules/user.ts` - 用户 API (已存在，需完善)

**Store文件**：
- `src/stores/modules/auth.ts` - 扩展超级登录功能

**工具文件**：
- `src/utils/permission.ts` - 权限判断工具
- `src/directives/permission.ts` - 权限指令

**类型文件**：
- `src/types/user.d.ts` - 用户类型定义
- `src/types/permission.d.ts` - 权限类型定义

#### 3.7 API接口

**基础用户管理**：
```typescript
GET    /api/v1/users              // 获取用户列表
POST   /api/v1/users              // 创建用户
GET    /api/v1/users/{id}         // 获取用户详情
PUT    /api/v1/users/{id}         // 更新用户
```

**超级登录相关**：
```typescript
POST   /api/v1/auth/super-login   // 超级登录
POST   /api/v1/auth/exit-super-login  // 退出超级登录
GET    /api/v1/auth/super-login-logs  // 超级登录日志
```

**权限管理相关**：
```typescript
GET    /api/v1/users/{id}/permissions     // 获取用户权限
PUT    /api/v1/users/{id}/permissions     // 更新用户权限
GET    /api/v1/permissions                // 获取所有权限列表
GET    /api/v1/role-templates             // 获取角色模板
```

#### 3.8 开发步骤

**Phase 1: 权限系统基础** (2-3天)
- [ ] 扩展用户类型定义，添加角色字段
- [ ] 创建权限常量定义文件
- [ ] 实现权限判断工具函数
- [ ] 更新 Auth Store，添加权限管理方法
- [ ] 创建权限指令 v-permission

**Phase 2: 超级登录功能** (2-3天)
- [ ] 扩展 Auth API，添加超级登录接口
- [ ] 实现超级登录 Store 逻辑
- [ ] 更新 Header 组件，添加超级登录提示
- [ ] 在用户列表添加超级登录按钮
- [ ] 实现退出超级登录功能
- [ ] 添加超级登录日志记录

**Phase 3: 权限管理界面** (3-4天)
- [ ] 创建权限配置组件
- [ ] 实现角色模板选择
- [ ] 实现菜单权限树
- [ ] 实现操作权限配置
- [ ] 添加权限保存和重置功能

**Phase 4: 特殊角色实现** (2-3天)
- [ ] 实现售后服务角色权限模板
- [ ] 实现仓库管理角色权限模板
- [ ] 添加客户信息过滤逻辑
- [ ] 更新各个页面的权限控制
- [ ] 测试不同角色的数据可见性

**Phase 5: 测试与优化** (2天)
- [ ] 功能测试
- [ ] 权限边界测试
- [ ] 性能优化
- [ ] 文档完善

**预计总时间**: 11-15 天

---

### 4. 套餐管理

#### 4.1 底层套餐（供应商套餐）

**页面**: `/package/supplier`

**权限**: 超级管理员

**功能**：
- 套餐列表
- 创建套餐
- 编辑套餐
- 按运营商/周期筛选

**表单字段**（与后端API一致）：
```typescript
{
  package_id: string        // 套餐ID（唯一标识，用于自动组流量池）
  name: string              // 套餐名称，如：移动1G/月
  carrier: 'cmcc' | 'cucc' | 'ctcc'  // 运营商
  flow_size: number         // 流量大小(MB)，如：1024
  period_type: 'monthly' | 'yearly'  // 周期类型
  valid_days: number        // 有效天数，如：30
  cost_price: number        // 采购成本（元）
  supplier_id: number       // 供应商ID
  enable_auto_pool: boolean // 是否启用自动组流量池（默认false）
  remark?: string           // 备注（可选）
  status?: 'enable' | 'disable'  // 状态（可选，默认enable）
}
```

**字段说明**：
- `package_id`：套餐唯一标识符，用于自动组流量池功能
- `enable_auto_pool`：启用后，相同package_id的卡片激活时自动加入流量池
- `flow_size`：后端存储单位为MB，前端可提供GB/MB切换输入
- `cost_price`：金额字段，最多2位小数
- 所有必填字段必须进行前端验证

**自动组流量池规则**：
- 只有 `enable_auto_pool=true` 的套餐才会自动组池
- 相同 `package_id` 的卡片激活后自动加入同一个流量池
- 流量池名称自动生成：`{运营商}-{流量大小}-{周期}-自动池-{创建日期}`
- 例如：`移动-1G-月包-自动池-20260205`

#### 4.2 销售套餐

**页面**: `/package/sale`

**权限**: 超级管理员

**功能**：
- 销售套餐列表
- 创建销售套餐
- 编辑销售套餐
- 关联底层套餐

**表单字段**（与后端API一致）：
```typescript
{
  package_id: string              // 套餐ID（与底层套餐关联）
  name: string                    // 销售套餐名称
  supplier_package_id: number     // 关联的底层套餐ID
  sale_price: number              // 销售价格（元）
  profit_margin?: number          // 利润率(%) - 可选，前端计算显示
  status: 'enable' | 'disable'    // 状态
  remark?: string                 // 备注（可选）
}
```

**字段说明**：
- `package_id`：销售套餐唯一标识符，继承自底层套餐或自定义
- `profit_margin` 可由前端计算：`((sale_price - cost_price) / cost_price) * 100`
- `sale_price` 必须大于等于底层套餐的 `cost_price`

---

### 5. 出入库管理

#### 5.1 卡片入库

**页面**: `/stock/in`

**权限**: 超级管理员

**功能**：
- **批量导入卡片（固定Excel模板）**
- 选择供应商
- 选择底层套餐
- 设置测试期截止日期（可选）
- 设置沉默期截止日期（必填）
- 查看入库记录
- **导出入库记录**

**Excel模板格式**（固定格式，防止人为输入错误）：
```
列A: ICCID（必填，19-20位数字）
列B: IMSI（必填）
列C: 电话号码（必填，11位手机号）
```

**模板示例**：
```csv
ICCID,IMSI,电话号码
89860123456789012345,460012345678901,13800138000
89860123456789012346,460012345678902,13800138001
```

**导入功能**：
- 提供标准Excel模板下载
- 上传前进行格式校验（列数、列名、数据格式）
- 显示导入进度条
- 导入失败时提供详细错误报告（第几行、哪个字段、错误原因）
- 支持部分成功导入（跳过错误行）

**表单字段**（与后端API一致）：
```typescript
{
  supplier_id: number           // 供应商ID
  package_id: number            // 底层套餐ID
  test_expire_date?: string     // 测试期截止日期 (YYYY-MM-DD，可选)
  silent_expire_date: string    // 沉默期截止日期 (YYYY-MM-DD，必填)
  file: File                    // Excel文件
  remark?: string               // 备注（可选）
}
```

**字段说明**：
- 日期格式：前端DatePicker选择后转换为 `YYYY-MM-DD` 格式发送给后端
- 前端显示时可转换为 `YY/M/D` 格式（如：26/1/31）
- `silent_expire_date` 必填，`test_expire_date` 可选

**API**：
```typescript
GET  /api/v1/stock/import-template        // 下载Excel模板
POST /api/v1/stock/in                     // 批量入库
GET  /api/v1/stock/in/records             // 入库记录列表
POST /api/v1/stock/in/records/export      // 导出入库记录
GET  /api/v1/stock/records/card           // 按卡号查询出入库记录 ✅
```

#### 5.2 卡片出库（增强版）✨

**页面**: `/stock/out`

**权限**: 超级管理员

**功能**：
- 选择库存卡片（支持批量）
- 选择目标用户
- 选择销售套餐
- **选择套餐周期**（月包/年包不同选项）
- **选择卡类型**（仅月包套餐显示：单卡/流量池卡）
- 设置出库日期、测试期、沉默期
- 确认出库
- 查看出库记录
- **导出出库记录**
- **Excel批量出库**（固定格式模板）
- **卡片回收功能**（已出库的卡支持回收，重新出库）

**表单字段**（与后端API一致）：
```typescript
{
  card_ids: number[]            // 卡片ID数组
  user_id: number               // 目标用户ID
  sale_package_id: number       // 销售套餐ID
  period_count: number          // 套餐周期数量
  card_type?: 'single' | 'pool' // 卡类型（仅月包套餐需要）
  stock_out_date: string        // 出库日期 (YYYY-MM-DD)
  test_expire_date?: string     // 测试期截止日期 (YYYY-MM-DD，可选)
  silent_expire_date: string    // 沉默期截止日期 (YYYY-MM-DD，必填)
  remark?: string               // 备注（可选）
}
```

**套餐周期选择规则**：
```typescript
// 月包套餐（period_type = 'monthly'）
const monthlyPeriods = [
  { label: '3个月', value: 3 },
  { label: '6个月', value: 6 },
  { label: '12个月', value: 12 },
  { label: '24个月', value: 24 },
  { label: '36个月', value: 36 },
  { label: '50个月', value: 50 },
  { label: '60个月', value: 60 }
]

// 年包套餐（period_type = 'yearly'）
// 注意：年包有效期是360天，不是365天
const yearlyPeriods = [
  { label: '1年', value: 1, days: 360 },
  { label: '2年', value: 2, days: 720 },
  { label: '3年', value: 3, days: 1080 },
  { label: '5年', value: 5, days: 1800 },
  { label: '6年', value: 6, days: 2160 }
]
```

**卡类型选择规则**：
- **仅月包套餐显示**卡类型选择框
- 年包套餐不显示卡类型选择（默认为单卡）
- 单卡（single）：达量即停机，无流量池功能
- 流量池卡（pool）：可加入流量池共享流量

**Excel批量出库**：

模板格式（固定格式）：
```csv
ICCID,用户ID,销售套餐ID,套餐周期,卡类型,出库日期,测试期截止日期,沉默期截止日期,备注
89860123456789012345,10,5,12,single,2026-02-11,2026-03-11,2026-04-11,测试卡
89860123456789012346,10,5,12,pool,2026-02-11,,2026-04-11,正式卡
```

字段说明：
- ICCID：必填，19-20位数字
- 用户ID：必填，目标用户ID
- 销售套餐ID：必填
- 套餐周期：必填，月包填月数（3/6/12等），年包填年数（1/2/3等）
- 卡类型：月包必填（single/pool），年包可不填
- 出库日期：必填，格式YYYY-MM-DD
- 测试期截止日期：可选，格式YYYY-MM-DD
- 沉默期截止日期：必填，格式YYYY-MM-DD
- 备注：可选

**Excel导入功能**：
- 提供标准Excel模板下载
- 上传前进行格式校验
- 显示导入进度条
- 导入失败时提供详细错误报告（第几行、哪个字段、错误原因）
- 支持部分成功导入（跳过错误行）

**卡片回收功能**：
```typescript
{
  card_ids: number[]            // 要回收的卡片ID数组
  recycle_reason: string        // 回收原因（必填）
  remark?: string               // 备注（可选）
}
```

**回收规则**：
- 只有已出库的卡片才能回收
- 回收后卡片状态恢复为"库存"
- 回收操作需要二次确认
- 记录回收原因和操作人
- 回收后的卡片可以重新出库

**字段说明**：
- `period_count`：套餐周期数量，月包单位是月，年包单位是年
- `card_type`：仅月包套餐需要，年包套餐不需要（后端默认为single）
- 前端需要根据选择的销售套餐的 `period_type` 动态显示周期选项和卡类型选择框

**API**：
```typescript
POST /api/v1/stock/out                    // 批量出库
GET  /api/v1/stock/out/records            // 出库记录列表
POST /api/v1/stock/out/records/export     // 导出出库记录
GET  /api/v1/stock/out/template           // 下载Excel出库模板
POST /api/v1/stock/out/batch-import       // Excel批量出库
POST /api/v1/stock/recycle                // 卡片回收
GET  /api/v1/stock/recycle/records        // 回收记录列表
```

#### 5.3 库存管理

**页面**: `/stock/inventory`

**权限**: 超级管理员

**功能**：
- 库存统计（按供应商/套餐/运营商）
- 库存卡片列表
- 按条件筛选
- 导出库存数据
- **支持输入卡号批量查询**
- **支持正序/降序排序**

**库存卡片列表字段**：
```typescript
{
  id: number                    // 卡片ID
  carrier: 'cmcc' | 'cucc' | 'ctcc'  // 运营商
  iccid: string                 // ICCID（20位）
  imsi: string                  // IMSI
  msisdn: string                // 电话号码
  package_id: string            // 底层套餐ID
  package_name: string          // 底层套餐名称
  stock_in_at: string           // 入库日期 (YYYY-MM-DD)
  test_expire_date: string      // 测试期到期日 (YYYY-MM-DD)
  silent_expire_date: string    // 沉默期到期日 (YYYY-MM-DD)
  supplier_id: number           // 供应商ID
  supplier_name: string         // 供应商名称
  remark: string                // 备注
  status: 'stock'               // 状态（库存中）
}
```

**批量查询功能**：
- 支持输入多个ICCID（换行或逗号分隔）
- 一次最多查询100个卡号
- 显示查询结果和未找到的卡号
- 支持导出查询结果

**排序功能**：
- 支持按入库日期、测试期到期日、沉默期到期日排序
- 支持正序（ASC）和降序（DESC）
- 默认按入库日期降序排列

**筛选条件**：
- 运营商筛选
- 供应商筛选
- 套餐筛选
- 入库日期范围
- 测试期到期日范围
- 沉默期到期日范围

**API**：
```typescript
GET  /api/v1/stock/inventory              // 库存列表
GET  /api/v1/stock/inventory/stats        // 库存统计
POST /api/v1/stock/inventory/batch-query  // 批量查询
POST /api/v1/stock/inventory/export       // 导出库存
```

---

### 6. 卡片管理

**页面**: `/card`

**权限**: 用户、子用户

**功能**：

#### 6.1 卡片列表
- 分页表格（带网格线border）
- 快速搜索（ICCID/IMSI/MSISDN/后6位）
- **支持输入ICCID批量查询卡信息**（结果直接显示在主列表，非弹窗）
- 基础筛选（状态/运营商/周期/流量池）
- **高级搜索**（可展开/收起）：关联客户（远程搜索）、备注关键词、出库单号、出库时间范围、激活时间范围、到期时间范围
- 批量操作（划拨/备注/导出/续费/停机/复机）
- **批量续费功能**
- **批量停复机功能**
- 卡片详情查看
- **流量显示格式**：2G（非2.00GB）、M（非MB）、使用百分比0位小数

**表格字段**（与后端完全一致）：
```typescript
{
  id: number                // 卡片ID
  iccid: string             // ICCID（20位）
  imsi: string              // IMSI
  msisdn: string            // 号码
  carrier: 'cmcc' | 'cucc' | 'ctcc'  // 运营商
  status: 'stock' | 'testing' | 'silent' | 'activated' | 'expired' | 'suspended' | 'cancelled'
  data_used: number         // 已用流量(MB)
  data_total: number        // 总流量(MB)
  usage_percent: number     // 使用率(%) - 前端计算
  flow_size: number         // 套餐流量(MB)
  period_type: 'monthly' | 'yearly'  // 周期类型
  test_expire_date: string  // 测试期日期 (YYYY-MM-DD，显示为 26/1/31)
  silent_expire_date: string // 沉默期日期 (YYYY-MM-DD，显示为 26/4/30)
  activated_at: string      // 激活日期 (YYYY-MM-DD)
  expired_at: string        // 到期日期 (YYYY-MM-DD)
  pool_id: number           // 流量池ID
  pool_name: string         // 流量池名称 - 前端关联查询
  is_pool_member: boolean   // 是否在流量池中
  remark: string            // 备注
  user_id: number           // 所属用户ID
  supplier_id: number       // 供应商ID
  sale_package_id: number   // 销售套餐ID
}
```

**注意**：
- 日期字段后端返回 `YYYY-MM-DD` 格式，前端显示时转换为 `YY/M/D` 格式
- `usage_percent` 由前端计算：`(data_used / data_total) * 100`
- `pool_name` 需要前端根据 `pool_id` 关联查询或后端返回

**批量查询功能**：
```typescript
{
  iccids: string[]              // ICCID数组（最多100个）
}
```
- 支持输入多个ICCID（换行或逗号分隔）
- 显示查询结果和未找到的卡号
- 支持导出查询结果

**批量续费功能**：
```typescript
{
  card_ids: number[]            // 卡片ID数组
  renew_period: 1 | 3 | 6 | 12  // 续费周期（月）
  total_amount: number          // 总金额（前端计算显示）
}
```
- 续费前显示总金额预览
- 支持选择续费周期（1/3/6/12个月）
- 余额不足时给出明确提示
- 续费成功后更新到期日期

**批量停复机功能**：
```typescript
{
  card_ids: number[]            // 卡片ID数组
  action: 'suspend' | 'resume'  // 操作类型：停机/复机
  reason?: string               // 操作原因（可选）
}
```
- 停机前需要二次确认
- 显示影响的卡片数量
- 支持填写操作原因
- 记录操作日志

#### 6.2 卡片详情
- 基本信息
- 流量使用情况（进度条）
- 生命周期日期
- 划拨记录
- 操作日志

#### 6.3 卡片操作
- 划拨给子用户
- 添加/编辑备注
- 手动停卡/复机（需权限）

**注意**：流量池的卡片添加/移除操作在流量池管理模块中进行，不在卡片管理模块操作。

**API**：
```typescript
GET    /api/v1/cards                       // 卡片列表（支持高级搜索参数：remark, customer_id, batch_id, stock_out_start/end, activated_start/end, expired_start/end）
GET    /api/v1/cards/{id}
GET    /api/v1/cards/search
POST   /api/v1/cards/batch-query          // 批量查询
POST   /api/v1/cards/{id}/transfer
PUT    /api/v1/cards/{id}/remark
POST   /api/v1/cards/batch-renew          // 批量续费
POST   /api/v1/cards/batch-suspend        // 批量停机
POST   /api/v1/cards/batch-resume         // 批量复机
POST   /api/v1/cards/export
```

---

### 7. 流量池管理

**页面**: `/pool`

**权限**: 用户

**功能**：

#### 7.1 流量池列表
- 流量池卡片展示
- 用量统计（总流量/已用/剩余）
- 使用率进度条
- 告警状态标识
- **充值流量池加油包功能**

**卡片展示**：
```
┌─────────────────────────────────────┐
│  移动-1G-月包共享池                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  已用: 1.2GB / 3GB (40%)            │
│  卡片数: 3张                        │
│  告警阈值: 80%                      │
│  [查看详情] [编辑] [充值加油包]     │
└─────────────────────────────────────┘
```

**充值加油包功能**：
```typescript
{
  pool_id: number               // 流量池ID
  package_type: string          // 加油包类型（如：1GB/5GB/10GB）
  flow_size: number             // 充值流量大小(MB)
  price: number                 // 加油包价格（元）
  valid_days: number            // 有效天数
}
```

**加油包充值流程**：
1. 选择流量池
2. 选择加油包规格（1GB/5GB/10GB等）
3. 显示价格和有效期
4. 确认充值
5. 扣除账户余额
6. 更新流量池总流量
7. 记录充值日志

**加油包规则**：
- 加油包流量立即生效
- 加油包有独立的有效期
- 优先消耗加油包流量
- 过期未用完的流量自动清零

#### 7.2 流量池详情
- 基本信息
- 用量趋势图（ECharts）
- 池内卡片列表
- 操作日志

**表单字段**（与后端API一致）：
```typescript
{
  name: string                  // 流量池名称
  carrier: 'cmcc' | 'cucc' | 'ctcc'  // 运营商
  flow_size: number             // 单卡流量(MB)
  period_type: 'monthly' | 'yearly'  // 周期类型
  alert_threshold?: number      // 告警阈值(%)，如：80
  stop_threshold?: number       // 停卡阈值(%)，如：100
  remark?: string               // 备注（可选）
}
```

**字段说明**：
- 流量池规格由 `carrier` + `flow_size` + `period_type` 三要素确定
- 只有相同规格的卡片才能加入同一个流量池
- `alert_threshold` 和 `stop_threshold` 为可选，默认值可由后端设置

**API**：
```typescript
GET    /api/v1/pools
POST   /api/v1/pools
GET    /api/v1/pools/{id}
PUT    /api/v1/pools/{id}
POST   /api/v1/pools/{id}/cards
DELETE /api/v1/pools/{id}/cards
GET    /api/v1/pools/{id}/usage
POST   /api/v1/pools/{id}/recharge        // 充值加油包
GET    /api/v1/pools/packages             // 获取加油包列表
GET    /api/v1/pools/{id}/recharge-logs   // 充值记录
```

---

### 8. 停卡管理

#### 8.1 停卡策略

**页面**: `/suspend/policy`

**权限**: 超级管理员

**功能**：
- 策略列表
- 创建策略
- 编辑策略
- 启用/禁用策略

**策略类型**：
- 到期自动停卡
- 流量池超限停卡
- 单卡超量停卡
- 超级管理员可批量强制停卡
- 超级管理员可批量强制激活卡

#### 8.2 停卡记录

**页面**: `/suspend/logs`

**权限**: 超级管理员、用户

**功能**：
- 停卡记录列表
- 按类型/时间筛选
- 查看停卡原因
- 手动批量复机

**API**：
```typescript
GET    /api/v1/suspend/policies
POST   /api/v1/suspend/policies
POST   /api/v1/suspend/cards/suspend
POST   /api/v1/suspend/cards/resume
GET    /api/v1/suspend/logs
```

---

### 9. 系统设置

**页面**: `/system`

**权限**: 超级管理员

**功能**：
- 系统配置管理（每个二级账户生成固定的APPID AppSecret 和API文档）
- 登录日志查询
- 操作日志查询
- 告警规则设置
- 通知模板管理
- 账户密码修改

**API**：
```typescript
GET    /api/v1/system/configs
PUT    /api/v1/system/configs
GET    /api/v1/system/logs/login
GET    /api/v1/system/logs/operation
```

---

## 🎨 UI组件设计

### 通用组件

#### DataTable 数据表格
```vue
<DataTable
  :data="tableData"
  :columns="columns"
  :loading="loading"
  :pagination="pagination"
  @page-change="handlePageChange"
  @selection-change="handleSelectionChange"
>
  <template #toolbar>
    <el-button type="primary">新增</el-button>
  </template>
</DataTable>
```

#### SearchBar 搜索栏
```vue
<SearchBar
  v-model="searchForm"
  :fields="searchFields"
  @search="handleSearch"
  @reset="handleReset"
/>
```

#### StatusTag 状态标签
```vue
<StatusTag :status="card.status" />
<!-- 自动根据状态显示不同颜色 -->
```

---

## 🔐 权限控制

### 路由权限
```typescript
// router/index.ts
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth && !userStore.token) {
    next('/login')
  } else if (to.meta.permission) {
    if (userStore.hasPermission(to.meta.permission)) {
      next()
    } else {
      next('/403')
    }
  } else {
    next()
  }
})
```

### 按钮权限
```vue
<el-button v-permission="'user:create'">创建用户</el-button>
```

### 权限指令
```typescript
// directives/permission.ts
export const permission = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    const { value } = binding
    const userStore = useUserStore()
    
    if (!userStore.hasPermission(value)) {
      el.parentNode?.removeChild(el)
    }
  }
}
```

---

## 📊 数据格式化

### 日期格式
- 显示格式：`26/1/31` (YY/M/D)
- 存储格式：`2026-01-31` (YYYY-MM-DD)

### 流量单位
- 显示：自动转换，无小数位 (1024MB → 1G, 512MB → 512M)
- 存储：统一使用 MB
- 使用百分比：0位小数（Math.round）

### 运营商映射
```typescript
const carrierMap = {
  cmcc: '中国移动',
  cucc: '中国联通',
  ctcc: '中国电信'
}
```

### 状态映射
```typescript
const statusMap = {
  stock: { label: '库存', type: 'info' },
  testing: { label: '测试期', type: 'warning' },
  silent: { label: '沉默期', type: '' },
  activated: { label: '已激活', type: 'success' },
  expired: { label: '已到期', type: 'danger' },
  suspended: { label: '已停机', type: 'danger' },
  cancelled: { label: '已销卡', type: 'info' }
}
```

---

## 🚀 开发规范

### 命名规范
- 组件：PascalCase (`UserList.vue`)
- 文件：kebab-case (`user-list.ts`)
- 变量/函数：camelCase (`getUserList`)
- 常量：UPPER_SNAKE_CASE (`API_BASE_URL`)
- CSS类：BEM (`card__header--active`)

### 代码规范
- 使用 ESLint + Prettier
- 使用 TypeScript 严格模式
- 组件使用 Composition API + `<script setup>`
- 避免使用 `any`，明确类型定义

### Git提交规范
```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试
chore: 构建/工具链
```

---

## 📦 依赖清单

```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "element-plus": "^2.5.0",
    "axios": "^1.6.0",
    "echarts": "^5.4.0",
    "dayjs": "^1.11.0",
    "@vueuse/core": "^10.7.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "@vitejs/plugin-vue": "^5.0.0",
    "sass": "^1.69.0",
    "eslint": "^8.56.0",
    "prettier": "^3.1.0"
  }
}
```

---

## 🎯 开发计划

| 阶段 | 模块 | 预估时间 |
|------|------|----------|
| Phase 1 | 项目初始化 + 登录认证 | 1天 |
| Phase 2 | 布局框架 + 路由权限 | 1天 |
| Phase 3 | 仪表盘 | 1天 |
| Phase 4 | 用户管理 | 1天 |
| Phase 5 | 套餐管理 | 1天 |
| Phase 6 | 出入库管理 | 2天 |
| Phase 7 | 卡片管理 | 2天 |
| Phase 8 | 流量池管理 | 2天 |
| Phase 9 | 停卡管理 | 1天 |
| Phase 10 | 系统设置 | 1天 |
| Phase 11 | 联调测试 | 2天 |

**总计**: 约 15 个工作日

---

---

## 📊 前后端字段映射对照表

### 卡片相关字段（iot_cards表）

| 前端字段 | 后端字段 | 类型 | 说明 |
|---------|---------|------|------|
| id | id | number | 卡片ID |
| iccid | iccid | string | ICCID（19-20位） |
| imsi | imsi | string | IMSI |
| msisdn | msisdn | string | 号码 |
| carrier | carrier | enum | 运营商：cmcc/cucc/ctcc |
| status | status | enum | 状态：stock/testing/silent/activated/expired/suspended/cancelled |
| flowSize | flow_size | number | 套餐流量(MB) |
| periodType | period_type | enum | 周期：monthly/yearly |
| dataUsed | data_used | number | 已用流量(MB) |
| dataTotal | data_total | number | 总流量(MB) |
| testExpireDate | test_expire_date | string | 测试期日期(YYYY-MM-DD) |
| silentExpireDate | silent_expire_date | string | 沉默期日期(YYYY-MM-DD) |
| activatedAt | activated_at | string | 激活日期(YYYY-MM-DD) |
| expiredAt | expired_at | string | 到期日期(YYYY-MM-DD) |
| poolId | pool_id | number | 流量池ID |
| isPoolMember | is_pool_member | boolean | 是否在流量池 |
| userId | user_id | number | 所属用户ID |
| supplierId | supplier_id | number | 供应商ID |
| salePackageId | sale_package_id | number | 销售套餐ID |
| remark | remark | string | 备注 |
| stockInAt | stock_in_at | datetime | 入库时间 |
| stockOutAt | stock_out_at | datetime | 出库时间 |

### 流量池相关字段（traffic_pools表）

| 前端字段 | 后端字段 | 类型 | 说明 |
|---------|---------|------|------|
| id | id | number | 流量池ID |
| name | name | string | 流量池名称 |
| userId | user_id | number | 所属用户ID |
| carrier | carrier | enum | 运营商 |
| flowSize | flow_size | number | 单卡流量(MB) |
| periodType | period_type | enum | 周期类型 |
| cardCount | card_count | number | 卡片数量 |
| dataTotal | data_total | number | 总流量(MB) |
| dataUsed | data_used | number | 已用流量(MB) |
| alertThreshold | alert_threshold | number | 告警阈值(%) |
| stopThreshold | stop_threshold | number | 停卡阈值(%) |
| status | status | enum | 状态：enable/disable |
| remark | remark | string | 备注 |

### 用户相关字段（sys_users表）

| 前端字段 | 后端字段 | 类型 | 说明 |
|---------|---------|------|------|
| id | id | number | 用户ID |
| username | username | string | 用户名 |
| realName | real_name | string | 真实姓名 |
| phone | phone | string | 手机号 |
| email | email | string | 邮箱 |
| userLevel | user_level | number | 用户级别：1/2/3 |
| parentId | parent_id | number | 父级用户ID |
| status | status | enum | 状态：enable/disable |
| remark | remark | string | 备注 |

### 套餐相关字段（packages表）

| 前端字段 | 后端字段 | 类型 | 说明 |
|---------|---------|------|------|
| id | id | number | 套餐ID |
| name | name | string | 套餐名称 |
| carrier | carrier | enum | 运营商 |
| flowSize | flow_size | number | 流量(MB) |
| periodType | period_type | enum | 周期类型 |
| validDays | valid_days | number | 有效天数 |
| costPrice | cost_price | number | 成本价 |
| salePrice | sale_price | number | 销售价 |
| supplierId | supplier_id | number | 供应商ID |
| status | status | enum | 状态 |
| remark | remark | string | 备注 |

**命名规范**：
- 后端：snake_case（下划线命名）
- 前端：camelCase（驼峰命名）
- 前端需要在API层进行字段转换

---

## 🔧 核心优化方案（稳定性 + 用户体验）

### 1. 错误处理机制（减少Bug）

#### 全局错误捕获
```typescript
// utils/errorHandler.ts
export class ErrorHandler {
  // API错误处理
  static handleApiError(error: any) {
    const { response } = error
    if (!response) {
      ElMessage.error('网络连接失败，请检查网络')
      return
    }
    
    const errorMap: Record<number, string> = {
      400: '请求参数错误',
      401: '登录已过期，请重新登录',
      403: '没有权限访问',
      404: '请求的资源不存在',
      500: '服务器错误，请稍后重试',
      502: '网关错误',
      503: '服务暂时不可用'
    }
    
    const message = errorMap[response.status] || response.data?.message || '操作失败'
    ElMessage.error(message)
    
    // 401自动跳转登录
    if (response.status === 401) {
      router.push('/login')
    }
  }
  
  // 组件错误边界
  static handleComponentError(err: Error, instance: any, info: string) {
    console.error('组件错误:', err, instance, info)
    ElMessage.error('页面加载失败，请刷新重试')
  }
}
```

#### 请求拦截器（自动重试 + Token刷新）
```typescript
// utils/request.ts
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000
})

// 请求拦截
request.interceptors.request.use(
  (config) => {
    const token = storage.get('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截（自动刷新Token）
request.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const { config, response } = error
    
    // Token过期，自动刷新
    if (response?.status === 401 && !config._retry) {
      config._retry = true
      try {
        const { token } = await authApi.refreshToken()
        storage.set('token', token)
        config.headers.Authorization = `Bearer ${token}`
        return request(config)
      } catch (err) {
        router.push('/login')
        return Promise.reject(err)
      }
    }
    
    ErrorHandler.handleApiError(error)
    return Promise.reject(error)
  }
)
```

### 2. 表单验证（防止错误输入）

#### 统一验证规则
```typescript
// utils/validator.ts
export const validators = {
  // ICCID验证（19-20位数字）
  iccid: (rule: any, value: string, callback: any) => {
    if (!value) {
      callback(new Error('请输入ICCID'))
    } else if (!/^\d{19,20}$/.test(value)) {
      callback(new Error('ICCID格式错误，应为19-20位数字'))
    } else {
      callback()
    }
  },
  
  // 手机号验证
  phone: (rule: any, value: string, callback: any) => {
    if (!value) {
      callback()
    } else if (!/^1[3-9]\d{9}$/.test(value)) {
      callback(new Error('手机号格式错误'))
    } else {
      callback()
    }
  },
  
  // 金额验证（最多2位小数）
  price: (rule: any, value: number, callback: any) => {
    if (value === undefined || value === null) {
      callback(new Error('请输入金额'))
    } else if (value < 0) {
      callback(new Error('金额不能为负数'))
    } else if (!/^\d+(\.\d{1,2})?$/.test(String(value))) {
      callback(new Error('金额最多保留2位小数'))
    } else {
      callback()
    }
  }
}
```

### 3. 防抖节流（优化性能）

#### 搜索防抖
```typescript
// composables/useDebounce.ts
import { ref } from 'vue'
import { useDebounceFn } from '@vueuse/core'

export function useSearch(fetchFn: Function, delay = 500) {
  const keyword = ref('')
  const loading = ref(false)
  
  const debouncedSearch = useDebounceFn(async () => {
    loading.value = true
    try {
      await fetchFn(keyword.value)
    } finally {
      loading.value = false
    }
  }, delay)
  
  const handleSearch = (value: string) => {
    keyword.value = value
    debouncedSearch()
  }
  
  return { keyword, loading, handleSearch }
}
```

### 4. 乐观更新（即时反馈）

#### 卡片划拨示例
```typescript
// views/card/index.vue
const handleTransfer = async (cardIds: number[], targetUserId: number) => {
  // 1. 乐观更新UI（立即移除卡片）
  const backupCards = [...cardList.value]
  cardList.value = cardList.value.filter(card => !cardIds.includes(card.id))
  
  try {
    // 2. 调用API
    await cardApi.transfer({ cardIds, targetUserId })
    ElMessage.success('划拨成功')
  } catch (error) {
    // 3. 失败回滚
    cardList.value = backupCards
    ElMessage.error('划拨失败，请重试')
  }
}
```

### 5. 网络状态监控

```typescript
// composables/useNetwork.ts
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

export function useNetwork() {
  const isOnline = ref(navigator.onLine)
  
  const handleOnline = () => {
    isOnline.value = true
    ElMessage.success('网络已恢复')
  }
  
  const handleOffline = () => {
    isOnline.value = false
    ElMessage.warning('网络连接已断开')
  }
  
  onMounted(() => {
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
  })
  
  onUnmounted(() => {
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
  })
  
  return { isOnline }
}
```

### 6. 数据缓存策略

```typescript
// stores/modules/card.ts
import { defineStore } from 'pinia'

export const useCardStore = defineStore('card', {
  state: () => ({
    list: [] as Card[],
    cacheTime: 0,
    cacheDuration: 5 * 60 * 1000 // 5分钟缓存
  }),
  
  actions: {
    async fetchList(force = false) {
      const now = Date.now()
      
      // 缓存未过期且非强制刷新，直接返回
      if (!force && this.list.length > 0 && now - this.cacheTime < this.cacheDuration) {
        return this.list
      }
      
      // 请求新数据
      const data = await cardApi.getList()
      this.list = data
      this.cacheTime = now
      return data
    }
  }
})
```

### 7. 表格虚拟滚动（大数据量优化）

```vue
<!-- components/common/VirtualTable.vue -->
<template>
  <el-table
    :data="visibleData"
    :height="tableHeight"
    @scroll="handleScroll"
  >
    <slot></slot>
  </el-table>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  data: any[]
  itemHeight: number
}>()

const scrollTop = ref(0)
const tableHeight = 600
const visibleCount = Math.ceil(tableHeight / props.itemHeight) + 2

const visibleData = computed(() => {
  const startIndex = Math.floor(scrollTop.value / props.itemHeight)
  return props.data.slice(startIndex, startIndex + visibleCount)
})

const handleScroll = (e: Event) => {
  scrollTop.value = (e.target as HTMLElement).scrollTop
}
</script>
```

### 8. 操作确认（防误操作）

```typescript
// utils/confirm.ts
import { ElMessageBox } from 'element-plus'

export const confirmBatchOperation = (count: number, action: string) => {
  return ElMessageBox.confirm(
    `即将对 ${count} 条数据执行"${action}"操作，是否继续？`,
    '批量操作确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
}
```

### 9. 空状态设计

```vue
<!-- components/common/EmptyState.vue -->
<template>
  <div class="empty-state">
    <img :src="emptyImage" alt="空状态" />
    <p class="empty-text">{{ text }}</p>
    <el-button v-if="showAction" type="primary" @click="handleAction">
      {{ actionText }}
    </el-button>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  type?: 'no-data' | 'no-search' | 'error'
  text?: string
  showAction?: boolean
  actionText?: string
}>()

const emptyImage = computed(() => {
  const images = {
    'no-data': '/images/empty/no-data.svg',
    'no-search': '/images/empty/no-search.svg',
    'error': '/images/empty/error.svg'
  }
  return images[props.type || 'no-data']
})
</script>
```

### 10. 骨架屏加载

```vue
<!-- components/common/LoadingSkeleton.vue -->
<template>
  <div class="skeleton-wrapper">
    <el-skeleton :rows="rows" animated />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  rows?: number
}>()
</script>
```

---

## 📝 开发规范与最佳实践

### 1. TypeScript严格模式
```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

### 2. 组件命名规范
- 组件文件：PascalCase (`UserList.vue`)
- 组件使用：kebab-case (`<user-list />`)
- Props：camelCase
- Events：kebab-case

### 3. API调用规范
```typescript
// ✅ 正确：使用try-catch + loading状态
const fetchData = async () => {
  loading.value = true
  try {
    const data = await api.getData()
    list.value = data
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

// ❌ 错误：没有错误处理
const fetchData = async () => {
  const data = await api.getData()
  list.value = data
}
```

### 4. 性能优化清单
- ✅ 使用 `v-show` 代替频繁切换的 `v-if`
- ✅ 长列表使用虚拟滚动
- ✅ 图片使用懒加载
- ✅ 路由使用懒加载
- ✅ 大组件使用异步组件
- ✅ 合理使用 `computed` 缓存计算结果
- ✅ 避免在模板中使用复杂表达式

### 5. 安全规范
- ✅ 所有用户输入进行XSS过滤
- ✅ Token存储使用加密
- ✅ 敏感操作二次确认
- ✅ API请求添加CSRF Token
- ✅ 禁止在前端存储敏感信息

---

## 🔥 前后端对接注意事项（必读）

> **核心原则**：不信任任何外部数据，做好防御性编程

### 1. 接口文档与规范统一 ✅

#### 1.1 接口文档必须明确的内容
```typescript
/**
 * 接口文档模板
 * 
 * 接口名称：获取卡片列表
 * 接口地址：GET /api/v1/cards
 * 
 * 请求参数：
 * - page: number (必填) - 页码，从1开始
 * - page_size: number (必填) - 每页数量，最大100
 * - status: string (可选) - 状态筛选
 * - keyword: string (可选) - 关键词搜索
 * 
 * 响应格式：
 * {
 *   code: 200,           // 业务状态码
 *   message: "success",  // 提示信息
 *   data: {
 *     total: 100,        // 总数
 *     list: [],          // 数据列表
 *     page: 1,           // 当前页
 *     page_size: 20      // 每页数量
 *   }
 * }
 * 
 * 错误码：
 * - 400: 参数错误
 * - 401: 未登录
 * - 403: 无权限
 * - 404: 资源不存在
 * - 500: 服务器错误
 */
```

#### 1.2 统一响应格式
```typescript
// types/api.d.ts
// 统一响应结构
interface ApiResponse<T = any> {
  code: number          // 业务状态码：200成功，其他失败
  message: string       // 提示信息
  data: T              // 业务数据
}

// 分页响应结构
interface PageResponse<T = any> {
  total: number        // 总数
  list: T[]           // 数据列表
  page: number        // 当前页
  page_size: number   // 每页数量
}

// 使用示例
type CardListResponse = ApiResponse<PageResponse<Card>>
```

#### 1.3 前后端约定清单
- [ ] 统一时区（建议使用UTC或东八区）
- [ ] 统一日期格式（YYYY-MM-DD HH:mm:ss）
- [ ] 统一布尔值（true/false，不用0/1）
- [ ] 统一null处理（空值返回null还是空字符串）
- [ ] 统一数组处理（空数组返回[]，不返回null）
- [ ] 统一分页参数（page从0还是1开始）
- [ ] 统一排序参数（sort字段命名）
- [ ] 统一文件上传格式（multipart/form-data）

---

### 2. 接口状态码与异常处理 ✅

#### 2.1 HTTP状态码处理
```typescript
// utils/request.ts
import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000
})

// 响应拦截器 - 统一处理HTTP状态码
request.interceptors.response.use(
  (response) => {
    const { data } = response
    
    // 业务成功
    if (data.code === 200) {
      return data.data
    }
    
    // 业务失败
    ElMessage.error(data.message || '操作失败')
    return Promise.reject(new Error(data.message))
  },
  (error) => {
    // HTTP错误处理
    if (!error.response) {
      ElMessage.error('网络连接失败，请检查网络')
      return Promise.reject(error)
    }
    
    const { status, data } = error.response
    
    // 统一错误处理
    const errorMap: Record<number, () => void> = {
      400: () => ElMessage.error(data?.message || '请求参数错误'),
      401: () => {
        ElMessage.error('登录已过期，请重新登录')
        router.push('/login')
      },
      403: () => ElMessage.error('没有权限访问'),
      404: () => ElMessage.error('请求的资源不存在'),
      500: () => ElMessage.error('服务器错误，请稍后重试'),
      502: () => ElMessage.error('网关错误'),
      503: () => ElMessage.error('服务暂时不可用')
    }
    
    const handler = errorMap[status]
    if (handler) {
      handler()
    } else {
      ElMessage.error(data?.message || `请求失败(${status})`)
    }
    
    return Promise.reject(error)
  }
)
```

#### 2.2 业务状态码处理
```typescript
// 定义业务状态码枚举
enum ApiCode {
  SUCCESS = 200,
  PARAM_ERROR = 400,
  UNAUTHORIZED = 401,
  FORBIDDEN = 403,
  NOT_FOUND = 404,
  SERVER_ERROR = 500
}

// 业务状态码映射
const codeMessageMap: Record<number, string> = {
  [ApiCode.SUCCESS]: '操作成功',
  [ApiCode.PARAM_ERROR]: '参数错误',
  [ApiCode.UNAUTHORIZED]: '未登录或登录已过期',
  [ApiCode.FORBIDDEN]: '没有权限',
  [ApiCode.NOT_FOUND]: '资源不存在',
  [ApiCode.SERVER_ERROR]: '服务器错误'
}
```

---

### 3. 数据校验与防御性编程 ✅

#### 3.1 不信任后端返回的数据
```typescript
// ❌ 错误：直接使用后端数据
const cardList = response.data.list
cardList.forEach(card => {
  console.log(card.iccid.substring(0, 6)) // 可能报错：card.iccid is undefined
})

// ✅ 正确：先校验再使用
const cardList = Array.isArray(response.data?.list) ? response.data.list : []
cardList.forEach(card => {
  const iccid = card?.iccid || ''
  if (iccid) {
    console.log(iccid.substring(0, 6))
  }
})
```

#### 3.2 数据校验工具函数
```typescript
// utils/validator.ts

/**
 * 校验是否为有效数组
 */
export function isValidArray(data: any): data is any[] {
  return Array.isArray(data) && data.length > 0
}

/**
 * 校验是否为有效字符串
 */
export function isValidString(data: any): data is string {
  return typeof data === 'string' && data.trim() !== ''
}

/**
 * 校验是否为有效数字
 */
export function isValidNumber(data: any): data is number {
  return typeof data === 'number' && !isNaN(data) && isFinite(data)
}

/**
 * 安全获取对象属性
 */
export function safeGet<T>(obj: any, path: string, defaultValue: T): T {
  const keys = path.split('.')
  let result = obj
  
  for (const key of keys) {
    if (result && typeof result === 'object' && key in result) {
      result = result[key]
    } else {
      return defaultValue
    }
  }
  
  return result ?? defaultValue
}

// 使用示例
const total = safeGet(response, 'data.total', 0)
const list = safeGet(response, 'data.list', [])
```

#### 3.3 数据转换与清洗
```typescript
// utils/dataTransform.ts

/**
 * 清洗卡片数据
 */
export function sanitizeCard(card: any): Card | null {
  // 必填字段校验
  if (!card?.iccid || !card?.carrier) {
    console.warn('卡片数据缺少必填字段:', card)
    return null
  }
  
  return {
    id: Number(card.id) || 0,
    iccid: String(card.iccid).trim(),
    imsi: String(card.imsi || '').trim(),
    msisdn: String(card.msisdn || '').trim(),
    carrier: card.carrier,
    status: card.status || 'stock',
    dataUsed: Number(card.data_used) || 0,
    dataTotal: Number(card.data_total) || 0,
    flowSize: Number(card.flow_size) || 0,
    periodType: card.period_type || 'monthly',
    testExpireDate: card.test_expire_date || null,
    silentExpireDate: card.silent_expire_date || null,
    activatedAt: card.activated_at || null,
    expiredAt: card.expired_at || null,
    poolId: card.pool_id || null,
    isPoolMember: Boolean(card.is_pool_member),
    remark: String(card.remark || '').trim(),
    userId: Number(card.user_id) || null,
    supplierId: Number(card.supplier_id) || null,
    salePackageId: Number(card.sale_package_id) || null
  }
}

/**
 * 批量清洗数据
 */
export function sanitizeCardList(list: any[]): Card[] {
  if (!Array.isArray(list)) {
    console.warn('卡片列表不是数组:', list)
    return []
  }
  
  return list
    .map(sanitizeCard)
    .filter((card): card is Card => card !== null)
}
```

#### 3.4 类型守卫
```typescript
// types/guards.ts

/**
 * 卡片类型守卫
 */
export function isCard(data: any): data is Card {
  return (
    data &&
    typeof data === 'object' &&
    typeof data.iccid === 'string' &&
    ['cmcc', 'cucc', 'ctcc'].includes(data.carrier) &&
    typeof data.dataUsed === 'number' &&
    typeof data.dataTotal === 'number'
  )
}

/**
 * 分页数据类型守卫
 */
export function isPageResponse<T>(
  data: any,
  itemGuard: (item: any) => item is T
): data is PageResponse<T> {
  return (
    data &&
    typeof data === 'object' &&
    typeof data.total === 'number' &&
    Array.isArray(data.list) &&
    data.list.every(itemGuard)
  )
}

// 使用示例
const response = await cardApi.getList()
if (isPageResponse(response, isCard)) {
  // TypeScript知道response.list是Card[]类型
  cardList.value = response.list
} else {
  console.error('响应数据格式错误')
  cardList.value = []
}
```

---

### 4. 边界情况处理 ✅

#### 4.1 空数据处理
```typescript
// composables/useCardList.ts
export function useCardList() {
  const cardList = ref<Card[]>([])
  const loading = ref(false)
  const isEmpty = computed(() => !loading.value && cardList.value.length === 0)
  
  const fetchList = async () => {
    loading.value = true
    try {
      const response = await cardApi.getList()
      
      // 防御性处理
      const list = response?.list || []
      cardList.value = sanitizeCardList(list)
      
      // 空数据提示
      if (cardList.value.length === 0) {
        console.log('暂无数据')
      }
    } catch (error) {
      console.error('获取列表失败:', error)
      cardList.value = [] // 失败时清空列表
    } finally {
      loading.value = false
    }
  }
  
  return { cardList, loading, isEmpty, fetchList }
}
```

#### 4.2 数字边界处理
```typescript
/**
 * 安全的数字计算
 */
export function safeCalculate(a: any, b: any, operator: '+' | '-' | '*' | '/'): number {
  const numA = Number(a) || 0
  const numB = Number(b) || 0
  
  switch (operator) {
    case '+':
      return numA + numB
    case '-':
      return numA - numB
    case '*':
      return numA * numB
    case '/':
      return numB === 0 ? 0 : numA / numB
    default:
      return 0
  }
}

/**
 * 安全的百分比计算
 */
export function safePercent(used: any, total: any): number {
  const numUsed = Number(used) || 0
  const numTotal = Number(total) || 0
  
  if (numTotal <= 0) return 0
  
  const percent = (numUsed / numTotal) * 100
  return Math.min(Math.max(percent, 0), 100) // 限制在0-100之间
}
```

#### 4.3 日期处理
```typescript
// utils/dateHelper.ts
import dayjs from 'dayjs'

/**
 * 安全的日期格式化
 */
export function formatDate(date: any, format = 'YYYY-MM-DD'): string {
  if (!date) return '-'
  
  const parsed = dayjs(date)
  if (!parsed.isValid()) {
    console.warn('无效的日期:', date)
    return '-'
  }
  
  return parsed.format(format)
}

/**
 * 转换为前端显示格式 (YY/M/D)
 */
export function formatDateShort(date: any): string {
  if (!date) return '-'
  
  const parsed = dayjs(date)
  if (!parsed.isValid()) return '-'
  
  return parsed.format('YY/M/D')
}

/**
 * 判断日期是否过期
 */
export function isExpired(date: any): boolean {
  if (!date) return false
  
  const parsed = dayjs(date)
  if (!parsed.isValid()) return false
  
  return parsed.isBefore(dayjs(), 'day')
}
```

---

### 5. 并发与竞态处理 ✅

#### 5.1 防止重复提交
```typescript
// composables/useSubmit.ts
export function useSubmit(submitFn: Function) {
  const submitting = ref(false)
  
  const handleSubmit = async (...args: any[]) => {
    if (submitting.value) {
      ElMessage.warning('请勿重复提交')
      return
    }
    
    submitting.value = true
    try {
      await submitFn(...args)
    } finally {
      submitting.value = false
    }
  }
  
  return { submitting, handleSubmit }
}

// 使用示例
const { submitting, handleSubmit } = useSubmit(async (data) => {
  await cardApi.create(data)
  ElMessage.success('创建成功')
})
```

#### 5.2 请求取消
```typescript
// utils/request.ts
import axios, { CancelTokenSource } from 'axios'

// 存储请求取消函数
const pendingRequests = new Map<string, CancelTokenSource>()

// 生成请求key
function getRequestKey(config: any): string {
  return `${config.method}_${config.url}_${JSON.stringify(config.params)}`
}

// 请求拦截器 - 添加取消token
request.interceptors.request.use((config) => {
  const key = getRequestKey(config)
  
  // 取消之前的相同请求
  if (pendingRequests.has(key)) {
    pendingRequests.get(key)?.cancel('请求被取消')
    pendingRequests.delete(key)
  }
  
  // 创建新的取消token
  const source = axios.CancelToken.source()
  config.cancelToken = source.token
  pendingRequests.set(key, source)
  
  return config
})

// 响应拦截器 - 移除取消token
request.interceptors.response.use(
  (response) => {
    const key = getRequestKey(response.config)
    pendingRequests.delete(key)
    return response
  },
  (error) => {
    if (axios.isCancel(error)) {
      console.log('请求被取消:', error.message)
      return Promise.reject(error)
    }
    
    const key = getRequestKey(error.config)
    pendingRequests.delete(key)
    return Promise.reject(error)
  }
)

// 取消所有请求（路由切换时调用）
export function cancelAllRequests() {
  pendingRequests.forEach((source) => {
    source.cancel('路由切换，取消请求')
  })
  pendingRequests.clear()
}
```

---

### 6. 调试与日志 ✅

#### 6.1 开发环境日志
```typescript
// utils/logger.ts
const isDev = import.meta.env.DEV

export const logger = {
  log(...args: any[]) {
    if (isDev) console.log('[LOG]', ...args)
  },
  
  warn(...args: any[]) {
    if (isDev) console.warn('[WARN]', ...args)
  },
  
  error(...args: any[]) {
    console.error('[ERROR]', ...args)
  },
  
  api(method: string, url: string, data?: any) {
    if (isDev) {
      console.group(`[API] ${method} ${url}`)
      if (data) console.log('Data:', data)
      console.groupEnd()
    }
  }
}
```

#### 6.2 API调用日志
```typescript
// 请求拦截器 - 记录请求
request.interceptors.request.use((config) => {
  logger.api(config.method?.toUpperCase() || 'GET', config.url || '', config.data)
  return config
})

// 响应拦截器 - 记录响应
request.interceptors.response.use(
  (response) => {
    logger.log('API响应:', response.config.url, response.data)
    return response
  },
  (error) => {
    logger.error('API错误:', error.config?.url, error.response?.data)
    return Promise.reject(error)
  }
)
```

---

### 7. 前后端联调检查清单 ✅

#### 开发前
- [ ] 获取完整的API文档
- [ ] 确认接口基础URL（开发/测试/生产环境）
- [ ] 确认认证方式（JWT Token放在Header还是Cookie）
- [ ] 确认响应格式（统一的code/message/data结构）
- [ ] 确认分页参数（page从0还是1开始）
- [ ] 确认日期格式（时区、格式）
- [ ] 确认文件上传方式

#### 开发中
- [ ] 所有API调用都有类型定义
- [ ] 所有API调用都有错误处理
- [ ] 所有数据都经过校验和清洗
- [ ] 所有边界情况都有处理
- [ ] 所有异步操作都有loading状态
- [ ] 所有表单都有前端验证
- [ ] 所有危险操作都有确认

#### 联调时
- [ ] 使用真实API，不使用Mock
- [ ] 测试正常流程
- [ ] 测试异常流程（401、403、500等）
- [ ] 测试边界情况（空数据、大数据量）
- [ ] 测试并发情况（快速点击、重复提交）
- [ ] 检查控制台是否有错误
- [ ] 检查网络请求是否正常

---

## ✅ API对接检查清单

### 开发前检查
- [ ] 确认后端API已开发完成
- [ ] 获取API文档（接口地址、请求参数、响应格式）
- [ ] 使用Postman/Apifox测试API可用性
- [ ] 确认字段命名规范（后端snake_case → 前端camelCase）
- [ ] 确认日期格式（后端YYYY-MM-DD → 前端显示YY/M/D）
- [ ] 确认枚举值（carrier、status、period_type等）

### 开发中检查
- [ ] 所有API调用都有loading状态
- [ ] 所有API调用都有错误处理
- [ ] 所有表单都有前端验证
- [ ] 所有危险操作都有二次确认
- [ ] 所有列表都有空状态处理
- [ ] 所有日期字段都正确格式化
- [ ] 所有金额字段都保留2位小数
- [ ] 所有枚举值都使用常量映射

### 测试检查
- [ ] 测试正常流程
- [ ] 测试异常流程（网络错误、401、403、500等）
- [ ] 测试边界情况（空数据、大数据量、特殊字符）
- [ ] 测试并发操作（快速点击、重复提交）
- [ ] 测试权限控制（不同角色看到不同功能）

---

## 🎯 新功能开发计划

### 功能1: 超级登录功能

**需求描述**：
上级用户可以直接登录到下级用户账号，以下级用户的身份进行操作，方便管理和问题排查。

**功能特性**：
- ✅ 超级管理员可以登录到任何下级账号
- ✅ 普通用户可以登录到自己的子用户账号
- ✅ 超级登录时保留原用户身份，可随时退出
- ✅ 超级登录模式下顶部显示明显提示
- ✅ 记录所有超级登录操作日志

**技术实现**：
1. 后端生成特殊Token，包含原用户ID和目标用户ID
2. 前端保存原Token到sessionStorage
3. 切换到新Token，刷新页面
4. Header组件显示超级登录提示横幅
5. 退出时恢复原Token

**开发工作量**: 2-3天

---

### 功能2: 动态权限管理系统

**需求描述**：
为不同角色的用户分配不同的权限，实现细粒度的访问控制。

**权限维度**：
- **菜单权限**: 控制用户可以看到哪些菜单
- **操作权限**: 控制用户可以执行哪些操作（增删改查）
- **数据权限**: 控制用户可以看到哪些数据

**角色模板**：
- **普通用户**: 完整权限（可查看客户信息）
- **售后服务**: 可查看卡片和供应商信息，但看不到客户信息
- **仓库管理**: 可查看仓库出入库，但看不到客户信息

**技术实现**：
1. 定义权限常量（card:view, card:edit等）
2. 后端返回用户权限列表
3. 前端Store存储权限
4. 路由守卫检查菜单权限
5. v-permission指令控制按钮权限
6. API层过滤敏感数据

**开发工作量**: 3-4天

---

### 功能3: 售后服务角色

**需求描述**：
售后人员可以查看卡片信息和供应商信息，但不能看到客户信息（保护客户隐私）。

**权限配置**：
```typescript
const AfterSalesPermissions = [
  'card:view',              // 可以查看卡片
  'card:export',            // 可以导出卡片
  'package:view',           // 可以查看套餐
  'package:view_supplier',  // 可以查看供应商信息
  'pool:view',              // 可以查看流量池
  // 注意：没有 card:view_customer, pool:view_customer
]
```

**数据过滤**：
- 卡片列表：隐藏"所属客户"列
- 卡片详情：隐藏客户信息区域
- 流量池：隐藏客户信息
- 导出数据：不包含客户字段

**开发工作量**: 2天

---

### 功能4: 仓库管理角色

**需求描述**：
仓库人员只能访问出入库管理模块，不能看到客户信息。

**权限配置**：
```typescript
const WarehousePermissions = [
  'stock:view',             // 可以查看库存
  'stock:in',               // 可以入库
  'stock:out',              // 可以出库
  'stock:edit',             // 可以编辑库存
  'card:view',              // 可以查看卡片（仅基本信息）
  // 注意：没有 stock:view_customer, card:view_customer
]
```

**菜单限制**：
- 只显示"库存管理"菜单
- 隐藏其他所有菜单
- 出入库记录中隐藏客户信息

**开发工作量**: 1-2天

---

### 开发优先级与时间规划

| 功能 | 优先级 | 工作量 | 依赖关系 |
|------|--------|--------|----------|
| 动态权限管理系统 | P0 | 3-4天 | 无 |
| 超级登录功能 | P1 | 2-3天 | 权限系统 |
| 售后服务角色 | P1 | 2天 | 权限系统 |
| 仓库管理角色 | P2 | 1-2天 | 权限系统 |

**总计**: 8-11天

**开发顺序**：
1. 先开发权限管理系统（基础设施）
2. 再开发超级登录功能
3. 最后实现特殊角色（售后、仓库）

---

## 📝 备注

1. **响应式设计**: 优先支持桌面端（1920x1080），移动端适配为次要目标
2. **浏览器兼容**: Chrome 90+, Edge 90+, Firefox 88+, Safari 14+
3. **性能目标**: 
   - 首屏加载 < 2秒
   - 页面切换 < 300ms
   - API响应 < 1秒
4. **数据要求**: 
   - **严禁使用模拟数据（Mock Data）**
   - 所有数据必须通过后端API获取
   - 开发阶段确保后端API可用
   - 前端不得硬编码任何业务数据
5. **测试要求**:
   - 单元测试覆盖率 > 60%
   - 关键业务逻辑必须有测试
   - 上线前进行完整的回归测试
6. **代码质量**:
   - TypeScript严格模式，禁止使用any
   - ESLint + Prettier统一代码风格
   - 组件复用率 > 70%
   - 代码注释覆盖率 > 30%

---

## 🎯 后端API状态确认

根据 `MODULE_PLAN.md`，以下模块已完成，可以开始前端对接：

| 模块 | 后端状态 | API端点 | 前端可开始 |
|------|---------|---------|-----------|
| 1. 用户权限管理 | ✅ 已完成 | /api/v1/auth/*, /api/v1/users/* | ✅ 可开始 |
| 2. 套餐管理 | ✅ 已完成 | /api/v1/packages/* | ✅ 可开始 |
| 3. 出入库管理 | ✅ 已完成 | /api/v1/stock/*, /api/v1/batches/* | ✅ 可开始 |
| 4. 卡片管理 | ✅ 已完成 | /api/v1/cards/* | ✅ 可开始 |
| 5. 流量池管理 | ✅ 已完成 | /api/v1/pools/* | ✅ 可开始 |
| 6. 停卡策略 | ✅ 已完成 | /api/v1/suspend/* | ✅ 可开始 |
| 7. 供应商管理 | ✅ 已完成 | /api/v1/suppliers/* | ✅ 可开始 |
| 8. 仪表盘 | ✅ 已完成 | /api/v1/dashboard/* | ✅ 可开始 |
| 9. 系统设置 | ✅ 已完成 | /api/v1/system/* | ✅ 可开始 |

**结论**：后端9个核心模块全部完成，前端可以全面开始开发！

---

## 📞 联系与协作

**前后端协作规范**：
1. 遇到API问题，先查看后端API文档
2. 字段不匹配时，优先以后端数据库字段为准
3. 新增需求需要前后端共同评审
4. API变更需要提前通知前端
5. 定期进行联调测试

**文档维护**：
- 本文档随项目迭代持续更新
- 重大变更需要更新文档版本号
- 所有开发人员必须遵守本文档规范

---

## 🆕 新增功能需求总结（2026-02-11更新）

### 最新更新：出库功能增强 ✨

#### 1. 套餐周期灵活配置
- **月包套餐**：可选 3/6/12/24/36/50/60 个月
- **年包套餐**：可选 1/2/3/5/6 年（注意：年包有效期是360天，不是365天）
- 前端根据选择的销售套餐的 `period_type` 动态显示对应的周期选项

#### 2. 卡类型选择（仅月包）
- **单卡（single）**：达量即停机，无流量池功能
- **流量池卡（pool）**：可加入流量池共享流量
- **显示规则**：仅月包套餐显示卡类型选择框，年包套餐不显示

#### 3. Excel批量出库
- 提供固定格式的Excel模板下载
- 支持批量导入出库数据
- 包含字段：ICCID、用户ID、销售套餐ID、套餐周期、卡类型、出库日期、测试期、沉默期、备注
- 导入时进行格式校验和错误提示
- 支持部分成功导入

#### 4. 数据库设计
- 采用 **方案B**：使用 `period_count` 字段存储周期数量
- 月包：period_count 表示月数（3/6/12等）
- 年包：period_count 表示年数（1/2/3等），有效期计算为 period_count × 360 天

---

## 🆕 新增功能需求总结（2026-02-05）

### 1. 仪表盘增强 ✨

#### 1.1 账户余额显示
- **功能**：显示当前账户余额，支持充值
- **字段**：余额、预警阈值、最后充值时间/金额
- **交互**：余额不足时高亮提示，点击可跳转充值页面
- **API**：`GET /api/v1/dashboard/account/balance`

#### 1.2 本月到期卡明细
- **功能**：显示本月即将到期的卡片列表
- **排序**：按到期日期升序排列
- **操作**：支持批量续费，显示续费所需金额
- **API**：`GET /api/v1/dashboard/cards/expiring`

#### 1.3 超套餐用量卡明细
- **功能**：显示流量使用超过套餐的卡片
- **显示**：超量百分比、超量流量
- **操作**：支持批量停机或加油包充值
- **API**：`GET /api/v1/dashboard/cards/over-usage`

#### 1.4 流量池用量实时百分比
- **功能**：可视化展示各流量池使用情况
- **展示方式**：进度条或饼图
- **排序**：按使用率从高到低
- **告警**：超过告警阈值的流量池高亮显示
- **API**：`GET /api/v1/dashboard/pools/usage-percent`

---

### 2. 套餐管理增强 ✨

#### 2.1 套餐ID字段
- **底层套餐**：增加 `package_id` 字段（唯一标识）
- **销售套餐**：增加 `package_id` 字段（与底层套餐关联）
- **用途**：用于自动组流量池功能

#### 2.2 自动组流量池功能
- **触发条件**：
  - 套餐启用了 `enable_auto_pool` 选项
  - 相同 `package_id` 的卡片激活时
- **自动操作**：
  - 自动创建或加入流量池
  - 流量池名称：`{运营商}-{流量大小}-{周期}-自动池-{日期}`
  - 例如：`移动-1G-月包-自动池-20260205`
- **优势**：减少手动操作，自动化管理

---

### 3. 库存管理增强 ✨

#### 3.1 固定Excel模板上传
- **模板格式**：
  ```
  列A: ICCID（必填，19-20位数字）
  列B: IMSI（必填）
  列C: 电话号码（必填，11位手机号）
  ```
- **功能**：
  - 提供标准模板下载
  - 上传前格式校验
  - 显示导入进度条
  - 详细错误报告（第几行、哪个字段、错误原因）
  - 支持部分成功导入
- **API**：`GET /api/v1/stock/import-template`

#### 3.2 出入库记录导出
- **入库记录导出**：`POST /api/v1/stock/in/records/export`
- **出库记录导出**：`POST /api/v1/stock/out/records/export`
- **格式**：Excel格式，包含所有字段

#### 3.3 卡片回收功能
- **功能**：已出库的卡支持回收，重新出库
- **回收规则**：
  - 只有已出库的卡片才能回收
  - 回收后状态恢复为"库存"
  - 需要填写回收原因
  - 需要二次确认
  - 记录回收日志
- **API**：
  - `POST /api/v1/stock/recycle` - 卡片回收
  - `GET /api/v1/stock/recycle/records` - 回收记录

#### 3.4 库存卡片列表增强
- **新增字段**：
  - 运营商
  - ICCID
  - IMSI
  - 电话号码
  - 底套餐（package_id + package_name）
  - 入库日期
  - 测试期到期日
  - 沉默期到期日
  - 供应商
  - 备注
- **排序功能**：
  - 支持按入库日期、测试期、沉默期排序
  - 支持正序（ASC）和降序（DESC）
  - 默认按入库日期降序
- **批量查询**：
  - 输入多个ICCID（换行或逗号分隔）
  - 最多100个
  - 显示查询结果和未找到的卡号
  - 支持导出查询结果
- **API**：`POST /api/v1/stock/inventory/batch-query`

---

### 4. 卡片管理增强 ✨

#### 4.1 批量查询功能
- **功能**：输入多个ICCID批量查询卡信息
- **限制**：最多100个ICCID
- **显示**：查询结果 + 未找到的卡号列表
- **导出**：支持导出查询结果
- **API**：`POST /api/v1/cards/batch-query`

#### 4.2 批量续费功能
- **功能**：批量为卡片续费
- **续费周期**：1/3/6/12个月
- **流程**：
  1. 选择要续费的卡片
  2. 选择续费周期
  3. 显示总金额预览
  4. 检查账户余额
  5. 确认续费
  6. 扣除余额
  7. 更新到期日期
- **余额不足**：给出明确提示，引导充值
- **API**：`POST /api/v1/cards/batch-renew`

#### 4.3 批量停复机功能
- **功能**：批量停机或复机
- **操作类型**：
  - 停机（suspend）
  - 复机（resume）
- **流程**：
  1. 选择要操作的卡片
  2. 选择操作类型
  3. 填写操作原因（可选）
  4. 显示影响的卡片数量
  5. 二次确认
  6. 执行操作
  7. 记录操作日志
- **API**：
  - `POST /api/v1/cards/batch-suspend` - 批量停机
  - `POST /api/v1/cards/batch-resume` - 批量复机

---

### 5. 流量池管理增强 ✨

#### 5.1 充值流量池加油包
- **功能**：为流量池充值额外流量
- **加油包规格**：1GB/5GB/10GB等
- **流程**：
  1. 选择流量池
  2. 选择加油包规格
  3. 显示价格和有效期
  4. 确认充值
  5. 扣除账户余额
  6. 更新流量池总流量
  7. 记录充值日志
- **加油包规则**：
  - 立即生效
  - 有独立的有效期
  - 优先消耗加油包流量
  - 过期未用完自动清零
- **API**：
  - `POST /api/v1/pools/{id}/recharge` - 充值加油包
  - `GET /api/v1/pools/packages` - 获取加油包列表
  - `GET /api/v1/pools/{id}/recharge-logs` - 充值记录

---

## 📋 新增功能开发计划

| 模块 | 功能 | 优先级 | 工作量 | 依赖 |
|------|------|--------|--------|------|
| **出库管理** | **套餐周期选择** | **P0** | **1天** | **无** |
| **出库管理** | **卡类型选择（月包）** | **P0** | **0.5天** | **套餐周期** |
| **出库管理** | **Excel批量出库** | **P0** | **1.5天** | **套餐周期** |
| **出库管理** | **出库日期/测试期/沉默期** | **P0** | **0.5天** | **无** |
| 仪表盘 | 账户余额显示 | P0 | 0.5天 | 无 |
| 仪表盘 | 本月到期卡明细 | P0 | 0.5天 | 无 |
| 仪表盘 | 超套餐用量卡明细 | P1 | 0.5天 | 无 |
| 仪表盘 | 流量池用量百分比 | P1 | 1天 | 无 |
| 套餐管理 | 套餐ID字段 | P0 | 0.5天 | 无 |
| 套餐管理 | 自动组流量池 | P1 | 1.5天 | 套餐ID |
| 库存管理 | Excel模板上传 | P0 | 1天 | 无 |
| 库存管理 | 出入库记录导出 | P1 | 0.5天 | 无 |
| 库存管理 | 卡片回收功能 | P1 | 1天 | 无 |
| 库存管理 | 库存列表增强 | P0 | 1天 | 无 |
| 库存管理 | 批量查询 | P1 | 0.5天 | 无 |
| 卡片管理 | 批量查询 | P1 | 0.5天 | 无 |
| 卡片管理 | 批量续费 | P0 | 1.5天 | 账户余额 |
| 卡片管理 | 批量停复机 | P1 | 1天 | 无 |
| 流量池管理 | 充值加油包 | P1 | 1.5天 | 账户余额 |

**总计工作量**：约 16.5 天

**开发顺序建议**：
1. **Phase 1**（出库功能增强，3.5天）：✨ **当前优先**
   - 数据库添加 period_count 和 card_type 字段
   - 出库表单添加套餐周期选择
   - 出库表单添加卡类型选择（月包显示）
   - 出库表单添加出库日期、测试期、沉默期
   - Excel批量出库功能
   - 创建Excel出库模板

2. **Phase 2**（基础功能，3天）：
   - 账户余额显示
   - 套餐ID字段
   - Excel模板上传（入库）
   - 库存列表增强

3. **Phase 3**（核心功能，5天）：
   - 本月到期卡明细
   - 批量续费
   - 卡片回收功能
   - 自动组流量池

4. **Phase 4**（增强功能，5天）：
   - 超套餐用量卡明细
   - 流量池用量百分比
   - 批量查询功能
   - 批量停复机
   - 充值加油包
   - 出入库记录导出

---

## 🔔 注意事项

### 1. 账户余额系统
- 需要后端提供账户余额管理模块
- 需要支持充值、扣款、余额查询
- 需要记录余额变动日志
- 建议设置余额预警阈值（如：余额<100元时提醒）

---

## ✅ 已完成功能记录（2026-02-13更新）

### 一、核心模块开发完成

#### 1. 登录与认证模块 ✅
- 用户名/密码登录页面
- JWT Token 管理（存储、刷新、过期处理）
- 路由守卫（登录验证、权限校验）
- 超级登录功能（SuperLoginBanner组件）
- **文件**：`views/login/index.vue`、`stores/modules/auth.ts`、`router/guards.ts`、`api/modules/auth.ts`

#### 2. 仪表盘模块 ✅
- 统计卡片（卡片总数、流量池数、用户数、告警数）+ 点击跳转
- 运营商分布统计（移动/联通/电信）
- 账户余额显示（AccountBalance组件）
- 本月到期卡明细（ExpiringCardList组件）+ "查看全部"跳转
- 超套餐用量卡明细（OverUsageCardList组件）+ "查看全部"跳转
- 流量池用量百分比图表（PoolUsageChart组件）
- 告警列表（AlertList组件）
- **文件**：`views/dashboard/index.vue` 及 `components/` 下6个子组件

#### 3. 用户管理模块 ✅
- 用户列表（搜索、状态筛选）
- 创建/编辑用户（UserFormDialog）
- 重置密码（ResetPasswordDialog）
- 用户权限配置（UserPermissionDialog）
- 超级登录到下级账号
- **文件**：`views/users/index.vue` 及 `components/` 下3个子组件

#### 4. 权限管理模块 ✅
- 权限列表（按模块/关键词搜索）
- 创建/编辑/删除权限（PermissionFormDialog）
- 权限指令 v-permission
- **文件**：`views/permissions/index.vue`、`directives/permission.ts`、`api/modules/permission.ts`

#### 5. 套餐管理模块 ✅
- 底层套餐管理（搜索、运营商/周期筛选、创建/编辑）
- 销售套餐管理（关联底层套餐、定价）
- **文件**：`views/packages/supplier/index.vue`、`views/packages/sale/index.vue`、`api/modules/package.ts`

#### 6. 供应商管理模块 ✅
- 供应商列表（搜索、类型/状态筛选）
- 创建/编辑供应商（SupplierFormDialog）
- **文件**：`views/suppliers/index.vue`、`api/modules/supplier.ts`

#### 7. 出入库管理模块 ✅
- **卡片入库**：Excel模板上传、选择供应商/套餐、设置测试期/沉默期
- **卡片出库**：多步骤流程（选卡→配置→确认）、支持 period_count 套餐周期选择、card_type 卡类型选择（月包single/pool）、出库日期/测试期/沉默期配置、Excel批量出库导入
- **库存管理**：库存统计卡片、运营商分布、批量出库/回收入口
- **卡片回收**：回收规则提示、搜索/筛选、回收操作
- **出入库记录**：入库/出库记录Tab切换、筛选查询、按卡号查询 ✅
- **批次管理**：批次列表页面
- **API完整**：入库、出库、模板下载、批量导入、记录查询、导出、回收、库存查询等全部API已对接
- **文件**：`views/stock/in/`、`views/stock/out/`、`views/stock/inventory/`、`views/stock/recycle/`、`views/stock/records/`、`views/stock/batches/`、`api/modules/stock.ts`

#### 8. 卡片管理模块 ✅
- 卡片列表（统计卡片、关键词搜索、状态/运营商/周期/流量池筛选）
- **高级搜索**（可展开/收起）：关联客户（远程搜索）、备注关键词、出库单号、出库时间范围、激活时间范围、到期时间范围
- **批量查询**（BatchQueryDialog）：支持输入最多10000个ICCID，查询结果直接显示在主列表表格中（非弹窗），带橙色筛选提示栏，支持清除筛选
- 卡片详情页
- **批量划拨**（BatchTransferDialog）
- **批量备注**（BatchRemarkDialog）
- **批量续费**（BatchRenewDialog）：选择续费周期1/3/6/12个月
- **批量停机**（BatchSuspendDialog）：输入ICCID + 停机原因
- **批量复机**（BatchResumeDialog）：输入ICCID恢复
- 单卡划拨（TransferDialog）：打开时自动加载客户列表，支持空关键词搜索
- 单卡备注（RemarkDialog）
- 数据导出
- **UI优化**：表格网格线（border）、搜索框宽度优化（关键词293px、状态/运营商213px、周期/流量池187px）
- **数据格式优化**：流量显示简化（2G代替2.00GB、M代替MB）、使用百分比0位小数
- **文件**：`views/cards/list/index.vue` 及 `components/` 下8个子组件、`views/cards/detail/index.vue`、`api/modules/card.ts`

#### 9. 流量池管理模块 ✅
- 流量池列表（卡片式展示、搜索/运营商/状态筛选）
- 统计栏（总池数、启用/禁用数、告警数、总卡片数、总流量/已用流量）
- 流量池详情页
- 创建/编辑流量池（PoolFormDialog）
- 添加卡片到流量池（AddCardsDialog + CardSelectDialog）
- **充值加油包**（RechargeDialog）：选择加油包规格、显示价格/有效期、充值前后用量对比
- 卡片状态统计（card_stats：已激活/已停卡/库存/测试/已销卡）
- **文件**：`views/pools/list/index.vue` 及 `components/` 下4个子组件、`views/pools/detail/index.vue`、`api/modules/pool.ts`

#### 10. 停复机管理模块 ✅
- **停卡策略**：策略列表（到期/池超限/单卡超量）、创建/编辑策略、启用/禁用
- **停卡记录**：操作日志列表、按类型/时间筛选、批量停机/复机
- **告警管理**：告警列表、按目标类型/告警级别/处理状态筛选
- **API完整**：策略CRUD、批量停机/复机/强制激活、日志查询、告警查询/处理
- **文件**：`views/suspend/policy/`、`views/suspend/logs/`、`views/suspend/alerts/`、`api/modules/suspend.ts`

#### 11. 系统设置模块 ✅
- Tab式界面：系统配置、告警规则、登录日志、操作日志、通知模板
- 系统配置CRUD（ConfigPanel + ConfigFormDialog）
- 告警规则管理（AlertRulesPanel）
- 登录日志查询（LoginLogPanel）
- 操作日志查询（OperationLogPanel）
- 通知模板管理（NotifyTemplatePanel + NotifyTemplateFormDialog）
- **文件**：`views/system/index.vue` 及 `components/` 下6个子组件、`api/modules/system.ts`

#### 12. 续费管理模块 ✅
- 批量查询续费价格（输入ICCID，最多10000个）
- 查询结果表格（ICCID、号码、运营商、套餐规格、续费价格、状态、到期时间）
- 未找到ICCID告警提示
- Excel导出功能（纯前端，使用xlsx库）
- **文件**：`views/renewal/index.vue`、`api/modules/card.ts`

#### 13. 项目管理模块 ✅
- 项目列表（搜索、分页）
- 创建/编辑项目（ProjectFormDialog）
- 删除项目（二次确认）
- 项目信息：ID、名称、卡片数量、备注、创建时间
- 权限控制：用户仅可管理自己的项目
- **文件**：`views/projects/index.vue`、`views/projects/components/ProjectFormDialog.vue`、`api/modules/project.ts`、`types/project.d.ts`

### 二、基础设施完成

#### 14. 路由系统 ✅
- 24个路由页面全部配置完成（新增：续费管理、项目管理）
- 路由守卫（登录验证、权限校验、动态菜单）
- 路由懒加载
- **文件**：`router/routes.ts`、`router/guards.ts`、`router/index.ts`

#### 15. API层 ✅
- 13个API模块全部完成：auth、user、card、pool、package、stock、supplier、suspend、dashboard、menu、permission、system、project
- Axios封装（请求/响应拦截器、Token管理、错误处理）
- **文件**：`api/modules/` 下13个模块、`api/index.ts`

#### 16. 状态管理 ✅
- Auth Store（登录状态、Token管理、用户信息、权限缓存、超级登录）
- **文件**：`stores/modules/auth.ts`

#### 17. 布局与通用组件 ✅
- 主布局（MainLayout）
- 超级登录横幅（SuperLoginBanner）
- 权限指令（v-permission）
- 全局样式（variables.scss、reset.scss、global.scss）
- **文件**：`components/layout/MainLayout.vue`、`components/common/SuperLoginBanner.vue`、`directives/`

---

## 🚧 待完善/加强功能（按优先级排序）

> 以下功能虽然页面已创建，但部分细节可能需要验证和加强

### P0 - 需要验证和完善

#### 1. 出库功能细节验证 ⏳
- [ ] 验证 period_count 套餐周期选择是否与后端正确对接（月包3/6/12/24/36/50/60，年包1/2/3/5/6）
- [ ] 验证 card_type 卡类型选择逻辑（仅月包显示，年包默认single）
- [ ] 验证 Excel批量出库导入功能是否正常工作（模板下载、上传校验、错误报告）
- [ ] 验证出库日期/测试期/沉默期日期选择与后端格式一致

#### 2. 账户余额功能验证 ⏳
- [ ] 验证仪表盘 AccountBalance 组件是否正确调用后端API
- [ ] 验证余额预警阈值显示
- [ ] 验证充值入口跳转

#### 3. 套餐管理 package_id 字段 ⏳
- [ ] 验证底层套餐是否包含 `package_id` 字段
- [ ] 验证 `enable_auto_pool` 自动组池开关是否在表单中

---

### P1 - 功能加强

#### 4. 自动组流量池 ⏳
- [ ] 验证后端卡片激活时是否触发自动组池
- [ ] 验证流量池名称自动生成规则
- [ ] 处理并发激活情况

#### 5. 库存管理增强 ⏳
- [ ] 库存列表是否完整显示所有字段（运营商、ICCID、IMSI、电话号码、底套餐、入库日期、测试期、沉默期、供应商、备注）
- [ ] 是否支持按日期排序（正序/降序）
- [ ] 批量查询ICCID功能是否正常

#### 6. 出入库记录导出 ⏳
- [ ] 验证入库记录导出功能（Excel格式）
- [ ] 验证出库记录导出功能（Excel格式）

---

### P2 - 体验优化

#### 7. 表格虚拟滚动 ⏳
- [ ] 大数据量（>100条）表格是否启用虚拟滚动
- [ ] 卡片列表、库存列表等大表格性能优化

#### 8. 离线提示与网络监控 ⏳
- [ ] 网络断开时是否有提示
- [ ] 网络恢复时是否自动重连

#### 9. 表单离开未保存提示 ⏳
- [ ] 编辑表单时离开页面是否有未保存提示

#### 10. 快捷键支持 ⏳
- [ ] Ctrl+K 全局搜索
- [ ] Ctrl+R 刷新
- [ ] Esc 关闭弹窗

---

## 📊 开发进度统计

**总体进度**：17 / 17 个核心模块已完成前端开发（100%）

**已完成的核心模块**：
- ✅ 登录与认证
- ✅ 仪表盘（含账户余额、到期卡、超量卡、流量池用量图表）
- ✅ 用户管理（含超级登录、权限配置）
- ✅ 权限管理
- ✅ 套餐管理（底层套餐 + 销售套餐）
- ✅ 供应商管理
- ✅ 出入库管理（入库、出库、库存、回收、记录、批次）
- ✅ 卡片管理（含批量查询/划拨/备注/续费/停机/复机）
- ✅ 流量池管理（含充值加油包）
- ✅ 停复机管理（策略、记录、告警）
- ✅ 系统设置（配置、告警规则、日志、通知模板）
- ✅ 续费管理（批量查询续费价格、Excel导出）
- ✅ 项目管理（项目CRUD、卡片分组）
- ✅ 路由系统（24个页面）
- ✅ API层（13个模块）
- ✅ 状态管理
- ✅ 布局与通用组件

**待完善**：
- ⏳ 功能细节验证与后端联调（6项）
- ⏳ 体验优化（4项）

**当前阶段**：前端核心开发已完成，进入联调测试与细节完善阶段

---

## 🔄 下一步工作计划（2026-03-10更新）

**当前阶段**：前端核心模块开发已全部完成，进入联调测试与细节完善阶段。

### 最新修复记录（2026-03-10）

#### 1. 仪表盘运营商筛选功能 ✅
- **问题**：点击运营商卡片后，到期卡和超量卡列表未按运营商筛选
- **修复内容**：
  - 后端API添加 `carrier` 参数验证（仅允许 cmcc/cucc/ctcc）
  - 前端API添加 `carrier` 可选参数
  - 到期卡/超量卡组件支持 `carrier` props 并监听变化
  - 仪表盘添加"本月到期卡"和"超量卡"统计卡片，点击跳转并筛选
- **修改文件**：
  - `app/api/v1/dashboard.py` - 添加carrier参数验证
  - `app/services/dashboard_service.py` - 添加运营商筛选逻辑和统计字段
  - `app/schemas/dashboard.py` - CardStats添加expiring_count和over_usage_count
  - `frontend/src/api/modules/dashboard.ts` - API方法添加carrier参数
  - `frontend/src/views/dashboard/components/ExpiringCardList.vue` - 支持carrier筛选
  - `frontend/src/views/dashboard/components/OverUsageCardList.vue` - 支持carrier筛选
  - `frontend/src/views/dashboard/index.vue` - 添加统计卡片和类型定义
  - `frontend/src/views/cards/list/index.vue` - 支持URL参数筛选

**当前阶段**：前端核心模块开发已全部完成，进入联调测试与细节完善阶段。

### 优先级 P0：功能验证与联调

1. **各模块与后端API联调测试**
   - 逐模块验证数据是否正确显示
   - 验证所有表单提交是否成功
   - 验证错误处理是否正常

2. **出库功能细节确认**
   - period_count / card_type 与后端字段对接
   - Excel批量出库模板下载与导入

3. **仪表盘数据验证**
   - 账户余额、到期卡、超量卡、流量池用量图表数据是否真实

### 优先级 P1：体验优化

4. **性能优化**
   - 大数据量表格虚拟滚动
   - 请求取消（路由切换时）

5. **交互完善**
   - 表单离开未保存提示
   - 网络断开提示
   - 快捷键支持

---

## 📝 开发注意事项

### 1. 路由路径规范
- 所有路由跳转前先检查路由配置文件
- 使用完整路径（如 `/cards/list` 而非 `/cards`）
- 统一使用 `router.push()` 进行导航

### 2. API数据访问规范
- 响应拦截器已解包 `data.data`，组件中直接用 `res.items` 而非 `res.data.items`
- 所有API调用必须有 try-catch 和 loading 状态

### 3. 组件导入规范
- Composition API 必须导入：`useRouter`, `useRoute`, `ref`, `reactive`, `computed`

### 4. 测试验证规范
- 功能完成后必须在浏览器中测试
- 检查控制台是否有错误
- 检查网络请求是否正常

---

## 🆕 卡片管理优化记录（2026-02-27更新）

### 1. UI/UX 优化

#### 1.1 搜索框宽度调整
- 关键词输入框：293px
- 状态/运营商下拉：213px
- 周期/流量池下拉：187px

#### 1.2 表格优化
- 添加表格网格线（`border` 属性）
- 字体、间距、统计卡片样式优化

#### 1.3 数据格式优化
- 流量显示：`2G` 代替 `2.00GB`，`512M` 代替 `512MB`
- 使用百分比：0位小数（`Math.round`）
- 进度条百分比同步去除小数

### 2. 高级搜索功能（前后端联动）

#### 2.1 前端
- 可展开/收起的高级搜索区域（虚线分隔）
- 搜索字段：关联客户（远程搜索）、备注关键词、出库单号（batch_id）、出库时间范围、激活时间范围、到期时间范围
- 重置按钮同时清空高级搜索字段和日期范围
- `CardListParams` 类型扩展：`remark`, `customer_id`, `batch_id`, `stock_out_start/end`, `activated_start/end`, `expired_start/end`

#### 2.2 后端
- API 层（`iot_card.py`）：新增 Query 参数
- Service 层（`iot_card_service.py`）：透传参数
- CRUD 层（`iot_card_crud.py`）：remark LIKE 模糊搜索、customer_id/batch_id 精确匹配、日期范围过滤（stock_out_date、activated_at、expired_at）

### 3. 批量查询优化
- 查询结果直接显示在主列表表格中（非弹窗），可看到所有字段
- 橙色筛选提示栏显示查询结果数量和未找到数量
- 批量查询模式下隐藏分页
- 支持"清除筛选"恢复正常列表

### 4. 划拨对话框修复
- 打开时自动加载客户列表（`fetchUsers()` on dialog open）
- 支持空关键词搜索，解决"无目标客户可选"问题

### 5. 卡片详情页优化
- 基本信息区域：移除"入库时间"显示，新增"激活时间"、"沉默期到期"、"到期时间"字段
- 生命周期信息区域：移除重复的激活时间/沉默期到期/到期时间（已移至基本信息），仅保留测试期到期、停机时间、停机类型、停机原因
- 流量使用百分比：去除小数位（`.toFixed(2)` → `.toFixed(0)`）
- 进度条百分比：使用 `usagePercent.toFixed(0)` 替代 slot 的 `percentage`
- 剩余流量计算修复：`Math.max((data_total - data_used), 0)` 防止负数
- **文件**：`views/cards/detail/index.vue`

### 6. 续费管理模块（新增） ✅

#### 6.1 后端
- 新增 `POST /api/v1/cards/batch/renew-price-query` 接口
- 接收 `iccids: List[str]`（最多10000个）
- LEFT JOIN `sale_packages` 表获取 `price_sale`（续费价格/出库价格）
- 返回：`{ found: [...], not_found: [...] }`
- **文件**：`app/api/v1/iot_card.py`、`app/services/iot_card_service.py`

#### 6.2 前端
- 新增路由：`/renewal/management` → `RenewalManagement`
- 新增页面：`views/renewal/index.vue`
  - ICCID 批量输入（textarea，支持换行/逗号/空格分隔，最多10000个）
  - 查询结果表格：ICCID、号码、运营商、套餐规格、续费价格(¥)、状态、到期时间
  - 未找到 ICCID 告警提示
  - 下载 Excel 功能（纯前端导出，使用 xlsx 库）
- 新增 API 方法：`cardApi.queryRenewPrice(iccids)`
- MainLayout 图标映射：`'renewal': Money`
- 数据库菜单记录：`sys_menus` (id=75) + `sys_user_menus` 关联
- **文件**：`views/renewal/index.vue`、`router/routes.ts`、`api/modules/card.ts`、`components/layout/MainLayout.vue`

### 7. 项目管理模块（新增） ✅

#### 7.1 功能概述
- 用户可创建项目对卡片进行分组管理
- 支持为卡片关联项目，便于按项目维度统计和查询
- 项目与用户绑定，仅可管理自己的项目

#### 7.2 后端实现
- 数据库表：`projects` (id, name, user_id, remark, card_count, created_at, updated_at)
- API 接口：
  - `GET /api/v1/projects` - 项目列表（分页、关键词搜索）
  - `GET /api/v1/projects/all` - 所有项目（下拉选择用）
  - `GET /api/v1/projects/{id}` - 项目详情
  - `POST /api/v1/projects` - 创建项目
  - `PUT /api/v1/projects/{id}` - 更新项目
  - `DELETE /api/v1/projects/{id}` - 删除项目
- 权限控制：用户仅可操作自己创建的项目
- **文件**：`app/api/v1/project.py`、`app/schemas/project.py`、`app/crud/project_crud.py`、`app/db/models/project.py`

#### 7.3 前端实现
- 新增路由：`/projects` → `Projects`
- 新增页面：`views/projects/index.vue`
  - 搜索栏：项目名称关键词搜索
  - 操作栏：新增项目按钮
  - 项目列表表格：ID、项目名称、卡片数量、备注、创建时间、操作（编辑/删除）
  - 分页组件
- 新增组件：`views/projects/components/ProjectFormDialog.vue`（创建/编辑项目表单弹窗）
- 新增 API 模块：`api/modules/project.ts`
- 新增类型定义：`types/project.d.ts`
- MainLayout 图标映射：`'projects': FolderOpened`
- 数据库菜单记录：`sys_menus` (id=76) + `sys_user_menus` 关联
- **文件**：`views/projects/index.vue`、`views/projects/components/ProjectFormDialog.vue`、`router/routes.ts`、`api/modules/project.ts`、`types/project.d.ts`

#### 7.4 数据结构
```typescript
interface Project {
  id: number
  name: string              // 项目名称
  user_id: number           // 所属用户ID
  remark?: string           // 备注
  card_count: number        // 关联卡片数量
  created_at?: string
  updated_at?: string
}
```

