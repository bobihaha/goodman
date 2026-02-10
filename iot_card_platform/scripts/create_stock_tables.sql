-- ============================================
-- 出入库管理模块 - 新增数据库表
-- 创建日期: 2026-02-09
-- ============================================

-- 1. 入库记录表
CREATE TABLE IF NOT EXISTS `stock_in_records` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `supplier_id` BIGINT UNSIGNED NOT NULL COMMENT '供应商ID',
    `package_id` BIGINT UNSIGNED NOT NULL COMMENT '底层套餐ID',
    
    -- 生命周期配置
    `test_expire_date` DATE DEFAULT NULL COMMENT '测试期到期日',
    `silent_expire_date` DATE NOT NULL COMMENT '沉默期到期日',
    
    `card_count` INT NOT NULL DEFAULT 0 COMMENT '卡片数量',
    `success_count` INT NOT NULL DEFAULT 0 COMMENT '成功数量',
    `failed_count` INT NOT NULL DEFAULT 0 COMMENT '失败数量',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `operator_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '操作人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,
    
    PRIMARY KEY (`id`),
    KEY `idx_supplier_id` (`supplier_id`),
    KEY `idx_package_id` (`package_id`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='入库记录表';

-- 2. 出库记录表
CREATE TABLE IF NOT EXISTS `stock_out_records` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT UNSIGNED NOT NULL COMMENT '目标用户ID',
    `sale_package_id` BIGINT UNSIGNED NOT NULL COMMENT '销售套餐ID',
    
    `card_count` INT NOT NULL DEFAULT 0 COMMENT '卡片数量',
    `success_count` INT NOT NULL DEFAULT 0 COMMENT '成功数量',
    `failed_count` INT NOT NULL DEFAULT 0 COMMENT '失败数量',
    `unit_price` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '单价',
    `total_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '总金额',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `operator_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '操作人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,
    
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_sale_package_id` (`sale_package_id`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='出库记录表';

-- 3. 回收记录表
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
    `is_deleted` TINYINT DEFAULT 0,
    
    PRIMARY KEY (`id`),
    KEY `idx_operator_id` (`operator_id`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='回收记录表';

-- 4. 入库记录与卡片关联表（用于记录哪些卡片属于哪个入库记录）
CREATE TABLE IF NOT EXISTS `stock_in_record_cards` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `record_id` BIGINT UNSIGNED NOT NULL COMMENT '入库记录ID',
    `card_id` BIGINT UNSIGNED NOT NULL COMMENT '卡片ID',
    `iccid` VARCHAR(30) NOT NULL COMMENT 'ICCID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    KEY `idx_record_id` (`record_id`),
    KEY `idx_card_id` (`card_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='入库记录卡片关联表';

-- 5. 出库记录与卡片关联表
CREATE TABLE IF NOT EXISTS `stock_out_record_cards` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `record_id` BIGINT UNSIGNED NOT NULL COMMENT '出库记录ID',
    `card_id` BIGINT UNSIGNED NOT NULL COMMENT '卡片ID',
    `iccid` VARCHAR(30) NOT NULL COMMENT 'ICCID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    KEY `idx_record_id` (`record_id`),
    KEY `idx_card_id` (`card_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='出库记录卡片关联表';

-- 6. 回收记录与卡片关联表
CREATE TABLE IF NOT EXISTS `stock_recycle_record_cards` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `record_id` BIGINT UNSIGNED NOT NULL COMMENT '回收记录ID',
    `card_id` BIGINT UNSIGNED NOT NULL COMMENT '卡片ID',
    `iccid` VARCHAR(30) NOT NULL COMMENT 'ICCID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    KEY `idx_record_id` (`record_id`),
    KEY `idx_card_id` (`card_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='回收记录卡片关联表';

