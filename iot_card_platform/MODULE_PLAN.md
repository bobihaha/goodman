# 物联网卡管理平台 - 模块规划

> **版本**：v2.0 精简版 | **最后更新**：2026-03-10

---

## 📌 项目概述

基于 **Python + FastAPI** 的物联网卡管理平台后端，支持三级多租户 SaaS 架构。

**业务流程**：从供应商采购物联网卡底层套餐 → 重新包装销售给客户 → 通过供应商 API 实时同步流量消耗。

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        物联网卡管理平台                           │
├─────────────────────────────────────────────────────────────────┤
│  前端层 (Vue3 + TypeScript)                                      │
│  ├── 超级管理员后台                                               │
│  ├── 代理商/用户后台                                              │
│  └── 子用户后台                                                   │
├─────────────────────────────────────────────────────────────────┤
│  API网关层 (FastAPI)                                             │
│  ├── 认证鉴权 (JWT)                                               │
│  ├── 权限控制 (RBAC)                                              │
│  └── 请求路由                                                     │
├─────────────────────────────────────────────────────────────────┤
│  业务服务层                                                       │
│  ├── 用户服务      ├── 卡片服务      ├── 套餐服务                  │
│  ├── 流量池服务    ├── 出入库服务    └── 供应商对接服务             │
├─────────────────────────────────────────────────────────────────┤
│  数据层                                                          │
│  ├── MySQL 8.x (主数据)                                          │
│  ├── Redis (缓存/会话)                                           │
│  └── 文件存储 (日志/导出)                                         │
├─────────────────────────────────────────────────────────────────┤
│  外部接口层                                                       │
│  └── 供应商 API (流量同步/停复机)                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 👥 多租户架构 (三级)

| 级别 | 角色 | 权限范围 |
|------|------|----------|
| **Level 1** | 超级管理员 | 全平台管理，创建/管理用户，超级登录用户账号 |
| **Level 2** | 用户/代理商 | 管理自己的卡片和子用户，超级登录子用户账号 |
| **Level 3** | 子用户 | 仅查看被分配的卡片数据 |

**数据隔离策略**：
- 物理隔离：通过 `parent_id` 实现层级关系
- 权限隔离：根据 `user_level` 动态显示菜单

---

## 🎯 模块职责划分

```
┌─────────────────────────────────────────────────────────────────┐
│                    超级管理员 (平台侧)                           │
├─────────────────────────────────────────────────────────────────┤
│  套餐管理模块                                                    │
│  ├── 底层套餐 → 采购成本管理 (规格: 运营商+流量+周期)              │
│  └── 销售套餐 → 定价销售管理                                     │
├─────────────────────────────────────────────────────────────────┤
│  出入库模块                                                      │
│  ├── 卡入库 → 关联供应商+底层套餐+生命周期日期                    │
│  └── 卡出库 → 分配给用户，关联销售套餐                            │
├─────────────────────────────────────────────────────────────────┤
│  数据同步模块                                                    │
│  ├── 同步流量使用情况 (调用供应商API)                             │
│  └── 同步生命周期日期 (测试期/沉默期/激活日/过期日)                │
└─────────────────────────────────────────────────────────────────┘
                            ↓ 出库后
┌─────────────────────────────────────────────────────────────────┐
│                    用户/代理商 (客户侧)                          │
├─────────────────────────────────────────────────────────────────┤
│  卡片管理模块                                                    │
│  ├── 查看自己的卡片列表和详情                                     │
│  ├── 查看卡状态/流量使用情况                                      │
│  ├── 按 ICCID/后6位 搜索卡片                                     │
│  ├── 划拨卡给子用户                                              │
│  ├── 自定义备注 (单卡/批量)                                       │
│  └── 导出卡片数据                                                │
├─────────────────────────────────────────────────────────────────┤
│  流量池模块                                                      │
│  ├── 创建流量池 (相同规格卡组池共享)                              │
│  └── 查看池用量统计                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 核心模块与API端点

### 模块 1: 认证与用户管理 ✅

**功能**：三级用户体系、JWT认证、超级登录、权限管理

**API 端点**：
```
POST   /api/v1/auth/login           # 登录
POST   /api/v1/auth/logout          # 登出
POST   /api/v1/auth/refresh         # 刷新Token
POST   /api/v1/auth/super-login     # 超级登录
GET    /api/v1/auth/profile         # 当前用户信息

GET    /api/v1/users                # 用户列表
POST   /api/v1/users                # 创建用户
PUT    /api/v1/users/{id}           # 更新用户
DELETE /api/v1/users/{id}           # 删除用户
PUT    /api/v1/users/{id}/password  # 修改密码

GET    /api/v1/permissions          # 权限列表
GET    /api/v1/menus                # 菜单列表
```

---

### 模块 2: 套餐管理 ✅

**规格三要素**: 运营商 + 流量 + 周期类型

**API 端点**：
```
# 底层套餐 (超级管理员)
GET    /api/v1/packages/supplier          # 底层套餐列表
POST   /api/v1/packages/supplier          # 创建底层套餐
PUT    /api/v1/packages/supplier/{id}     # 更新底层套餐
DELETE /api/v1/packages/supplier/{id}     # 删除底层套餐

# 销售套餐 (超级管理员+用户)
GET    /api/v1/packages/sale              # 销售套餐列表
POST   /api/v1/packages/sale              # 创建销售套餐
PUT    /api/v1/packages/sale/{id}         # 更新销售套餐
DELETE /api/v1/packages/sale/{id}         # 删除销售套餐
```

---

### 模块 3: 出入库管理 ✅

**卡片生命周期**：
```
采购入库 → 测试期(可选) → 沉默期 → 激活使用 → 到期停卡 → 销卡
```

**API 端点**：
```
# 入库
POST   /api/v1/stock/in                   # 批量入库
GET    /api/v1/stock/in/records           # 入库记录列表

# 出库
POST   /api/v1/stock/out                  # 批量出库
GET    /api/v1/stock/out/records          # 出库记录列表

# 库存管理
GET    /api/v1/stock/summary              # 库存统计
GET    /api/v1/stock/inventory            # 库存卡片列表
POST   /api/v1/stock/inventory/batch-query # 批量查询卡片
POST   /api/v1/stock/inventory/export     # 导出库存数据

# 卡片回收
POST   /api/v1/stock/recycle              # 卡片回收
GET    /api/v1/stock/recycle/records      # 回收记录列表

# 数据同步
POST   /api/v1/sync/usage                 # 同步流量用量
POST   /api/v1/sync/lifecycle             # 同步生命周期日期
POST   /api/v1/sync/cards/{iccid}         # 同步单卡信息
GET    /api/v1/sync/logs                  # 同步日志
```

---

### 模块 4: 卡片管理 ✅

**功能**：卡片列表、搜索、划拨、备注、导出

**API 端点**：
```
GET    /api/v1/cards                      # 我的卡片列表
GET    /api/v1/cards/{id}                 # 卡片详情
GET    /api/v1/cards/search               # 快速搜索
GET    /api/v1/cards/stats                # 卡片统计

POST   /api/v1/cards/{id}/transfer        # 单卡划拨
POST   /api/v1/cards/batch/transfer       # 批量划拨

PUT    /api/v1/cards/{id}/remark          # 单卡备注
PUT    /api/v1/cards/batch/remark         # 批量备注

POST   /api/v1/cards/export               # 导出卡片数据
POST   /api/v1/cards/batch/renew-price-query  # 批量查询续费价格
```

---

### 模块 5: 流量池管理 ✅

**组池规则**: 相同规格 (运营商+流量+周期) 的已激活卡可组池共享

**API 端点**：
```
GET    /api/v1/pools                      # 流量池列表
POST   /api/v1/pools                      # 创建流量池
GET    /api/v1/pools/{id}                 # 流量池详情
PUT    /api/v1/pools/{id}                 # 更新流量池
DELETE /api/v1/pools/{id}                 # 删除流量池

GET    /api/v1/pools/{id}/cards           # 池内卡片列表
POST   /api/v1/pools/{id}/cards           # 添加卡片到池
DELETE /api/v1/pools/{id}/cards           # 批量移除卡片

GET    /api/v1/pools/{id}/usage           # 流量池用量统计
GET    /api/v1/pools/{id}/logs            # 操作日志
```

---

### 模块 6: 停复机管理 ✅

**停卡类型**：到期停卡、手动停卡、流量池超限、单卡超量

**API 端点**：
```
# 停卡策略
GET    /api/v1/suspend/policies              # 策略列表
POST   /api/v1/suspend/policies              # 创建策略
PUT    /api/v1/suspend/policies/{id}         # 更新策略
DELETE /api/v1/suspend/policies/{id}         # 删除策略

# 手动操作
POST   /api/v1/suspend/cards/suspend         # 手动停卡
POST   /api/v1/suspend/cards/resume          # 手动复机

# 停卡记录
GET    /api/v1/suspend/logs                  # 停卡记录列表

# 告警管理
GET    /api/v1/suspend/alerts                # 告警列表
GET    /api/v1/suspend/alerts/stats          # 告警统计
POST   /api/v1/suspend/alerts/{id}/handle    # 处理告警
```

---

### 模块 7: 供应商管理 ✅

**功能**：供应商信息管理、API配置、同步间隔配置

**API 端点**：
```
GET    /api/v1/suppliers                  # 供应商列表
POST   /api/v1/suppliers                  # 添加供应商
GET    /api/v1/suppliers/{id}             # 供应商详情
PUT    /api/v1/suppliers/{id}             # 更新供应商
DELETE /api/v1/suppliers/{id}             # 删除供应商
POST   /api/v1/suppliers/{id}/test        # 测试API连通性
```

---

### 模块 8: 仪表盘 ✅

**功能**：卡片统计、流量趋势、到期卡明细、超量卡明细、告警消息

**API 端点**：
```
GET    /api/v1/dashboard/overview         # 总览数据
GET    /api/v1/dashboard/cards/stats      # 卡片统计
GET    /api/v1/dashboard/usage/trend      # 流量趋势
GET    /api/v1/dashboard/pools/stats      # 流量池统计
GET    /api/v1/dashboard/users/stats      # 用户统计
GET    /api/v1/dashboard/alerts           # 告警消息
GET    /api/v1/dashboard/activities       # 最近活动
GET    /api/v1/dashboard/cards/expiring?carrier=cmcc   # 到期卡明细
GET    /api/v1/dashboard/cards/over-usage?carrier=cucc # 超量卡明细
```

---

### 模块 9: 系统设置 ✅

**功能**：系统配置、操作日志、登录日志、告警规则、通知模板

**API 端点**：
```
# 系统配置
GET    /api/v1/system/configs             # 获取系统配置列表
PUT    /api/v1/system/configs/{key}       # 更新配置
PUT    /api/v1/system/configs             # 批量更新配置

# 日志查询
GET    /api/v1/system/logs/login          # 登录日志
GET    /api/v1/system/logs/operation      # 操作日志

# 告警规则
GET    /api/v1/system/alerts/rules        # 获取告警规则
PUT    /api/v1/system/alerts/rules        # 更新告警规则

# 通知模板
GET    /api/v1/system/notify/templates           # 模板列表
POST   /api/v1/system/notify/templates           # 创建模板
PUT    /api/v1/system/notify/templates/{id}      # 更新模板
DELETE /api/v1/system/notify/templates/{id}      # 删除模板
```

---

### 模块 10: 项目管理 ✅

**功能**：项目分组管理、卡片关联

**API 端点**：
```
GET    /api/v1/projects                   # 项目列表
GET    /api/v1/projects/all               # 所有项目(下拉选择)
GET    /api/v1/projects/{id}              # 项目详情
POST   /api/v1/projects                   # 创建项目
PUT    /api/v1/projects/{id}              # 更新项目
DELETE /api/v1/projects/{id}              # 删除项目
```

---

## 🛠️ 技术栈

| 类型 | 技术 |
|------|------|
| **后端框架** | FastAPI |
| **数据库** | MySQL 8.4.7 |
| **ORM** | SQLAlchemy 2.x (异步) |
| **缓存** | Redis |
| **认证** | JWT (PyJWT) |
| **密码加密** | Bcrypt |
| **数据验证** | Pydantic v2 |
| **异步任务** | APScheduler |
| **日志** | Loguru |
| **容器化** | Docker + Docker Compose |

---

## 📚 相关文档

- **数据库设计**：[docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)
- **系统架构**：[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **开发指南**：[docs/DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md)
- **前端需求**：[FRONTEND_PRD.md](FRONTEND_PRD.md)
- **完整版文档**：[docs/archive/MODULE_PLAN_FULL.md](docs/archive/MODULE_PLAN_FULL.md)
