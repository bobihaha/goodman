SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `channel_partners` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL COMMENT '渠道名称',
    `contact_name` VARCHAR(50) NOT NULL COMMENT '联系人',
    `phone` VARCHAR(20) NOT NULL COMMENT '联系电话',
    `account` VARCHAR(50) NOT NULL COMMENT '渠道登录账号',
    `password` VARCHAR(128) NOT NULL COMMENT '密码哈希',
    `h5_slug` VARCHAR(32) NOT NULL COMMENT '客户报备H5标识',
    `registration_enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否允许H5报备',
    `status` VARCHAR(20) NOT NULL DEFAULT 'enable' COMMENT 'enable/disable',
    `stock_out_rate_override` DECIMAL(7,4) DEFAULT NULL COMMENT '出库积分比例覆盖(%)',
    `renewal_rate_override` DECIMAL(7,4) DEFAULT NULL COMMENT '续费积分比例覆盖(%)',
    `last_login_at` DATETIME DEFAULT NULL COMMENT '最近登录时间',
    `created_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人ID',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_channel_partner_phone` (`phone`),
    UNIQUE KEY `uk_channel_partner_account` (`account`),
    UNIQUE KEY `uk_channel_partner_h5_slug` (`h5_slug`),
    KEY `idx_channel_partner_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='渠道伙伴表';

CREATE TABLE IF NOT EXISTS `channel_commission_settings` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `default_stock_out_rate` DECIMAL(7,4) NOT NULL DEFAULT 0 COMMENT '默认出库积分比例(%)',
    `default_renewal_rate` DECIMAL(7,4) NOT NULL DEFAULT 0 COMMENT '默认续费积分比例(%)',
    `updated_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '更新人ID',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='渠道积分默认设置';

INSERT INTO `channel_commission_settings` (`id`, `default_stock_out_rate`, `default_renewal_rate`, `created_at`, `updated_at`)
VALUES (1, 0, 0, NOW(), NOW())
ON DUPLICATE KEY UPDATE `id` = `id`;

CREATE TABLE IF NOT EXISTS `channel_customer_relations` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `channel_id` BIGINT UNSIGNED NOT NULL COMMENT '渠道ID',
    `user_id` BIGINT UNSIGNED NOT NULL COMMENT '平台用户ID',
    `customer_name` VARCHAR(50) NOT NULL COMMENT '客户姓名快照',
    `customer_phone` VARCHAR(20) NOT NULL COMMENT '客户手机号快照',
    `status` VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active/inactive',
    `source` VARCHAR(30) NOT NULL DEFAULT 'channel_h5' COMMENT '归属来源',
    `registered_ip` VARCHAR(50) DEFAULT NULL COMMENT '报备IP',
    `registered_user_agent` VARCHAR(500) DEFAULT NULL COMMENT '报备User-Agent',
    `registered_at` DATETIME NOT NULL COMMENT '报备时间',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_channel_customer_phone` (`customer_phone`),
    UNIQUE KEY `uk_channel_customer_user` (`user_id`),
    KEY `idx_channel_customer_channel_status` (`channel_id`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='渠道客户归属表';

CREATE TABLE IF NOT EXISTS `renewal_orders` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `order_no` VARCHAR(50) NOT NULL COMMENT '续费订单号',
    `user_id` BIGINT UNSIGNED NOT NULL COMMENT '购买用户ID',
    `card_id` BIGINT UNSIGNED NOT NULL COMMENT '卡片ID',
    `iccid` VARCHAR(30) NOT NULL COMMENT 'ICCID',
    `renew_months` INT NOT NULL COMMENT '续费月数',
    `unit_price` DECIMAL(12,2) NOT NULL COMMENT '续费单价(元/月)',
    `total_amount` DECIMAL(14,2) NOT NULL COMMENT '订单总额(元)',
    `status` VARCHAR(20) NOT NULL DEFAULT 'completed' COMMENT 'completed/reversed',
    `completed_at` DATETIME NOT NULL COMMENT '完成时间',
    `operator_id` BIGINT UNSIGNED NOT NULL COMMENT '操作用户ID',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_renewal_order_no` (`order_no`),
    KEY `idx_renewal_order_user` (`user_id`),
    KEY `idx_renewal_order_card` (`card_id`),
    KEY `idx_renewal_order_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='单卡续费订单表';

CREATE TABLE IF NOT EXISTS `channel_point_ledger` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `channel_id` BIGINT UNSIGNED NOT NULL COMMENT '渠道ID',
    `relation_id` BIGINT UNSIGNED NOT NULL COMMENT '渠道客户关系ID',
    `user_id` BIGINT UNSIGNED NOT NULL COMMENT '平台客户ID',
    `customer_name` VARCHAR(50) NOT NULL COMMENT '客户姓名快照',
    `customer_phone` VARCHAR(20) NOT NULL COMMENT '客户手机号快照',
    `entry_type` VARCHAR(20) NOT NULL DEFAULT 'credit' COMMENT 'credit/reversal',
    `order_type` VARCHAR(20) NOT NULL COMMENT 'stock_out/renewal',
    `source_order_id` BIGINT UNSIGNED NOT NULL COMMENT '来源订单ID',
    `source_order_no` VARCHAR(50) NOT NULL COMMENT '来源订单号',
    `card_id` BIGINT UNSIGNED NOT NULL COMMENT '卡片ID',
    `iccid` VARCHAR(30) NOT NULL COMMENT 'ICCID',
    `base_amount` DECIMAL(14,2) NOT NULL COMMENT '计佣基数(元)',
    `rate_percent` DECIMAL(7,4) NOT NULL COMMENT '比例快照(%)',
    `points` DECIMAL(14,4) NOT NULL COMMENT '推广积分',
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'pending/settled',
    `related_entry_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '冲正关联的原积分ID',
    `settled_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '结算人ID',
    `settled_at` DATETIME DEFAULT NULL COMMENT '结算时间',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_channel_point_source_card` (`entry_type`, `order_type`, `source_order_id`, `card_id`),
    KEY `idx_channel_point_channel_status_time` (`channel_id`, `status`, `created_at`),
    KEY `idx_channel_point_user_time` (`user_id`, `created_at`),
    KEY `idx_channel_point_source_no` (`source_order_no`),
    KEY `idx_channel_point_related` (`related_entry_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='渠道推广积分账本';

INSERT INTO sys_menus (parent_id, user_level, code, name, type, icon, path, component, permission, sort_order, is_visible, status, created_at, updated_at)
SELECT 0, 1, 'channel_points', '渠道积分管理', 'menu', 'Money', '/channels', 'views/channels/admin.vue', 'channel_points:manage', 5, 1, 'enable', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM sys_menus WHERE code = 'channel_points');

INSERT IGNORE INTO sys_user_menus (user_id, menu_id, created_at)
SELECT id, (SELECT id FROM sys_menus WHERE code = 'channel_points'), NOW()
FROM sys_users
WHERE user_level = 1 AND is_deleted = 0;
