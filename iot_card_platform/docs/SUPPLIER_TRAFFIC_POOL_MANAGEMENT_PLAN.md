# 供应商流量池管理方案

## 背景

当前平台已有本地流量池管理，统计口径来自池内卡片的同步用量。运营上还需要直接查看供应商账户里的流量池使用情况，减少频繁登录供应商后台。

## 供应商接口确认

### LX / UPIOT

文档地址：`http://ec.upiot.net/app/v1/api-doc.html`

已确认可用接口：

| 能力 | 接口 | 说明 |
| --- | --- | --- |
| 流量池列表 | `GET /api/v2/{API_KEY}/usage_pool/` | 返回流量池代码、名称、运营商、计费组列表、总流量 |
| 流量池当前统计 | `GET /api/v2/{API_KEY}/usage_pool/info/` | 返回流量池代码、总卡数、激活卡数、总流量、已用流量 |
| 流量池充值 | `POST /api/v2/{API_KEY}/usage_pool/<code>/charge/` | 可后续接入供应商侧充值 |
| 充值产品 | `GET /api/v2/{API_KEY}/usage_pool/<code>/charge/products/` | 可后续接入供应商侧充值产品 |

限制：文档标注流量池列表为 `20次/分钟`，当前统计为 `20次/小时`，定时同步频率需要按小时级控制。

### SB / SIMBOSS

文档地址：`https://simboss.com/www/service/api`

已确认可用接口：

| 能力 | 接口 | 说明 |
| --- | --- | --- |
| 用户下所有流量池信息 | `POST /2.0/card/pool/list` | 返回供应商流量池 ID、规格、运营商、总量、用量、剩余量、卡数 |
| 流量池详情 | `POST /2.0/card/pool/detail` | 通过 `iccid`/`imsi`/`msisdn` 查询该卡所在流量池详情 |

限制：列表接口无需额外业务参数；详情接口不是按池 ID 查询，而是通过卡号定位流量池。

## 建议产品形态

新增“供应商流量池管理”页，作为超管运维视图，菜单位于“仪表盘”下方，不替代现有“流量池列表”。

建议展示字段：

- 供应商、供应商池编码、供应商池名称
- 运营商、规格、总流量、已用流量、剩余流量、使用率
- 总卡数、激活卡数、停卡数、库存/测试/销卡数
- 最近同步时间、同步状态、异常信息

建议操作：

- 手动同步全部或指定供应商
- 定时同步启停与同步间隔
- 点击供应商流量池进入详情，查看最近历史月份的使用率趋势和每月用量快照，方便运营判断增长趋势。
- 高使用率筛选与告警
- 每个供应商侧流量池默认按 60%、80%、100% 三级阈值发送邮件提醒；后续可单独修改单个流量池的阈值和提醒邮箱
- 后续再考虑供应商侧充值，先只读同步

## 技术落点

已在供应商客户端抽象层补充统一方法：

- `get_traffic_pool_list()`
- `get_traffic_pool_usage()`

已适配：

- `UpiotSupplierClient`: `usage_pool`、`usage_pool/info`。同步当前统计时会用 `usage_pool/info` 取用量，再用 `usage_pool` 补齐名称、运营商、计费组列表，并从计费组编码/显式字段解析 `pool_specification`，支持 LX 按规格筛选。
- `SimbossSupplierClient`: `card/pool/list`。SIMBOSS 流量池名称缺失时，按 `poolSpecification` 生成运营可读名称，例如 `51200MB` 显示为 `网络50GB/月`，`-1` 显示为 `全套餐`；原始数字池 ID 保留为供应商池编码。

已落地页面/API：

- `GET /api/v1/supplier-traffic-pools`：按供应商名称、运营商、流量池规格筛选，支持按使用率、套餐规格、已用量、总量、剩余量、本月预估用量、预计月底剩余排序。
- `GET /api/v1/supplier-traffic-pools/{pool_id}`：查看流量池详情和最近 1-36 个月月度历史快照；当前月会按 `已用量 / 已使用天数 * 当月天数` 返回本月预估使用量、预计月底剩余和预估使用率。
- `POST /api/v1/supplier-traffic-pools/{pool_id}/histories/export`：导出该供应商流量池最近 1-36 个月历史用量数据，包含月份、使用率、已用/总量、剩余量、本月预估使用量、预计月底剩余、卡数和同步时间。
- `POST /api/v1/supplier-traffic-pools/sync`：同步供应商侧流量池快照，并检查邮件提醒。返回值同时包含池维度和供应商维度统计，兼容旧字段 `success`/`failed`。
- `PUT /api/v1/supplier-traffic-pools/{pool_id}/alert`：更新提醒阈值和提醒邮箱

下一步如果落完整管理页，建议新增独立表：

```sql
CREATE TABLE supplier_traffic_pools (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    supplier_id BIGINT UNSIGNED NOT NULL,
    supplier_pool_code VARCHAR(100) NOT NULL,
    supplier_pool_name VARCHAR(100) DEFAULT NULL,
    carrier VARCHAR(20) DEFAULT NULL,
    pool_specification BIGINT DEFAULT NULL,
    total_flow DECIMAL(18,3) DEFAULT 0,
    used_flow DECIMAL(18,3) DEFAULT 0,
    remaining_flow DECIMAL(18,3) DEFAULT 0,
    usage_percent DECIMAL(8,2) DEFAULT 0,
    total_card_count INT DEFAULT 0,
    active_card_count INT DEFAULT 0,
    alert_thresholds VARCHAR(100) DEFAULT '60,80,100',
    last_alert_threshold INT DEFAULT NULL,
    raw_data JSON DEFAULT NULL,
    last_sync_at DATETIME DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uk_supplier_pool (supplier_id, supplier_pool_code),
    KEY idx_supplier_id (supplier_id),
    KEY idx_usage_percent (usage_percent)
) COMMENT='供应商侧流量池快照表';
```

同步成功写入当前快照时，会同时按 `supplier_pool_id + record_month` 更新一条 `supplier_traffic_pool_histories` 月度历史快照。历史表仅记录本地同步结果，不额外调用供应商接口，因此详情页不会增加供应商 API 压力。已有月份会被本月最新一次同步覆盖，跨月后自然沉淀为历史月份。

## 风险点

- LX 当前统计接口小时频率较低，不适合页面频繁实时刷新。
- LX 与 SIMBOSS 字段口径不同，页面应明确“供应商侧用量”，避免和本地池内卡片汇总混用。
- SIMBOSS 流量池详情按卡号查，不适合做主同步入口；列表接口更适合定时同步。
- 邮件提醒是同步后的附属动作：默认阈值为 `60,80,100`，单个邮箱或 SMTP 异常只记录到该池 `sync_error`，不影响快照入库和本次同步成功计数。
- 供应商接口级失败会把该供应商已有快照标记为 `failed` 并写入错误摘要，避免页面继续展示为正常快照。
