-- ============================================
-- 项目管理功能 - 数据库迁移脚本
-- 执行方式: mysql -u root -p < sql/add_project_management.sql
-- ============================================

USE iot_card_platform;

-- 1. 创建项目表
CREATE TABLE IF NOT EXISTS `projects` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '项目ID',
    `name` VARCHAR(100) NOT NULL COMMENT '项目名称',
    `user_id` BIGINT UNSIGNED NOT NULL COMMENT '所属用户ID',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT NOT NULL DEFAULT 0 COMMENT '删除标记',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目表';

-- 2. 在 iot_cards 表添加 project_id 字段（如果不存在）
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'iot_card_platform'
    AND TABLE_NAME = 'iot_cards'
    AND COLUMN_NAME = 'project_id');

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `iot_cards` ADD COLUMN `project_id` BIGINT UNSIGNED DEFAULT NULL COMMENT ''所属项目ID'' AFTER `sale_package_id`, ADD INDEX `idx_project_id` (`project_id`)',
    'SELECT ''project_id column already exists'' AS message');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3. 添加项目管理菜单（如果不存在）
INSERT INTO sys_menus (code, name, path, parent_id, user_level, type, icon, sort_order, status, created_at, updated_at)
SELECT 'projects', '项目管理', '/projects', NULL, 0, 'menu', 'folder', 15, 'enable', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM sys_menus WHERE code = 'projects');

-- 验证
SELECT '=== 项目表创建成功 ===' AS status;
SELECT COUNT(*) AS project_count FROM projects;
SELECT '=== 项目管理菜单 ===' AS status;
SELECT id, code, name, path, user_level, sort_order FROM sys_menus WHERE code = 'projects';
