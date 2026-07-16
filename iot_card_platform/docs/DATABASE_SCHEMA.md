# 数据库设计

## 核心表结构

### 1. 物联网卡表 (iot_cards)

```sql
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

    -- 规格信息
    `carrier` ENUM('cmcc', 'cucc', 'ctcc') NOT NULL COMMENT '运营商',
    `flow_size` BIGINT NOT NULL COMMENT '套餐流量(MB)',
    `period_type` ENUM('monthly', 'yearly') NOT NULL COMMENT '周期类型',

    -- 生命周期日期
    `test_expire_date` DATE DEFAULT NULL COMMENT '测试期到期日',
    `silent_expire_date` DATE DEFAULT NULL COMMENT '沉默期到期日',
    `activated_at` DATE DEFAULT NULL COMMENT '激活日',
    `expired_at` DATE DEFAULT NULL COMMENT '套餐过期日',

    -- 流量使用
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
```

### 2. 流量池表 (traffic_pools)

```sql
CREATE TABLE `traffic_pools` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL COMMENT '流量池名称',
    `user_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '所属用户ID',

    -- 组池规则
    `carrier` ENUM('cmcc', 'cucc', 'ctcc') NOT NULL COMMENT '运营商',
    `flow_size` BIGINT NOT NULL COMMENT '单卡流量(MB)',
    `period_type` ENUM('monthly', 'yearly') NOT NULL COMMENT '周期类型',

    -- 统计
    `card_count` INT NOT NULL DEFAULT 0 COMMENT '卡片数量',
    `data_total` BIGINT NOT NULL DEFAULT 0 COMMENT '总流量(MB)',
    `data_used` BIGINT NOT NULL DEFAULT 0 COMMENT '已用流量(MB)',

    -- 告警阈值
    `alert_threshold` INT DEFAULT NULL COMMENT '告警阈值(%)',
    `stop_threshold` INT DEFAULT NULL COMMENT '停卡阈值(%)',

    `status` ENUM('enable', 'disable') DEFAULT 'enable',
    `remark` VARCHAR(500) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,

    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`)
) COMMENT='流量池表';
```

### 3. 用户表 (sys_users)

```sql
CREATE TABLE `sys_users` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `username` VARCHAR(50) NOT NULL COMMENT '用户名',
    `password` VARCHAR(255) NOT NULL COMMENT '密码',
    `real_name` VARCHAR(50) DEFAULT NULL COMMENT '真实姓名',
    `phone` VARCHAR(20) DEFAULT NULL COMMENT '手机号',
    `email` VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    `user_level` TINYINT NOT NULL COMMENT '用户级别: 1-超管, 2-用户, 3-子用户',
    `parent_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '父级用户ID',
    `status` ENUM('enable', 'disable') DEFAULT 'enable',
    `remark` VARCHAR(500) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`),
    KEY `idx_parent_id` (`parent_id`)
) COMMENT='用户表';
```

### 4. 套餐表 (packages)

```sql
CREATE TABLE `packages` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `package_id` VARCHAR(50) DEFAULT NULL COMMENT '套餐ID',
    `name` VARCHAR(100) NOT NULL COMMENT '套餐名称',
    `carrier` ENUM('cmcc', 'cucc', 'ctcc') NOT NULL COMMENT '运营商',
    `flow_size` BIGINT NOT NULL COMMENT '流量(MB)',
    `period_type` ENUM('monthly', 'yearly') NOT NULL COMMENT '周期类型',
    `valid_days` INT NOT NULL COMMENT '有效天数',
    `cost_price` DECIMAL(10,2) DEFAULT NULL COMMENT '成本价',
    `sale_price` DECIMAL(10,2) DEFAULT NULL COMMENT '销售价',
    `supplier_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '供应商ID',
    `user_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '专属客户ID',
    `enable_auto_pool` TINYINT DEFAULT 0 COMMENT '是否启用自动组池',
    `status` ENUM('enable', 'disable') DEFAULT 'enable',
    `remark` VARCHAR(500) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,

    PRIMARY KEY (`id`),
    KEY `idx_package_id` (`package_id`),
    KEY `idx_supplier_id` (`supplier_id`)
) COMMENT='套餐表';
```

### 5. 供应商表 (suppliers)

```sql
CREATE TABLE `suppliers` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL COMMENT '供应商名称',
    `api_url` VARCHAR(255) DEFAULT NULL COMMENT 'API地址',
    `api_key` VARCHAR(255) DEFAULT NULL COMMENT 'API密钥',
    `api_secret` VARCHAR(255) DEFAULT NULL COMMENT 'API密钥',
    `sync_interval` INT DEFAULT 60 COMMENT '同步间隔(分钟)',
    `status` ENUM('enable', 'disable') DEFAULT 'enable',
    `remark` VARCHAR(500) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,

    PRIMARY KEY (`id`)
) COMMENT='供应商表';
```

### 6. 出入库记录表

```sql
-- 入库记录
CREATE TABLE `stock_in_records` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `supplier_id` BIGINT UNSIGNED NOT NULL,
    `package_id` BIGINT UNSIGNED NOT NULL,
    `test_expire_date` DATE DEFAULT NULL,
    `silent_expire_date` DATE NOT NULL,
    `card_count` INT NOT NULL DEFAULT 0,
    `success_count` INT NOT NULL DEFAULT 0,
    `failed_count` INT NOT NULL DEFAULT 0,
    `remark` VARCHAR(500) DEFAULT NULL,
    `operator_id` BIGINT UNSIGNED DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,
    PRIMARY KEY (`id`)
) COMMENT='入库记录表';

-- 出库记录
CREATE TABLE `stock_out_records` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT UNSIGNED NOT NULL,
    `sale_package_id` BIGINT UNSIGNED NOT NULL,
    `card_count` INT NOT NULL DEFAULT 0,
    `success_count` INT NOT NULL DEFAULT 0,
    `failed_count` INT NOT NULL DEFAULT 0,
    `unit_price` DECIMAL(10,2) NOT NULL,
    `total_amount` DECIMAL(10,2) NOT NULL,
    `remark` VARCHAR(500) DEFAULT NULL,
    `operator_id` BIGINT UNSIGNED DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,
    PRIMARY KEY (`id`)
) COMMENT='出库记录表';
```

### 7. 项目表 (projects)

```sql
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
    KEY `idx_user_id` (`user_id`)
) COMMENT='项目表';
```

### 8. 渠道推广积分表

渠道积分模块使用五张新增表，完整可执行结构以迁移脚本 `app/db/migrations/20260715_add_channel_points.sql` 为准：

- `channel_partners`：独立渠道账号、H5 标识、状态和比例覆盖。
- `channel_commission_settings`：平台默认出库、续费积分比例。
- `channel_customer_relations`：手机号和平台用户唯一渠道归属，并保存客户设备、场景、规模等用户情况快照。
- `renewal_orders`：客户在线续费的结构化订单。
- `channel_point_ledger`：出库、续费和冲正的逐卡积分账本。

关键约束：

- `channel_customer_relations.customer_phone` 唯一，防止重复渠道归属。
- `channel_customer_relations.user_id` 唯一，保证一个平台用户只有一个有效渠道来源。
- `channel_customer_relations.customer_profile` 使用 `VARCHAR(500)`；历史记录可为空，新 H5 报备由接口校验为必填，新增迁移见 `20260715_add_channel_customer_profile.sql`。
- `channel_point_ledger(entry_type, order_type, source_order_id, card_id)` 唯一，保证计分和冲正幂等。
- 金额使用 `DECIMAL(14,2)`，比例使用 `DECIMAL(7,4)`，积分使用 `DECIMAL(14,4)`。
- 比例以账本快照保存，后续配置变化不回写历史数据。

## 索引设计

### 高频查询索引
- `iot_cards.iccid` - 唯一索引
- `iot_cards.user_id` - 普通索引
- `iot_cards.status` - 普通索引
- `iot_cards.carrier` - 普通索引
- `traffic_pools.user_id` - 普通索引
- `sys_users.username` - 唯一索引

- `channel_customer_relations.customer_phone` - 渠道归属唯一手机号
- `channel_point_ledger(channel_id, status, created_at)` - 渠道积分和结算状态查询
### 联合索引
- `iot_cards(carrier, status)` - 运营商+状态筛选
- `iot_cards(user_id, status)` - 用户卡片筛选
- `channel_point_ledger(entry_type, order_type, source_order_id, card_id)` - 积分来源幂等约束
