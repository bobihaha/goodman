# 物联网卡管理平台 - 后端API文档

## 📋 目录

- [1. 认证模块 API](#1-认证模块-api)
- [2. 用户管理 API](#2-用户管理-api)
- [3. 菜单权限 API](#3-菜单权限-api)
- [4. 供应商管理 API](#4-供应商管理-api)
- [5. 套餐管理 API](#5-套餐管理-api)
- [6. 出入库管理 API](#6-出入库管理-api)
- [7. 卡片管理 API](#7-卡片管理-api)
- [8. 流量池管理 API](#8-流量池管理-api)
- [9. 停卡策略 API](#9-停卡策略-api)
- [10. 仪表盘 API](#10-仪表盘-api)
- [11. 系统设置 API](#11-系统设置-api)

---

## 🌐 基础信息

### 服务地址
- **开发环境**: `http://localhost:8000`
- **生产环境**: `https://api.yourdomain.com`

### API版本
- **当前版本**: `v1`
- **Base URL**: `/api/v1`

### 认证方式
- **类型**: JWT Bearer Token
- **Header**: `Authorization: Bearer {token}`

### 通用响应格式

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

**错误响应**:
```json
{
  "code": 400,
  "message": "错误信息",
  "data": null
}
```

### HTTP状态码
| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

---

## 1. 认证模块 API

### 1.1 用户登录
**接口**: `POST /api/v1/auth/login`

**请求参数**:
```json
{
  "username": "admin",
  "password": "123456"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 7200,
    "user": {
      "id": 1,
      "username": "admin",
      "nickname": "管理员",
      "user_level": 1,
      "status": "enable"
    }
  }
}
```

### 1.2 用户登出
**接口**: `POST /api/v1/auth/logout`

**请求头**: `Authorization: Bearer {token}`

**响应示例**:
```json
{
  "code": 200,
  "message": "登出成功"
}
```

### 1.3 刷新Token
**接口**: `POST /api/v1/auth/refresh`

**请求头**: `Authorization: Bearer {token}`

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "access_token": "new_token_here",
    "expires_in": 7200
  }
}
```

### 1.4 获取当前用户信息
**接口**: `GET /api/v1/auth/profile`

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "username": "admin",
    "nickname": "管理员",
    "email": "admin@example.com",
    "phone": "13800138000",
    "user_level": 1,
    "parent_id": null,
    "status": "enable",
    "created_at": "2024-01-01 00:00:00"
  }
}
```

### 1.5 超级登录
**接口**: `POST /api/v1/auth/super-login`

**说明**: 超级管理员可以无密码登录下级用户账号

**请求参数**:
```json
{
  "target_user_id": 10
}
```

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "access_token": "new_token_for_target_user",
    "user": {
      "id": 10,
      "username": "user001",
      "nickname": "用户001"
    }
  }
}
```

---

## 2. 用户管理 API

### 2.1 获取用户列表
**接口**: `GET /api/v1/users`

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| keyword | string | 否 | 搜索关键词（用户名/昵称） |
| user_level | int | 否 | 用户级别筛选 |
| status | string | 否 | 状态筛选：enable/disable |
| channel_id | int | 否 | 推荐渠道筛选，仅超级管理员查询一级平台用户时生效 |

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "username": "admin",
        "nickname": "管理员",
        "email": "admin@example.com",
        "phone": "13800138000",
        "recommended_channel_name": "渠道伙伴A",
        "user_level": 1,
        "parent_id": null,
        "status": "enable",
        "created_at": "2024-01-01 00:00:00"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

`recommended_channel_name` 仅用于超级管理员的一级平台用户列表；无渠道归属或一级平台用户查询自己的下级用户时返回 `null`，前端显示“—”。

### 2.2 创建用户
**接口**: `POST /api/v1/users`

**请求参数**:
```json
{
  "username": "user001",
  "password": "123456",
  "nickname": "用户001",
  "email": "user001@example.com",
  "phone": "13800138001",
  "user_level": 2,
  "status": "enable",
  "remark": "备注信息"
}
```

**响应示例**:
```json
{
  "code": 201,
  "message": "创建成功",
  "data": {
    "id": 10,
    "username": "user001",
    "nickname": "用户001"
  }
}
```

### 2.3 获取用户详情
**接口**: `GET /api/v1/users/{user_id}`

### 2.4 更新用户
**接口**: `PUT /api/v1/users/{user_id}`

### 2.5 删除用户
**接口**: `DELETE /api/v1/users/{user_id}`

### 2.6 修改密码
**接口**: `PUT /api/v1/users/{user_id}/password`

**请求参数**:
```json
{
  "old_password": "123456",
  "new_password": "654321"
}
```

### 2.7 启用/禁用用户
**接口**: `PUT /api/v1/users/{user_id}/status`

**请求参数**:
```json
{
  "status": "disable"
}
```

---

## 3. 菜单权限 API

### 3.1 获取菜单列表
**接口**: `GET /api/v1/menus`

**响应示例**:
```json
{
  "code": 200,
  "data": [
    {
      "id": 1,
      "name": "仪表盘",
      "path": "/dashboard",
      "component": "Dashboard",
      "icon": "dashboard",
      "sort": 1,
      "parent_id": null,
      "children": []
    }
  ]
}
```

### 3.2 获取用户菜单权限
**接口**: `GET /api/v1/menus/user/{user_id}`

### 3.3 设置用户菜单权限
**接口**: `PUT /api/v1/menus/user/{user_id}`

**请求参数**:
```json
{
  "menu_ids": [1, 2, 3, 4, 5]
}
```

---

## 4. 供应商管理 API

### 4.1 获取供应商列表
**接口**: `GET /api/v1/suppliers`

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "供应商A",
        "code": "SUP001",
        "contact": "张三",
        "phone": "13800138000",
        "api_url": "https://api.supplier-a.com",
        "api_key": "key123",
        "status": "enable",
        "created_at": "2024-01-01 00:00:00"
      }
    ],
    "total": 10
  }
}
```

### 4.2 创建供应商
**接口**: `POST /api/v1/suppliers`

**请求参数**:
```json
{
  "name": "供应商A",
  "code": "SUP001",
  "contact": "张三",
  "phone": "13800138000",
  "email": "contact@supplier-a.com",
  "api_url": "https://api.supplier-a.com",
  "api_key": "key123",
  "api_secret": "secret456",
  "status": "enable",
  "remark": "备注"
}
```

### 4.3 获取供应商详情
**接口**: `GET /api/v1/suppliers/{supplier_id}`

### 4.4 更新供应商
**接口**: `PUT /api/v1/suppliers/{supplier_id}`

### 4.5 删除供应商
**接口**: `DELETE /api/v1/suppliers/{supplier_id}`

---

## 5. 套餐管理 API

### 5.1 获取底层套餐列表
**接口**: `GET /api/v1/packages/supplier`

**说明**: 供应商采购成本套餐（仅超级管理员可见）

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "移动1G月包",
        "carrier": "cmcc",
        "flow_size": 1024,
        "period_type": "monthly",
        "valid_days": 30,
        "cost_price": 5.00,
        "supplier_id": 1,
        "supplier_name": "供应商A",
        "status": "enable"
      }
    ],
    "total": 20
  }
}
```

### 5.2 创建底层套餐
**接口**: `POST /api/v1/packages/supplier`

**请求参数**:
```json
{
  "name": "移动1G月包",
  "carrier": "cmcc",
  "flow_size": 1024,
  "period_type": "monthly",
  "valid_days": 30,
  "cost_price": 5.00,
  "supplier_id": 1,
  "status": "enable",
  "remark": "备注"
}
```

### 5.3 获取销售套餐列表
**接口**: `GET /api/v1/packages/sale`

**说明**: 客户销售定价套餐

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "移动1G月包",
        "carrier": "cmcc",
        "flow_size": 1024,
        "period_type": "monthly",
        "valid_days": 30,
        "sale_price": 10.00,
        "base_package_id": 1,
        "status": "enable"
      }
    ],
    "total": 30
  }
}
```

### 5.4 创建销售套餐
**接口**: `POST /api/v1/packages/sale`

---

## 6. 出入库管理 API

### 6.1 批量入库
**接口**: `POST /api/v1/stock/in`

**说明**: 导入卡片到库存

**请求参数**:
```json
{
  "supplier_id": 1,
  "package_id": 1,
  "test_expire_date": "2026-01-31",
  "silent_expire_date": "2026-04-30",
  "cards": [
    {
      "iccid": "89860123456789012345",
      "imsi": "460012345678901",
      "msisdn": "13800138000"
    }
  ],
  "remark": "2024年1月采购批次"
}
```

**响应示例**:
```json
{
  "code": 201,
  "message": "入库成功",
  "data": {
    "batch_id": 1,
    "batch_no": "BATCH20240101001",
    "success_count": 100,
    "failed_count": 0
  }
}
```

### 6.2 获取入库记录
**接口**: `GET /api/v1/stock/in`

### 6.3 创建出库单
**接口**: `POST /api/v1/stock/out`

**请求参数**:
```json
{
  "user_id": 10,
  "sale_package_id": 1,
  "card_ids": [1, 2, 3, 4, 5],
  "remark": "出库给用户001"
}
```

### 6.4 确认出库
**接口**: `POST /api/v1/stock/out/{out_id}/confirm`

### 6.5 获取库存统计
**接口**: `GET /api/v1/stock/summary`

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "total_stock": 10000,
    "by_carrier": {
      "cmcc": 5000,
      "cucc": 3000,
      "ctcc": 2000
    },
    "by_supplier": {
      "供应商A": 6000,
      "供应商B": 4000
    }
  }
}
```

---

## 7. 卡片管理 API

### 7.1 获取卡片列表
**接口**: `GET /api/v1/cards`

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| keyword | string | 否 | ICCID/IMSI/MSISDN搜索 |
| carrier | string | 否 | 运营商筛选 |
| status | string | 否 | 状态筛选 |
| pool_id | int | 否 | 流量池筛选 |

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "iccid": "89860123456789012345",
        "msisdn": "13800138000",
        "carrier": "cmcc",
        "status": "activated",
        "data_used": 512,
        "data_total": 1024,
        "usage_percent": 50.0,
        "activated_at": "2024-01-15",
        "expired_at": "2024-02-15",
        "pool_id": null,
        "remark": "大华道路检测"
      }
    ],
    "total": 1000,
    "page": 1,
    "page_size": 20
  }
}
```

### 7.2 获取卡片详情
**接口**: `GET /api/v1/cards/{card_id}`

### 7.3 快速搜索（后6位）
**接口**: `GET /api/v1/cards/search?keyword=012345`

### 7.4 单卡划拨
**接口**: `POST /api/v1/cards/{card_id}/transfer`

**请求参数**:
```json
{
  "to_user_id": 20,
  "remark": "划拨给子用户"
}
```

### 7.5 批量划拨
**接口**: `POST /api/v1/cards/batch/transfer`

**请求参数**:
```json
{
  "card_ids": [1, 2, 3],
  "to_user_id": 20,
  "remark": "批量划拨"
}
```

### 7.6 单卡备注
**接口**: `PUT /api/v1/cards/{card_id}/remark`

**请求参数**:
```json
{
  "remark": "大华道路检测设备"
}
```

### 7.7 批量备注
**接口**: `PUT /api/v1/cards/batch/remark`

### 7.8 导出卡片
**接口**: `POST /api/v1/cards/export`

**说明**: 按指定卡片或当前筛选条件导出完整卡片运营信息，包含关联账户名称和登录账号、卡片规格与类型、流量与生命周期、停卡、流量池、出入库、套餐价格、同步和设备信息；不包含账户密码或密钥。

**请求参数**:
```json
{
  "card_ids": [1, 2, 3],
  "format": "json"
}
```

---

## 8. 流量池管理 API

### 8.1 获取流量池列表
**接口**: `GET /api/v1/pools`

**查询参数**:
- `name`：流量池名称（模糊搜索）
- `carrier`：运营商
- `status`：启用状态
- `is_alert`：告警状态，`true` 仅返回告警中，`false` 仅返回未告警
- `page` / `page_size`：页码与每页数量

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "移动1G月包共享池",
        "carrier": "cmcc",
        "flow_size": 1024,
        "period_type": "monthly",
        "card_count": 50,
        "data_total": 51200,
        "data_used": 25600,
        "usage_percent": 50.0,
        "alert_threshold": 80,
        "stop_threshold": 95,
        "status": "enable"
      }
    ],
    "total": 10
  }
}
```

### 8.2 创建流量池
**接口**: `POST /api/v1/pools`

**请求参数**:
```json
{
  "name": "移动1G月包共享池",
  "carrier": "cmcc",
  "flow_size": 1024,
  "period_type": "monthly",
  "alert_threshold": 80,
  "stop_threshold": 95,
  "remark": "备注"
}
```

### 8.3 获取流量池详情
**接口**: `GET /api/v1/pools/{pool_id}`

### 8.4 更新流量池
**接口**: `PUT /api/v1/pools/{pool_id}`

### 8.5 删除流量池
**接口**: `DELETE /api/v1/pools/{pool_id}`

### 8.6 获取池内卡片列表
**接口**: `GET /api/v1/pools/{pool_id}/cards`

### 8.7 添加卡片到池
**接口**: `POST /api/v1/pools/{pool_id}/cards`

**请求参数**:
```json
{
  "card_ids": [1, 2, 3, 4, 5]
}
```

### 8.8 从池中移除卡片
**接口**: `DELETE /api/v1/pools/{pool_id}/cards`

**请求参数**:
```json
{
  "card_ids": [1, 2, 3]
}
```

### 8.9 获取流量池用量统计
**接口**: `GET /api/v1/pools/{pool_id}/usage`

### 8.10 获取操作日志
**接口**: `GET /api/v1/pools/{pool_id}/logs`

---

## 9. 停卡策略 API

### 9.1 获取停卡策略列表
**接口**: `GET /api/v1/suspend/policies`

### 9.2 创建停卡策略
**接口**: `POST /api/v1/suspend/policies`

### 9.3 手动停卡
**接口**: `POST /api/v1/suspend/cards/suspend`

**请求参数**:
```json
{
  "card_ids": [1, 2, 3],
  "reason": "用户申请停卡"
}
```

### 9.4 手动复机
**接口**: `POST /api/v1/suspend/cards/resume`

**请求参数**:
```json
{
  "card_ids": [1, 2, 3],
  "reason": "用户申请复机"
}
```

### 9.5 执行到期停卡任务
**接口**: `POST /api/v1/suspend/tasks/expired`

### 9.6 执行单卡超量检查
**接口**: `POST /api/v1/suspend/tasks/card-exceed`

### 9.7 获取停卡记录
**接口**: `GET /api/v1/suspend/logs`

### 9.8 获取告警列表
**接口**: `GET /api/v1/suspend/alerts`

### 9.9 获取告警统计
**接口**: `GET /api/v1/suspend/alerts/stats`

### 9.10 处理告警
**接口**: `POST /api/v1/suspend/alerts/{alert_id}/handle`

---

## 10. 仪表盘 API

### 10.1 获取总览数据
**接口**: `GET /api/v1/dashboard/overview`

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "total_cards": 10000,
    "active_cards": 8000,
    "total_users": 100,
    "total_pools": 20,
    "today_usage": 50000,
    "month_usage": 1500000
  }
}
```

### 10.2 获取卡片统计
**接口**: `GET /api/v1/dashboard/cards/stats`

### 10.3 获取流量趋势
**接口**: `GET /api/v1/dashboard/usage/trend`

### 10.4 获取流量池统计
**接口**: `GET /api/v1/dashboard/pools/stats`

### 10.5 获取用户统计
**接口**: `GET /api/v1/dashboard/users/stats`

### 10.6 获取告警消息
**接口**: `GET /api/v1/dashboard/alerts`

### 10.7 获取最近活动
**接口**: `GET /api/v1/dashboard/activities`

---

## 11. 系统设置 API

### 11.1 获取系统配置列表
**接口**: `GET /api/v1/system/configs`

### 11.2 获取单个配置
**接口**: `GET /api/v1/system/configs/{key}`

### 11.3 创建配置
**接口**: `POST /api/v1/system/configs`

### 11.4 更新配置
**接口**: `PUT /api/v1/system/configs/{key}`

### 11.5 批量更新配置
**接口**: `PUT /api/v1/system/configs`

### 11.6 删除配置
**接口**: `DELETE /api/v1/system/configs/{key}`

### 11.7 获取登录日志
**接口**: `GET /api/v1/system/logs/login`

### 11.8 获取操作日志
**接口**: `GET /api/v1/system/logs/operation`

### 11.9 获取告警规则
**接口**: `GET /api/v1/system/alerts/rules`

### 11.10 更新告警规则
**接口**: `PUT /api/v1/system/alerts/rules`

---

## 📝 附录

### 枚举值说明

**用户级别 (user_level)**:
- `1`: 超级管理员
- `2`: 用户/代理商
- `3`: 子用户

**运营商 (carrier)**:
- `cmcc`: 中国移动
- `cucc`: 中国联通
- `ctcc`: 中国电信

**周期类型 (period_type)**:
- `monthly`: 月包
- `yearly`: 年包

**卡片状态 (status)**:
- `stock`: 库存中
- `testing`: 测试期
- `silent`: 沉默期
- `activated`: 已激活
- `expired`: 已到期
- `suspended`: 已停机
- `cancelled`: 已销卡

**停卡类型 (suspend_type)**:
- `manual`: 手动停卡
- `expired`: 到期停卡
- `pool_exceed`: 流量池超限
- `card_exceed`: 单卡超量

---

## 🔗 相关文档

- [项目README](./README.md)
- [模块规划](./MODULE_PLAN.md)
- [前端PRD](./FRONTEND_PRD.md)

---

**文档版本**: v1.0  
**最后更新**: 2024-01-27  
**维护者**: 开发团队





## 12. 渠道推广积分 API

### 12.1 渠道客户报备

**接口**: `POST /api/v1/channels/public/{slug}/register`

**必填参数**：`customer_name`、`customer_phone`、`customer_profile`（设备、场景、规模，5～500 字）、`consent`。

### 12.2 渠道积分汇总

**接口**: `GET /api/v1/channels/me/summary`

汇总同时返回兼容字段 `settled_points`、`pending_points`，以及展示字段 `consumed_points`（已结算）、`remaining_points`（待结算）。

### 12.3 渠道推荐客户

**接口**: `GET /api/v1/channels/me/customers`

仅渠道 JWT 可访问，按当前渠道分页返回客户姓名、手机号、用户情况、报备时间、积分笔数及累计、已消耗、剩余积分。

### 12.4 渠道积分明细

**接口**: `GET /api/v1/channels/me/points`

---










