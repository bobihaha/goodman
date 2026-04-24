# 物联网卡管理平台 - 前端需求文档

> **版本**：v2.0 精简版 | **最后更新**：2026-03-10

---

## ⚠️ 重要规则

### 🚫 严禁使用模拟数据（Mock Data）

**强制要求**：
1. ❌ 禁止硬编码任何业务数据
2. ❌ 禁止使用 Mock.js 或模拟数据工具
3. ✅ 所有数据必须通过后端API获取
4. ✅ 前端字段名称格式必须和后端一致
5. ✅ 原则上不许修改后端代码，需询问得到许可

**开发流程**：
1. 确认后端API已开发完成
2. 查看API文档，确认请求/响应格式
3. 使用Postman/Apifox测试API
4. 前端对接真实API
5. 处理加载、错误、空状态

---

## 📌 项目概述

基于 **Vue 3.4+ / TypeScript 5.x / Element Plus** 的物联网卡管理平台前端，支持三级多租户 SaaS 架构。

**技术栈**：
- Vue 3.4+ (Composition API + `<script setup>`)
- TypeScript 5.x (严格模式)
- Element Plus 2.5+
- Pinia 2.1+ (状态管理)
- Vue Router 4.x
- Axios 1.6+
- Vite 5.x
- ECharts 5.4+ (数据可视化)

**核心优化策略**：
- ✅ 类型安全：100% TypeScript覆盖
- ✅ 错误边界：全局错误捕获 + 组件级错误处理
- ✅ 防抖节流：所有搜索/提交操作防抖
- ✅ 数据校验：前后端双重验证
- ✅ 加载状态：骨架屏 + 进度条

---

## 🎨 设计原则

### 视觉设计
- **主题色**：#1890ff (蓝色)
- **成功**：#52c41a (绿色)
- **警告**：#faad14 (橙色)
- **危险**：#ff4d4f (红色)

### 交互原则
- ✅ 危险操作二次确认
- ✅ 表单离开前未保存提示
- ✅ 输入框实时校验
- ✅ 操作成功：Toast提示（3秒）
- ✅ 操作失败：详细错误信息

---

## 🎯 核心功能模块

### 1. 登录与认证
**页面**: `/login`

**功能**：
- 用户名/密码登录
- JWT Token 管理
- Token 自动刷新

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
- 流量使用趋势图
- 账户余额显示
- 本月到期卡明细
- 超套餐用量卡明细
- 流量池用量百分比

**API**：
```typescript
GET /api/v1/dashboard/overview
GET /api/v1/dashboard/cards/stats
GET /api/v1/dashboard/cards/expiring?carrier=cmcc
GET /api/v1/dashboard/cards/over-usage?carrier=cucc
```

---

### 3. 用户管理
**页面**: `/users`

**功能**：
- 用户列表（树形结构）
- 创建/编辑用户
- 重置密码
- 超级登录（切换到下级账号）
- 权限管理

**表单字段**：
```typescript
{
  username: string
  password: string
  real_name: string
  phone?: string
  email?: string
  user_level: 1 | 2 | 3
  parent_id?: number
  status: 'enable' | 'disable'
}
```

**API**：
```typescript
GET    /api/v1/users
POST   /api/v1/users
PUT    /api/v1/users/{id}
POST   /api/v1/auth/super-login
```

---

### 4. 套餐管理

#### 4.1 底层套餐
**页面**: `/packages/supplier`

**表单字段**：
```typescript
{
  package_id: string
  name: string
  carrier: 'cmcc' | 'cucc' | 'ctcc'
  flow_size: number  // MB
  period_type: 'monthly' | 'yearly'
  valid_days: number
  cost_price: number
  supplier_id: number
  enable_auto_pool: boolean
}
```

#### 4.2 销售套餐
**页面**: `/packages/sale`

**表单字段**：
```typescript
{
  package_id: string
  name: string
  supplier_package_id: number
  sale_price: number
  user_id?: number  // 专属客户
}
```

**API**：
```typescript
GET  /api/v1/packages/supplier
POST /api/v1/packages/supplier
GET  /api/v1/packages/sale
POST /api/v1/packages/sale
```

---

### 5. 出入库管理

**本次增补（2026-04-24）**：
- 新增卡片主数据字段 `material`（材质），用于标识卡片物理形态
- 入库时必须选择材质，并随本次入库的全部卡片一起写入
- 出库页、库存管理页、卡片列表页增加“材质”展示列，便于用户识别卡片类型
- 材质选项固定为：
  - `plastic_plug`: 塑料插拔卡
  - `industrial_plug_large`: 工业插拔大卡
  - `industrial_plug_medium`: 工业插拔中卡
  - `industrial_plug_small`: 工业插拔小卡
  - `standard_smd_5_6`: 普通5*6贴片卡
  - `industrial_smd_5_6`: 工业5*6贴片卡

#### 5.1 卡片入库
**页面**: `/stock/in`

**功能**：
- Excel模板上传
- 选择供应商/套餐
- 选择材质
- 设置测试期/沉默期

**表单字段**：
```typescript
{
  supplier_id: number
  package_id: number
  material: 'plastic_plug' | 'industrial_plug_large' | 'industrial_plug_medium' | 'industrial_plug_small' | 'standard_smd_5_6' | 'industrial_smd_5_6'
  test_expire_date?: string  // YYYY-MM-DD
  silent_expire_date: string // YYYY-MM-DD
  file: File
}
```

**交互要求**：
- 材质为必填项，默认不选，必须由操作人显式选择
- 同一次入库中的全部卡片共用同一个材质
- 确认入库页需展示当前选中的材质
- 卡片创建成功后，材质写入卡片主表，并同步记录到采购批次，便于后续追溯

#### 5.2 卡片出库
**页面**: `/stock/out`

**功能**：
- 选择库存卡片
- 选择目标用户/销售套餐
- 套餐周期选择（月包/年包）
- 卡类型选择（仅月包：single/pool）
- Excel批量出库
- 卡片列表展示材质列

**表单字段**：
```typescript
{
  card_ids: number[]
  user_id: number
  sale_package_id: number
  period_count: number
  card_type?: 'single' | 'pool'
  stock_out_date: string
  test_expire_date?: string
  silent_expire_date: string
}
```

**API**：
```typescript
POST /api/v1/stock/in
POST /api/v1/stock/out
GET  /api/v1/stock/inventory
POST /api/v1/stock/recycle
GET  /api/v1/stock/records/card
```

**列表展示要求**：
- 出库选卡列表新增 `material_name`
- 出库确认页卡片列表新增“材质”列
- 字段来源必须为卡片主数据，不允许前端本地推断

#### 5.3 库存管理补充
**页面**: `/stock/inventory`

**补充功能**：
- 库存卡片列表新增“材质”列
- 批量查询结果弹窗同步展示“材质”列
- 字段来源为库存卡片的 `material_name`

---

### 6. 卡片管理
**页面**: `/cards/list`

**功能**：
- 卡片列表（分页、筛选）
- 快速搜索（ICCID/IMSI/MSISDN）
- 批量查询（最多10000个ICCID）
- 高级搜索（备注、客户、出库单号、日期范围）
- 批量操作（划拨/备注/续费/停机/复机）
- 列表支持展示卡片材质

**表格字段**：
```typescript
{
  id: number
  iccid: string
  msisdn: string
  carrier: 'cmcc' | 'cucc' | 'ctcc'
  status: 'stock' | 'testing' | 'silent' | 'activated' | 'expired' | 'suspended'
  data_used: number  // MB
  data_total: number // MB
  flow_size: number
  period_type: 'monthly' | 'yearly'
  material: 'plastic_plug' | 'industrial_plug_large' | 'industrial_plug_medium' | 'industrial_plug_small' | 'standard_smd_5_6' | 'industrial_smd_5_6'
  material_name: string
  activated_at: string
  expired_at: string
  pool_id: number
  remark: string
}
```

**展示要求**：
- 卡片列表新增“材质”列，支持列显示开关和列顺序配置
- 返回值同时提供 `material` 与 `material_name`
- 页面默认展示 `material_name`

**API**：
```typescript
GET  /api/v1/cards
POST /api/v1/cards/batch-query
POST /api/v1/cards/batch/transfer
POST /api/v1/cards/batch/renew
POST /api/v1/cards/batch-suspend
POST /api/v1/cards/export
```

---

### 7. 流量池管理
**页面**: `/pools/list`

**功能**：
- 流量池列表
- 创建/编辑流量池
- 添加/移除卡片
- 充值加油包
- 用量统计

**表单字段**：
```typescript
{
  name: string
  carrier: 'cmcc' | 'cucc' | 'ctcc'
  flow_size: number
  period_type: 'monthly' | 'yearly'
  alert_threshold?: number  // %
  stop_threshold?: number   // %
}
```

**API**：
```typescript
GET    /api/v1/pools
POST   /api/v1/pools
POST   /api/v1/pools/{id}/cards
DELETE /api/v1/pools/{id}/cards
POST   /api/v1/pools/{id}/recharge
```

---

### 8. 停复机管理
**页面**: `/suspend/policy`, `/suspend/logs`, `/suspend/alerts`

**功能**：
- 停卡策略管理
- 手动停机/复机
- 停卡记录查询
- 告警管理

**API**：
```typescript
GET  /api/v1/suspend/policies
POST /api/v1/suspend/cards/suspend
POST /api/v1/suspend/cards/resume
GET  /api/v1/suspend/logs
GET  /api/v1/suspend/alerts
```

---

## 📊 前后端字段映射

### 卡片字段

| 前端字段 | 后端字段 | 类型 | 说明 |
|---------|---------|------|------|
| id | id | number | 卡片ID |
| iccid | iccid | string | ICCID（19-20位） |
| msisdn | msisdn | string | 号码 |
| carrier | carrier | enum | 运营商 |
| status | status | enum | 状态 |
| dataUsed | data_used | number | 已用流量(MB) |
| dataTotal | data_total | number | 总流量(MB) |
| activatedAt | activated_at | string | 激活日期 |
| expiredAt | expired_at | string | 到期日期 |
| poolId | pool_id | number | 流量池ID |

**命名规范**：
- 后端：snake_case
- 前端：camelCase
- 前端API层负责转换

---

## 🔧 核心优化方案

### 1. 错误处理
```typescript
// 全局错误捕获
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
```

### 2. 表单验证
```typescript
// 统一验证规则
const validators = {
  iccid: (rule, value, callback) => {
    if (!/^\d{19,20}$/.test(value)) {
      callback(new Error('ICCID格式错误'))
    } else {
      callback()
    }
  }
}
```

### 3. 防抖节流
```typescript
// 搜索防抖
import { useDebounceFn } from '@vueuse/core'

const debouncedSearch = useDebounceFn(async () => {
  await fetchData()
}, 500)
```

---

## ✅ API对接检查清单

### 开发前
- [ ] 确认后端API已开发完成
- [ ] 获取API文档
- [ ] 使用Postman测试API
- [ ] 确认字段命名规范
- [ ] 确认日期格式

### 开发中
- [ ] 所有API调用都有loading状态
- [ ] 所有API调用都有错误处理
- [ ] 所有表单都有前端验证
- [ ] 所有危险操作都有二次确认

### 测试
- [ ] 测试正常流程
- [ ] 测试异常流程（401、403、500）
- [ ] 测试边界情况（空数据、大数据量）

---

## 📝 数据格式化

### 日期格式
- 显示：`26/1/31` (YY/M/D)
- 存储：`2026-01-31` (YYYY-MM-DD)

### 流量单位
- 显示：2G、512M（无小数）
- 存储：统一使用 MB

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
  suspended: { label: '已停机', type: 'danger' }
}
```

---

## 📞 文档说明

**完整版文档**：`docs/archive/FRONTEND_PRD_FULL.md`（包含所有历史记录和详细说明）

**变更日志**：`docs/archive/CHANGELOG.md`

**已完成功能**：`docs/archive/COMPLETED_FEATURES.md`

**开发指南**：`docs/DEVELOPMENT_GUIDE.md`
