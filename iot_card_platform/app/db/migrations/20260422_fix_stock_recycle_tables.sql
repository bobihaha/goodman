-- 修复生产环境缺失的回收表结构
-- 目标：
-- 1. 如果 stock_recycle_records / stock_recycle_record_cards 不存在，则创建
-- 2. 如果为旧表结构，则补齐缺失字段

CREATE TABLE IF NOT EXISTS `stock_recycle_records` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `card_count` INT NOT NULL DEFAULT 0 COMMENT '回收数量',
    `success_count` INT NOT NULL DEFAULT 0 COMMENT '成功数量',
    `failed_count` INT NOT NULL DEFAULT 0 COMMENT '失败数量',
    `recycle_reason` VARCHAR(500) NOT NULL COMMENT '回收原因',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `operator_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '操作人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0 COMMENT '删除标记：0=未删除，1=已删除',
    PRIMARY KEY (`id`),
    KEY `idx_operator_id` (`operator_id`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='回收记录表';

CREATE TABLE IF NOT EXISTS `stock_recycle_record_cards` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `record_id` BIGINT UNSIGNED NOT NULL COMMENT '回收记录ID',
    `card_id` BIGINT UNSIGNED NOT NULL COMMENT '卡片ID',
    `iccid` VARCHAR(30) NOT NULL COMMENT 'ICCID',
    `original_user_id` BIGINT UNSIGNED NULL COMMENT '原用户ID',
    `original_status` VARCHAR(20) NULL COMMENT '原状态',
    `original_sale_package_id` BIGINT UNSIGNED NULL COMMENT '原销售套餐ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0 COMMENT '删除标记：0=未删除，1=已删除',
    PRIMARY KEY (`id`),
    KEY `idx_record_id` (`record_id`),
    KEY `idx_card_id` (`card_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='回收记录卡片关联表';

SET @sql = IF(
    EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'stock_recycle_record_cards'
          AND COLUMN_NAME = 'original_user_id'
    ),
    'SELECT 1',
    'ALTER TABLE stock_recycle_record_cards ADD COLUMN original_user_id BIGINT UNSIGNED NULL COMMENT ''原用户ID'' AFTER iccid'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'stock_recycle_record_cards'
          AND COLUMN_NAME = 'original_status'
    ),
    'SELECT 1',
    'ALTER TABLE stock_recycle_record_cards ADD COLUMN original_status VARCHAR(20) NULL COMMENT ''原状态'' AFTER original_user_id'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'stock_recycle_record_cards'
          AND COLUMN_NAME = 'original_sale_package_id'
    ),
    'SELECT 1',
    'ALTER TABLE stock_recycle_record_cards ADD COLUMN original_sale_package_id BIGINT UNSIGNED NULL COMMENT ''原销售套餐ID'' AFTER original_status'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'stock_recycle_record_cards'
          AND COLUMN_NAME = 'updated_at'
    ),
    'SELECT 1',
    'ALTER TABLE stock_recycle_record_cards ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'stock_recycle_record_cards'
          AND COLUMN_NAME = 'is_deleted'
    ),
    'SELECT 1',
    'ALTER TABLE stock_recycle_record_cards ADD COLUMN is_deleted TINYINT DEFAULT 0 COMMENT ''删除标记：0=未删除，1=已删除'' AFTER updated_at'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'stock_recycle_record_cards'
          AND INDEX_NAME = 'idx_record_id'
    ),
    'SELECT 1',
    'ALTER TABLE stock_recycle_record_cards ADD INDEX idx_record_id (record_id)'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'stock_recycle_record_cards'
          AND INDEX_NAME = 'idx_card_id'
    ),
    'SELECT 1',
    'ALTER TABLE stock_recycle_record_cards ADD INDEX idx_card_id (card_id)'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
