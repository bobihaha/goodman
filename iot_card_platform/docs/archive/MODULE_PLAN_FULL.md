# 物联网卡管理平台 - 模块规划

## 📌 项目概述

基于 **Python + FastAPI** 的物联网卡管理平台后端，支持三级多租户 SaaS 架构。

**业务流程**：从供应商采购物联网卡底层套餐 → 重新包装销售给客户 → 通过供应商 API 实时同步流量消耗。

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        物联网卡管理平台                           │
├─────────────────────────────────────────────────────────────────┤
│  前端层 (Vue3/React)                                             │
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
│  ├── 中国移动 API    ├── 中国联通 API    ├── 中国电信 API          │
│  └── 第三方供应商 API                                             │
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
- 权限隐藏：根据 `user_level` 动态显示菜单

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

## 📦 核心模块规划

### 模块 1: 多租户 + 用户权限管理 ✅ 已完成

**功能**：
- [x] 三级用户体系 (超级管理员/用户/子用户)
- [x] 用户 CRUD (创建/读取/更新/删除)
- [x] JWT 认证 + 权限校验
- [x] 超级登录 (无密码切换下级账号)
- [x] 动态菜单权限
- [x] 二级用户默认配置 (2026-03-10)：
  - 默认权限模块：dashboard, user, card, package, pool, system
  - 默认菜单：dashboard, users, cards, renewal, pools, system_config
  - 默认通知：短信和邮件通知开启
  - 默认配额：max_cards=100, max_sub_users=5, pool_stop_threshold=100

**API 端点**：
```
POST   /api/v1/auth/login           # 登录
POST   /api/v1/auth/logout          # 登出
POST   /api/v1/auth/refresh         # 刷新Token
POST   /api/v1/auth/super-login     # 超级登录
GET    /api/v1/auth/profile         # 当前用户信息
GET    /api/v1/auth/permissions     # 当前权限列表

GET    /api/v1/users                # 用户列表
POST   /api/v1/users                # 创建用户
GET    /api/v1/users/{id}           # 用户详情
PUT    /api/v1/users/{id}           # 更新用户
DELETE /api/v1/users/{id}           # 删除用户
PUT    /api/v1/users/{id}/password  # 修改密码
PUT    /api/v1/users/{id}/status    # 启用/禁用

GET    /api/v1/menus                # 菜单列表
GET    /api/v1/menus/user/{id}      # 用户菜单权限
PUT    /api/v1/menus/user/{id}      # 设置用户菜单
```

---

### 模块 2: 套餐管理 ✅ 已完成

**规格三要素**: 运营商 + 流量 + 周期类型

**套餐规格示例**：
| 规格名称 | 运营商 | 流量 | 周期 | 有效天数 |
|----------|--------|------|------|----------|
| 移动1G/月 | cmcc | 1024MB | monthly | 30天 |
| 移动5G/月 | cmcc | 5120MB | monthly | 30天 |
| 联通1G/年 | cucc | 1024MB | yearly | 360天 |

**功能**：
- [x] 底层套餐管理 (供应商采购成本)
- [x] 销售套餐管理 (客户销售定价)
- [x] 规格标准化 (运营商+流量+周期)
- [x] 有效期配置 (月包30天/年包360天)
- [x] 专属客户关联 (2026-03-06 修复：编辑时客户字段显示问题)
- [x] 客户搜索功能 (2026-03-06 新增：按客户名称/账户搜索套餐)
- [x] 权限控制优化 (2026-03-06 修复：出库时根据目标用户过滤套餐)

**API 端点**：
```
# 底层套餐 (超级管理员)
GET    /api/v1/packages/supplier          # 底层套餐列表
POST   /api/v1/packages/supplier          # 创建底层套餐
GET    /api/v1/packages/supplier/{id}     # 套餐详情
PUT    /api/v1/packages/supplier/{id}     # 更新底层套餐
DELETE /api/v1/packages/supplier/{id}     # 删除底层套餐

# 销售套餐 (超级管理员+用户)
GET    /api/v1/packages/sale              # 销售套餐列表
POST   /api/v1/packages/sale              # 创建销售套餐
GET    /api/v1/packages/sale/{id}         # 套餐详情
PUT    /api/v1/packages/sale/{id}         # 更新销售套餐
DELETE /api/v1/packages/sale/{id}         # 删除销售套餐
```

---

### 模块 3: 出入库管理 ✅ 已完成

**卡片生命周期**：
```
采购入库 → 测试期(可选) → 沉默期 → 激活使用 → 到期停卡 → 销卡
          ↑              ↑        ↑
          可能没有       一定有    超期会强制激活
```

**功能**：

**入库操作**：
- [x] 批量导入卡片 (Excel/CSV: ICCID, IMSI, MSISDN)
- [x] 关联供应商 + 底层套餐
- [x] 设置测试期截止日期 (可选，如: 26/1/31)
- [x] 设置沉默期截止日期 (必填，如: 26/4/30)
- [x] Excel模板下载功能
- [x] 格式校验和详细错误提示

**出库操作**：
- [x] 选择库存卡片
- [x] 选择目标用户/代理商
- [x] 选择销售套餐 (定价)
- [x] 确认出库
- [x] 生成出库单

**库存管理**：
- [x] 库存统计 (按供应商/套餐/运营商)
- [x] 出入库记录查询
- [x] 批量查询功能 (最多10000个ICCID)
- [x] 高级筛选和排序
- [x] 导出功能 (Excel格式)

**卡片回收**：
- [x] 已出库卡片回收
- [x] 回收原因记录
- [x] 二次确认机制
- [x] 回收记录查询

**数据同步 (调用供应商API)**：
- [x] 批量同步流量使用情况 (单位: MB)
- [x] 自动更新卡片状态和日期 (激活日/过期日)
- [x] 定时任务调度器 (APScheduler)
- [x] 生命周期同步状态检查 (2026-03-06 修复：同步后调用状态检查逻辑)

**API 端点**：
```
# 入库
POST   /api/v1/stock/in                   # 批量入库 (导入卡片) ✅
GET    /api/v1/stock/in/records           # 入库记录列表 ✅
GET    /api/v1/stock/in/records/{id}      # 入库单详情 ✅
POST   /api/v1/stock/in/records/export    # 导出入库记录 ✅

# 出库
POST   /api/v1/stock/out                  # 批量出库 ✅
GET    /api/v1/stock/out/records          # 出库记录列表 ✅
GET    /api/v1/stock/out/records/{id}     # 出库单详情 ✅
POST   /api/v1/stock/out/records/export   # 导出出库记录 ✅

# 卡片回收
POST   /api/v1/stock/recycle              # 卡片回收 ✅
GET    /api/v1/stock/recycle/records      # 回收记录列表 ✅

# 库存管理
GET    /api/v1/stock/summary              # 库存统计 ✅
GET    /api/v1/stock/inventory            # 库存卡片列表 ✅
POST   /api/v1/stock/inventory/batch-query # 批量查询卡片 ✅
POST   /api/v1/stock/inventory/export     # 导出库存数据 ✅
GET    /api/v1/stock/records/card         # 按卡号查询出入库记录 ✅

# Excel模板
GET    /api/v1/stock/import-template      # 下载Excel导入模板 ✅

# 数据同步
POST   /api/v1/sync/usage                 # 同步流量用量
POST   /api/v1/sync/lifecycle             # 同步生命周期日期
POST   /api/v1/sync/cards/{iccid}         # 同步单卡信息
GET    /api/v1/sync/logs                  # 同步日志
```

**前端页面**：
- ✅ `/stock/in` - 卡片入库页面
- ✅ `/stock/out` - 卡片出库页面
- ✅ `/stock/inventory` - 库存管理页面
- ✅ `/stock/recycle` - 卡片回收页面
- ✅ `/stock/records` - 出入库记录页面

**开发文档**：
- 📄 `STOCK_MODULE_SUMMARY.md` - 模块开发总结文档

---

### 模块 4: 卡片管理 ✅ 已完成

**模块定位**: 用户/代理商管理自己的卡片

**功能**：

**查询**：
- [x] 卡片列表 (分页、筛选)
- [x] 按 ICCID/IMSI/MSISDN 查询
- [x] 支持后6位模糊查询
- [x] 按状态/套餐/运营商筛选
- [x] 高级搜索：备注模糊搜索、关联客户、出库单号、出库/激活/到期时间范围

**查看**：
- [x] 卡片详情 (状态/流量/到期日)
- [x] 流量使用情况 (已用/剩余，单位M)
- [x] 生命周期日期 (格式: 26/1/31)
- [x] 划拨记录查询

**操作**：
- [x] 划拨给子用户 (单卡/批量)
- [x] 划拨权限校验 (2026-03-06 修复：验证目标用户存在且为直属子用户)
- [x] 自定义备注 (如: 大华道路检测)
- [x] 批量备注
- [x] 导出卡信息 (JSON格式，可转Excel)

**卡片状态**：
| 状态 | 英文 | 说明 |
|------|------|------|
| 测试期 | testing | test_expire_date 未到 |
| 沉默期 | silent | 等待激活 |
| 已激活 | activated | 正常使用中 |
| 已到期 | expired | 套餐到期 |
| 已停机 | suspended | 被停机 |
| 已销卡 | cancelled | 已注销 |

**API 端点**：
```
# 卡片列表与查询
GET    /api/v1/cards                      # 我的卡片列表 (支持高级搜索: remark, customer_id, batch_id, stock_out_start/end, activated_start/end, expired_start/end)
GET    /api/v1/cards/{id}                 # 卡片详情
GET    /api/v1/cards/search               # 快速搜索 (后6位)
GET    /api/v1/cards/stats                # 卡片统计

# 划拨操作
POST   /api/v1/cards/{id}/transfer        # 单卡划拨
POST   /api/v1/cards/batch/transfer       # 批量划拨

# 备注操作
PUT    /api/v1/cards/{id}/remark          # 单卡备注
PUT    /api/v1/cards/batch/remark         # 批量备注

# 导出
POST   /api/v1/cards/export               # 导出卡片数据

# 续费价格查询
POST   /api/v1/cards/batch/renew-price-query  # 批量查询续费价格（JOIN sale_packages 获取 price_sale）
```

---

### 模块 5: 流量池管理 ✅ 已完成

**组池规则**: 相同规格 (运营商+流量+周期) 的已激活卡可组池共享

**流量池示例**：
```
┌─────────────────────────────────────────────┐
│  流量池: 移动-1G-月包共享池                  │
│  组池条件: carrier=cmcc, flow=1024, monthly │
├─────────────────────────────────────────────┤
│  卡1 (供应商A) → 已用 300MB                 │
│  卡2 (供应商B) → 已用 500MB                 │
│  卡3 (供应商C) → 已用 200MB                 │
├─────────────────────────────────────────────┤
│  总流量: 3GB | 已用: 1GB | 剩余: 2GB        │
└─────────────────────────────────────────────┘
```

**功能**：
- [x] 创建流量池 (选择规格)
- [x] 添加卡片到流量池 (规格校验)
- [x] 从流量池移除卡片
- [x] 流量池用量统计 (自动汇总)
- [x] 设置告警阈值
- [x] 设置停卡阈值
- [x] 操作日志记录

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

### 模块 6: 停卡策略 ✅ 已完成

**停卡类型**：

| 类型 | 触发方式 | 触发条件 | 可复机 |
|------|----------|----------|--------|
| 到期停卡 | 自动 | 套餐过期日到期 | ✅ 续费后 |
| 手动停卡 | 手动 | 管理员/用户操作 | ✅ 直接复机 |
| 流量池超限 | 自动 | 池用量超阈值 | ✅ 池充值后 |
| 单卡超量 | 自动 | 单卡用量超套餐 (非池卡) | ✅ 充值/入池后 |

**功能**：
- [x] 停卡策略管理 (CRUD)
- [x] 手动停卡/复机
- [x] 到期停卡任务 (自动)
- [x] 单卡超量检查任务 (自动)
- [x] 停卡记录查询
- [x] 告警记录管理
- [x] 告警统计
- [x] 告警处理

**停卡流程**：

```
1. 到期停卡 (自动)
   定时任务扫描 → expired_at < 今天 → 停卡 → 调用供应商API

2. 手动停卡 ✅ 已集成供应商API (2026-03-06)
   用户操作 → API调用 → 调用供应商API → 更新数据库 → 记录日志

3. 手动复机 ✅ 已集成供应商API (2026-03-06)
   用户操作 → API调用 → 调用供应商API → 更新数据库 → 记录日志

4. 流量池超限停卡 (自动)
   流量同步后 → 池用量 >= 阈值 → 池内所有卡停卡

5. 单卡超量停卡 (自动)
   流量同步后 → 卡用量 >= 套餐 (非池卡) → 单卡停卡
```

**供应商API集成 (2026-03-06)**：
- ✅ 停机接口：`POST /api/v2/{API_KEY}/sor/` 参数 `{"number": iccid, "type": "01"}`
- ✅ 复机接口：`POST /api/v2/{API_KEY}/sor/` 参数 `{"number": iccid, "type": "00"}`
- ✅ 性能优化：预加载供应商信息，消除N+1查询（50卡操作：51次→2次查询）
- ✅ 容错设计：API失败不阻塞数据库更新，记录详细错误日志

**告警阈值**：
| 阈值 | 动作 |
|------|------|
| 80% | 发送告警通知 |
| 90% | 发送紧急预警 |
| 100% | 执行停卡 |

**API 端点**：
```
# 停卡策略
GET    /api/v1/suspend/policies              # 策略列表 ✅
POST   /api/v1/suspend/policies              # 创建策略 ✅
GET    /api/v1/suspend/policies/{id}         # 策略详情 ✅
PUT    /api/v1/suspend/policies/{id}         # 更新策略 ✅
DELETE /api/v1/suspend/policies/{id}         # 删除策略 ✅

# 手动操作
POST   /api/v1/suspend/cards/suspend         # 手动停卡 ✅
POST   /api/v1/suspend/cards/resume          # 手动复机 ✅

# 自动任务
POST   /api/v1/suspend/tasks/expired         # 执行到期停卡 ✅
POST   /api/v1/suspend/tasks/card-exceed     # 执行单卡超量检查 ✅

# 停卡记录
GET    /api/v1/suspend/logs                  # 停卡记录列表 ✅

# 告警管理
GET    /api/v1/suspend/alerts                # 告警列表 ✅
GET    /api/v1/suspend/alerts/stats          # 告警统计 ✅
POST   /api/v1/suspend/alerts/{id}/handle    # 处理告警 ✅
```

---

### 模块 7: 供应商对接 ✅ 已完成

**功能**：
- [x] 供应商信息管理 (CRUD)
- [x] API 配置管理 (URL/Key/Secret)
- [x] 同步间隔配置 (sync_interval 字段，单位：分钟)
- [x] 供应商API对接 (流量同步)
- [x] 定时任务自动同步 (基于供应商配置的间隔)
- [x] 卡片状态自动转换服务

**API 端点**：
```
GET    /api/v1/suppliers                  # 供应商列表 ✅
POST   /api/v1/suppliers                  # 添加供应商 ✅
GET    /api/v1/suppliers/{id}             # 供应商详情 ✅
PUT    /api/v1/suppliers/{id}             # 更新供应商 ✅
DELETE /api/v1/suppliers/{id}             # 删除供应商 ✅
POST   /api/v1/suppliers/{id}/test        # 测试API连通性

# 数据同步 (2026-03-04 新增)
POST   /api/v1/sync/usage                 # 手动同步流量 ✅
POST   /api/v1/sync/cards/{iccid}         # 同步单卡 ✅
GET    /api/v1/sync/logs                  # 同步日志 ✅
```

---

### 模块 8: 首页仪表盘 ✅ 已完成

**功能**：
- [x] 卡片数量统计 (按状态/运营商)
- [x] 流量使用统计 (趋势图)
- [x] 用户数量统计
- [x] 套餐销售统计
- [x] 流量池统计
- [x] 告警消息展示
- [x] 近期活动日志
- [x] 本月到期卡统计和明细 (支持运营商筛选)
- [x] 超量卡统计和明细 (支持运营商筛选)
- [x] 运营商卡片点击跳转筛选功能

**最新更新 (2026-03-10)**：
- 添加 `expiring_count` 和 `over_usage_count` 统计字段
- 到期卡和超量卡API支持 `carrier` 参数筛选
- 前端仪表盘添加统计卡片，点击跳转到卡片列表并自动筛选
- 卡片列表页面支持URL参数 `carrier`、`expiring`、`over_usage` 自动筛选

**API 端点**：
```
GET    /api/v1/dashboard/overview         # 总览数据 ✅
GET    /api/v1/dashboard/cards/stats      # 卡片统计 ✅
GET    /api/v1/dashboard/usage/trend      # 流量趋势 ✅
GET    /api/v1/dashboard/pools/stats      # 流量池统计 ✅
GET    /api/v1/dashboard/users/stats      # 用户统计 ✅
GET    /api/v1/dashboard/alerts           # 告警消息 ✅
GET    /api/v1/dashboard/activities       # 最近活动 ✅
GET    /api/v1/dashboard/cards/expiring?carrier=cmcc   # 到期卡明细(支持运营商筛选) ✅
GET    /api/v1/dashboard/cards/over-usage?carrier=cucc # 超量卡明细(支持运营商筛选) ✅
```

---

### 模块 9: 系统设置 ✅ 已完成

**功能**：
- [x] 系统参数配置
- [x] 操作日志查询
- [x] 登录日志查询
- [x] 告警规则设置
- [x] 通知模板管理

**API 端点**：
```
# 系统配置
GET    /api/v1/system/configs             # 获取系统配置列表 ✅
GET    /api/v1/system/configs/public      # 获取公开配置 ✅
GET    /api/v1/system/configs/{key}       # 获取单个配置 ✅
POST   /api/v1/system/configs             # 创建配置 ✅
PUT    /api/v1/system/configs/{key}       # 更新配置 ✅
PUT    /api/v1/system/configs             # 批量更新配置 ✅
DELETE /api/v1/system/configs/{key}       # 删除配置 ✅

# 日志查询
GET    /api/v1/system/logs/login          # 登录日志 ✅
GET    /api/v1/system/logs/operation      # 操作日志 ✅

# 告警规则
GET    /api/v1/system/alerts/rules        # 获取告警规则 ✅
PUT    /api/v1/system/alerts/rules        # 更新告警规则 ✅

# 通知模板
GET    /api/v1/system/notify/templates           # 模板列表 ✅
GET    /api/v1/system/notify/templates/{id}      # 模板详情 ✅
POST   /api/v1/system/notify/templates           # 创建模板 ✅
PUT    /api/v1/system/notify/templates/{id}      # 更新模板 ✅
DELETE /api/v1/system/notify/templates/{id}      # 删除模板 ✅
```

---

### 模块 10: 项目管理 ✅ 已完成

**模块定位**: 用户可创建项目对卡片进行分组管理

**功能**：
- [x] 项目 CRUD (创建/读取/更新/删除)
- [x] 项目列表查询 (分页、关键词搜索)
- [x] 项目详情查看
- [x] 卡片数量统计
- [x] 权限控制 (用户仅可操作自己的项目)

**数据模型**：
```python
class Project:
    id: int                    # 项目ID
    name: str                  # 项目名称
    user_id: int               # 所属用户ID
    remark: Optional[str]      # 备注
    card_count: int            # 关联卡片数量
    created_at: datetime       # 创建时间
    updated_at: datetime       # 更新时间
```

**API 端点**：
```
GET    /api/v1/projects                   # 项目列表 ✅
GET    /api/v1/projects/all               # 所有项目(下拉选择) ✅
GET    /api/v1/projects/{id}              # 项目详情 ✅
POST   /api/v1/projects                   # 创建项目 ✅
PUT    /api/v1/projects/{id}              # 更新项目 ✅
DELETE /api/v1/projects/{id}              # 删除项目 ✅
```

**前端页面**：
- ✅ `/projects` - 项目管理页面
- ✅ 项目表单弹窗 (ProjectFormDialog)

**开发文件**：
- 后端：`app/api/v1/project.py`、`app/schemas/project.py`、`app/crud/project_crud.py`、`app/db/models/project.py`
- 前端：`views/projects/index.vue`、`views/projects/components/ProjectFormDialog.vue`、`api/modules/project.ts`、`types/project.d.ts`

---

## 📊 数据库表设计

### 卡片相关表

```sql
-- 物联网卡表
CREATE TABLE `iot_cards` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    
    -- 卡片标识
    `iccid` VARCHAR(30) NOT NULL COMMENT 'ICCID',
    `imsi` VARCHAR(20) DEFAULT NULL COMMENT 'IMSI',
    `msisdn` VARCHAR(20) DEFAULT NULL COMMENT '号码',
    
    -- 归属关系
    `user_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '当前所属用户ID',
    `supplier_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '供应商ID',
    `batch_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '采购批次ID',
    `sale_package_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '销售套餐ID',
    
    -- 规格信息 (冗余，方便查询和组池)
    `carrier` ENUM('cmcc', 'cucc', 'ctcc') NOT NULL COMMENT '运营商',
    `flow_size` BIGINT NOT NULL COMMENT '套餐流量(MB)',
    `period_type` ENUM('monthly', 'yearly') NOT NULL COMMENT '周期类型',
    
    -- 生命周期日期 (格式: YYYY-MM-DD, 显示为 26/1/31)
    `test_expire_date` DATE DEFAULT NULL COMMENT '测试期到期日',
    `silent_expire_date` DATE DEFAULT NULL COMMENT '沉默期到期日',
    `activated_at` DATE DEFAULT NULL COMMENT '激活日',
    `expired_at` DATE DEFAULT NULL COMMENT '套餐过期日',
    
    -- 流量使用 (单位: MB)
    `data_used` BIGINT NOT NULL DEFAULT 0 COMMENT '已用流量(MB)',
    `data_total` BIGINT NOT NULL COMMENT '总流量(MB)',
    `data_sync_at` DATETIME DEFAULT NULL COMMENT '流量同步时间',
    
    -- 状态
    `status` ENUM('stock', 'testing', 'silent', 'activated', 'expired', 'suspended', 'cancelled') 
        NOT NULL DEFAULT 'stock' COMMENT '状态',
    
    -- 停卡信息
    `suspend_type` ENUM('none', 'manual', 'expired', 'pool_exceed', 'card_exceed') 
        DEFAULT 'none' COMMENT '停卡类型',
    `suspend_at` DATETIME DEFAULT NULL COMMENT '停卡时间',
    `suspend_reason` VARCHAR(200) DEFAULT NULL COMMENT '停卡原因',
    
    -- 流量池
    `pool_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '所属流量池ID',
    `is_pool_member` TINYINT DEFAULT 0 COMMENT '是否加入流量池',
    
    -- 备注
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    
    -- 出入库时间
    `stock_in_at` DATETIME DEFAULT NULL COMMENT '入库时间',
    `stock_out_at` DATETIME DEFAULT NULL COMMENT '出库时间',
    
    -- 系统字段
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_iccid` (`iccid`),
    KEY `idx_msisdn` (`msisdn`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_carrier` (`carrier`),
    KEY `idx_status` (`status`),
    KEY `idx_pool_id` (`pool_id`)
) COMMENT='物联网卡表';

-- 入库记录表
CREATE TABLE `stock_in_records` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `supplier_id` BIGINT UNSIGNED NOT NULL COMMENT '供应商ID',
    `package_id` BIGINT UNSIGNED NOT NULL COMMENT '底层套餐ID',
    
    -- 生命周期配置
    `test_expire_date` DATE DEFAULT NULL COMMENT '测试期到期日',
    `silent_expire_date` DATE NOT NULL COMMENT '沉默期到期日',
    
    `card_count` INT NOT NULL DEFAULT 0 COMMENT '卡片数量',
    `success_count` INT NOT NULL DEFAULT 0 COMMENT '成功数量',
    `failed_count` INT NOT NULL DEFAULT 0 COMMENT '失败数量',
    `remark` VARCHAR(500) DEFAULT NULL,
    `operator_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '操作人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,
    
    PRIMARY KEY (`id`),
    KEY `idx_supplier_id` (`supplier_id`),
    KEY `idx_created_at` (`created_at`)
) COMMENT='入库记录表';

-- 出库记录表
CREATE TABLE `stock_out_records` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT UNSIGNED NOT NULL COMMENT '目标用户ID',
    `sale_package_id` BIGINT UNSIGNED NOT NULL COMMENT '销售套餐ID',
    
    `card_count` INT NOT NULL DEFAULT 0 COMMENT '卡片数量',
    `success_count` INT NOT NULL DEFAULT 0 COMMENT '成功数量',
    `failed_count` INT NOT NULL DEFAULT 0 COMMENT '失败数量',
    `unit_price` DECIMAL(10,2) NOT NULL COMMENT '单价',
    `total_amount` DECIMAL(10,2) NOT NULL COMMENT '总金额',
    `remark` VARCHAR(500) DEFAULT NULL,
    `operator_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '操作人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,
    
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_created_at` (`created_at`)
) COMMENT='出库记录表';

-- 回收记录表
CREATE TABLE `stock_recycle_records` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `card_count` INT NOT NULL DEFAULT 0 COMMENT '回收数量',
    `success_count` INT NOT NULL DEFAULT 0 COMMENT '成功数量',
    `failed_count` INT NOT NULL DEFAULT 0 COMMENT '失败数量',
    `recycle_reason` VARCHAR(500) NOT NULL COMMENT '回收原因',
    `remark` VARCHAR(500) DEFAULT NULL,
    `operator_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '操作人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,
    
    PRIMARY KEY (`id`),
    KEY `idx_created_at` (`created_at`)
) COMMENT='回收记录表';

-- 流量池表 ✅ 已实现
CREATE TABLE `traffic_pools` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL COMMENT '流量池名称',
    `user_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '所属用户ID(NULL=平台池)',
    
    -- 组池规则 (相同规格)
    `carrier` ENUM('cmcc', 'cucc', 'ctcc') NOT NULL COMMENT '运营商',
    `flow_size` BIGINT NOT NULL COMMENT '单卡流量(MB)',
    `period_type` ENUM('monthly', 'yearly') NOT NULL COMMENT '周期类型',
    
    -- 统计 (自动更新)
    `card_count` INT NOT NULL DEFAULT 0 COMMENT '卡片数量',
    `data_total` BIGINT NOT NULL DEFAULT 0 COMMENT '总流量(MB)',
    `data_used` BIGINT NOT NULL DEFAULT 0 COMMENT '已用流量(MB)',
    
    -- 告警与停卡阈值
    `alert_threshold` INT DEFAULT NULL COMMENT '告警阈值(%)',
    `stop_threshold` INT DEFAULT NULL COMMENT '停卡阈值(%)',
    
    `status` ENUM('enable', 'disable') DEFAULT 'enable',
    `remark` VARCHAR(500) DEFAULT NULL,
    `created_by` BIGINT UNSIGNED DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,
    
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_carrier` (`carrier`)
) COMMENT='流量池表';

-- 流量池操作日志表 ✅ 已实现
CREATE TABLE `pool_card_logs` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `pool_id` BIGINT UNSIGNED NOT NULL COMMENT '流量池ID',
    `card_id` BIGINT UNSIGNED NOT NULL COMMENT '卡片ID',
    `iccid` VARCHAR(30) NOT NULL COMMENT 'ICCID',
    `action` VARCHAR(20) NOT NULL COMMENT '操作: add/remove',
    `operator_id` BIGINT UNSIGNED NOT NULL COMMENT '操作人ID',
    `remark` VARCHAR(200) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,
    
    PRIMARY KEY (`id`),
    KEY `idx_pool_id` (`pool_id`),
    KEY `idx_card_id` (`card_id`)
) COMMENT='流量池操作日志表';

-- 卡片划拨记录表
CREATE TABLE `card_transfers` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `card_id` BIGINT UNSIGNED NOT NULL COMMENT '卡片ID',
    `iccid` VARCHAR(30) NOT NULL COMMENT 'ICCID',
    `from_user_id` BIGINT UNSIGNED NOT NULL COMMENT '原用户ID',
    `to_user_id` BIGINT UNSIGNED NOT NULL COMMENT '目标用户ID',
    `operator_id` BIGINT UNSIGNED NOT NULL COMMENT '操作人ID',
    `remark` VARCHAR(200) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    KEY `idx_card_id` (`card_id`)
) COMMENT='卡片划拨记录';

-- 停卡记录表
CREATE TABLE `suspend_logs` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `card_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '卡片ID',
    `pool_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '流量池ID',
    `iccid` VARCHAR(30) DEFAULT NULL COMMENT 'ICCID',
    `suspend_type` ENUM('manual', 'expired', 'pool_exceed', 'card_exceed') NOT NULL,
    `operator_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '操作人',
    `trigger_value` VARCHAR(50) DEFAULT NULL COMMENT '触发值',
    `reason` VARCHAR(200) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    KEY `idx_card_id` (`card_id`)
) COMMENT='停卡记录表';

-- 项目表 ✅ 已实现
CREATE TABLE `projects` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL COMMENT '项目名称',
    `user_id` BIGINT UNSIGNED NOT NULL COMMENT '所属用户ID',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `card_count` INT NOT NULL DEFAULT 0 COMMENT '关联卡片数量',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,

    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_name` (`name`)
) COMMENT='项目表';
```

---

## 📁 项目目录结构

```
iot_card_platform/
├── app/
│   ├── __init__.py
│   ├── main.py                    # 应用入口 ✅
│   ├── config.py                  # 配置管理 ✅
│   ├── api/                       # API 路由
│   │   └── v1/
│   │       ├── auth.py            # 认证接口 ✅
│   │       ├── sys_user.py        # 用户管理 ✅
│   │       ├── sys_menu.py        # 菜单管理 ✅
│   │       ├── supplier.py        # 供应商管理 ✅
│   │       ├── package.py         # 套餐管理 ✅
│   │       ├── stock.py           # 出入库管理 ✅
│   │       ├── iot_card.py        # 卡片管理 ✅
│   │       ├── pool.py            # 流量池管理 ✅
│   │       └── dashboard.py       # 仪表盘
│   ├── db/                        # 数据库
│   │   ├── database.py            # 数据库连接 ✅
│   │   └── models/                # ORM 模型
│   │       ├── sys_user.py        # 用户模型 ✅
│   │       ├── sys_menu.py        # 菜单模型 ✅
│   │       ├── supplier.py        # 供应商模型 ✅
│   │       ├── package.py         # 套餐模型 ✅
│   │       ├── iot_card.py        # 卡片模型 ✅
│   │       ├── stock.py           # 出入库模型 ✅
│   │       └── pool.py            # 流量池模型 ✅
│   ├── schemas/                   # Pydantic 模型
│   ├── crud/                      # 数据操作
│   ├── services/                  # 业务逻辑
│   ├── clients/                   # 外部API客户端
│   ├── tasks/                     # 后台任务
│   └── utils/                     # 工具函数
├── scripts/
│   └── init_database.sql          # 数据库初始化 ✅
├── tests/                         # 测试用例
├── requirements.txt               # 依赖清单 ✅
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🚀 开发计划

| 阶段 | 模块 | 预估时间 | 状态 |
|------|------|----------|------|
| Phase 1 | 多租户 + 用户权限 | 2-3天 | ✅ 已完成 |
| Phase 2 | 套餐管理 | 1-2天 | ✅ 已完成 |
| Phase 3 | 出入库管理 (前端) | 2-3天 | ✅ 已完成 |
| Phase 3.1 | 出入库管理 (后端数据库) | 2-3天 | ✅ 已完成 |
| Phase 4 | 卡片管理 | 2-3天 | ✅ 已完成 |
| Phase 5 | 流量池管理 | 1-2天 | ✅ 已完成 |
| Phase 6 | 停卡策略 | 1天 | ✅ 已完成 |
| Phase 7 | 供应商对接 + 自动同步 | 3-5天 | ✅ 已完成 |
| Phase 8 | 仪表盘 | 1-2天 | ✅ 已完成 |
| Phase 9 | 系统设置 | 1天 | ✅ 已完成 |
| Phase 10 | 项目管理 | 1天 | ✅ 已完成 |

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
| **异步任务** | Celery / APScheduler |
| **日志** | Loguru |
| **容器化** | Docker + Docker Compose |
