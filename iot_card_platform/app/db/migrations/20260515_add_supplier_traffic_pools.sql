SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `supplier_traffic_pools` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `supplier_id` BIGINT UNSIGNED NOT NULL COMMENT '供应商ID',
    `supplier_name` VARCHAR(100) DEFAULT NULL COMMENT '供应商名称快照',
    `supplier_pool_code` VARCHAR(100) NOT NULL COMMENT '供应商流量池编码',
    `supplier_pool_name` VARCHAR(100) DEFAULT NULL COMMENT '供应商流量池名称',
    `carrier` VARCHAR(20) DEFAULT NULL COMMENT '运营商',
    `pool_specification` BIGINT DEFAULT NULL COMMENT '流量池规格(MB)',
    `total_flow` DOUBLE NOT NULL DEFAULT 0 COMMENT '总流量(MB)',
    `used_flow` DOUBLE NOT NULL DEFAULT 0 COMMENT '已用流量(MB)',
    `remaining_flow` DOUBLE NOT NULL DEFAULT 0 COMMENT '剩余流量(MB)',
    `package_flow` DOUBLE NOT NULL DEFAULT 0 COMMENT '叠加包量(MB)',
    `usage_percent` DOUBLE NOT NULL DEFAULT 0 COMMENT '使用率(%)',
    `total_card_count` INT NOT NULL DEFAULT 0 COMMENT '总卡数',
    `active_card_count` INT NOT NULL DEFAULT 0 COMMENT '激活卡数',
    `suspended_card_count` INT NOT NULL DEFAULT 0 COMMENT '停卡卡数',
    `stock_card_count` INT NOT NULL DEFAULT 0 COMMENT '库存卡数',
    `testing_card_count` INT NOT NULL DEFAULT 0 COMMENT '测试期卡数',
    `cancelled_card_count` INT NOT NULL DEFAULT 0 COMMENT '销卡卡数',
    `activation_ready_count` INT NOT NULL DEFAULT 0 COMMENT '待激活卡数',
    `alert_threshold` INT DEFAULT NULL COMMENT '邮件提醒阈值(%)',
    `alert_thresholds` VARCHAR(100) NOT NULL DEFAULT '60,80,100' COMMENT '邮件提醒阈值列表(%)',
    `alert_emails` TEXT DEFAULT NULL COMMENT '提醒邮箱',
    `last_alert_at` DATETIME DEFAULT NULL COMMENT '最近提醒时间',
    `last_alert_usage_percent` DOUBLE DEFAULT NULL COMMENT '最近提醒使用率',
    `last_alert_threshold` INT DEFAULT NULL COMMENT '最近提醒阈值(%)',
    `last_sync_at` DATETIME DEFAULT NULL COMMENT '最近同步时间',
    `sync_status` VARCHAR(20) NOT NULL DEFAULT 'success' COMMENT '同步状态',
    `sync_error` VARCHAR(500) DEFAULT NULL COMMENT '同步错误',
    `raw_data` JSON DEFAULT NULL COMMENT '供应商原始数据',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_supplier_pool_code` (`supplier_id`, `supplier_pool_code`),
    KEY `idx_supplier_id` (`supplier_id`),
    KEY `idx_carrier` (`carrier`),
    KEY `idx_pool_specification` (`pool_specification`),
    KEY `idx_usage_percent` (`usage_percent`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='供应商侧流量池快照表';

CREATE TABLE IF NOT EXISTS `supplier_traffic_pool_histories` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `supplier_pool_id` BIGINT UNSIGNED NOT NULL COMMENT '供应商流量池快照ID',
    `supplier_id` BIGINT UNSIGNED NOT NULL COMMENT '供应商ID',
    `supplier_name` VARCHAR(100) DEFAULT NULL COMMENT '供应商名称快照',
    `supplier_pool_code` VARCHAR(100) NOT NULL COMMENT '供应商流量池编码',
    `supplier_pool_name` VARCHAR(100) DEFAULT NULL COMMENT '供应商流量池名称',
    `record_month` VARCHAR(7) NOT NULL COMMENT '记录月份 YYYY-MM',
    `carrier` VARCHAR(20) DEFAULT NULL COMMENT '运营商',
    `pool_specification` BIGINT DEFAULT NULL COMMENT '流量池规格(MB)',
    `total_flow` DOUBLE NOT NULL DEFAULT 0 COMMENT '总流量(MB)',
    `used_flow` DOUBLE NOT NULL DEFAULT 0 COMMENT '已用流量(MB)',
    `remaining_flow` DOUBLE NOT NULL DEFAULT 0 COMMENT '剩余流量(MB)',
    `package_flow` DOUBLE NOT NULL DEFAULT 0 COMMENT '叠加包量(MB)',
    `usage_percent` DOUBLE NOT NULL DEFAULT 0 COMMENT '使用率(%)',
    `total_card_count` INT NOT NULL DEFAULT 0 COMMENT '总卡数',
    `active_card_count` INT NOT NULL DEFAULT 0 COMMENT '激活卡数',
    `sync_at` DATETIME DEFAULT NULL COMMENT '本月快照同步时间',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_supplier_pool_month` (`supplier_pool_id`, `record_month`),
    KEY `idx_supplier_pool_id` (`supplier_pool_id`),
    KEY `idx_supplier_id` (`supplier_id`),
    KEY `idx_record_month` (`record_month`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='供应商侧流量池月度历史快照表';

INSERT INTO sys_menus (parent_id, user_level, code, name, type, icon, path, component, permission, sort_order, is_visible, status, created_at, updated_at)
SELECT 0, 1, 'supplier_traffic_pools', '供应商流量池管理', 'menu', 'Connection', '/supplier-traffic-pools', 'views/supplier-traffic-pools/index.vue', 'supplier_traffic_pool:view', 2, 1, 'enable', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM sys_menus WHERE code = 'supplier_traffic_pools');

INSERT IGNORE INTO sys_user_menus (user_id, menu_id, created_at)
SELECT id, (SELECT id FROM sys_menus WHERE code = 'supplier_traffic_pools'), NOW()
FROM sys_users
WHERE user_level = 1 AND is_deleted = 0;
