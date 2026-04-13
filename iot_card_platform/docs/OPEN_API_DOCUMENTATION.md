# 开放 API 对接文档

## 1. 适用范围

本开放 API 面向一级用户使用。每个一级用户拥有独立的 `APPID` 与 `AppSecret`，用于访问其名下卡片数据。

## 2. 获取凭证

后台入口：

- 超级管理员：用户管理 -> 一级用户 -> `API凭证`
- 一级用户：用户管理 -> `我的API凭证`

说明：

- `APPID` 固定用于标识调用方
- `AppSecret` 仅在重置后完整展示一次，请及时保存
- 重置 `AppSecret` 后，旧密钥立即失效

## 3. 基础信息

- Base URL：`/api/v1/open`
- 数据格式：`application/json`
- 字符编码：`UTF-8`

## 4. 认证方式

每次请求都必须带上以下请求头：

```http
X-APP-ID: APP1234567890ABCD
X-APP-SECRET: your_app_secret
Content-Type: application/json
```

认证失败时，返回：

```json
{
  "code": 401,
  "msg": "身份认证失败，请重新登录",
  "data": null
}
```

## 5. 通用响应格式

成功：

```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

失败：

```json
{
  "code": 400,
  "msg": "错误信息",
  "data": null
}
```

## 6. 接口列表

### 6.1 获取卡片列表

- 方法：`GET /api/v1/open/cards`

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | ICCID / MSISDN / 后6位 |
| status | string | 否 | 卡状态 |
| carrier | string | 否 | 运营商 |
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页条数，默认 20，最大 100 |

请求示例：

```bash
curl --request GET 'http://localhost:8000/api/v1/open/cards?page=1&page_size=20&keyword=8986' \
  --header 'X-APP-ID: APP1234567890ABCD' \
  --header 'X-APP-SECRET: your_app_secret'
```

响应示例：

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "total": 1,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1001,
        "iccid": "8986001234567890123",
        "msisdn": "14400001111",
        "status": "activated",
        "carrier": "china_mobile",
        "user_id": 12
      }
    ]
  }
}
```

### 6.2 获取卡片详情

- 方法：`GET /api/v1/open/cards/{card_id}`

请求示例：

```bash
curl --request GET 'http://localhost:8000/api/v1/open/cards/1001' \
  --header 'X-APP-ID: APP1234567890ABCD' \
  --header 'X-APP-SECRET: your_app_secret'
```

说明：

- 返回卡片状态 `status`、状态名称 `status_name`
- 返回当前总用量 `data_used`
- 返回当月用量 `data_used_month`
- 若卡属于流量池，会返回 `pool_id`

### 6.3 获取卡片用量摘要

- 方法：`GET /api/v1/open/cards/{card_id}/usage-summary`

用途：

- 获取单张卡的单日用量信息
- 获取当前月用量信息
- 获取当前卡状态
- 获取是否属于流量池

响应示例：

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "card_id": 1001,
    "iccid": "8986001234567890123",
    "status": "activated",
    "status_name": "已激活",
    "daily_usage": {
      "snapshot_date": "2026-04-10",
      "used_mb": 125,
      "total_used_mb": 2048
    },
    "monthly_usage": {
      "snapshot_month": "2026-04",
      "used_mb": 2048,
      "total_mb": 3072,
      "remaining_mb": 1024,
      "usage_percent": 66.67
    },
    "pool_info": {
      "pool_id": 88,
      "is_pool_member": true
    },
    "data_sync_at": "2026-04-10T08:30:00"
  }
}
```

### 6.4 获取卡片用量历史

- 方法：`GET /api/v1/open/cards/{card_id}/usage-history`

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | 否 | 开始日期，格式 `YYYY-MM-DD` |
| end_date | string | 否 | 结束日期，格式 `YYYY-MM-DD` |

说明：

- 返回每日快照列表
- `daily_used` 为当日新增用量（MB）
- `data_used` 为截至当日累计用量（MB）

### 6.5 获取卡片统计

- 方法：`GET /api/v1/open/cards/stats`

请求示例：

```bash
curl --request GET 'http://localhost:8000/api/v1/open/cards/stats' \
  --header 'X-APP-ID: APP1234567890ABCD' \
  --header 'X-APP-SECRET: your_app_secret'
```

### 6.6 批量查询卡片

- 方法：`POST /api/v1/open/cards/batch-query`

请求体：

```json
[
  "8986001234567890123",
  "8986001234567890456"
]
```

请求示例：

```bash
curl --request POST 'http://localhost:8000/api/v1/open/cards/batch-query' \
  --header 'Content-Type: application/json' \
  --header 'X-APP-ID: APP1234567890ABCD' \
  --header 'X-APP-SECRET: your_app_secret' \
  --data '[
    "8986001234567890123",
    "8986001234567890456"
  ]'
```

响应示例：

```json
{
  "code": 200,
  "msg": "查询完成：找到 1 张卡片",
  "data": {
    "found": [
      {
        "id": 1001,
        "iccid": "8986001234567890123"
      }
    ],
    "not_found": [
      "8986001234567890456"
    ]
  }
}
```

### 6.7 获取流量池列表

- 方法：`GET /api/v1/open/pools`

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 否 | 流量池名称 |
| carrier | string | 否 | 运营商 |
| status | string | 否 | 状态 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页条数 |

### 6.8 获取流量池详情

- 方法：`GET /api/v1/open/pools/{pool_id}`

说明：

- 返回流量池基本信息
- 返回运营商、规格、总量、已用量、剩余量、用量百分比
- 返回所属用户、销售套餐等信息

### 6.9 获取流量池用量详情

- 方法：`GET /api/v1/open/pools/{pool_id}/usage`

说明：

- 返回流量池总体用量
- 返回池内卡片明细用量
- 可直接用于展示“流量池详情”

响应示例：

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "pool_id": 88,
    "pool_name": "移动共享池A",
    "spec_name": "中国移动3G/月包",
    "card_count": 20,
    "data_total": 61440,
    "data_used": 28672,
    "data_remain": 32768,
    "usage_percent": 46.67,
    "is_alert": false,
    "is_exceed": false,
    "cards": [
      {
        "card_id": 1001,
        "iccid": "8986001234567890123",
        "data_used": 2048,
        "data_total": 3072,
        "usage_percent": 66.67
      }
    ]
  }
}
```

## 7. 对接建议

- 服务端保存 `APPID` 与 `AppSecret`，不要放在前端页面明文调用
- 建议对接方按用户维度隔离凭证，不要多个系统共用同一套密钥
- 若怀疑泄露，请立即在后台重置 `AppSecret`
