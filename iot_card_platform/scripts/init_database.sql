-- ============================================
-- 物联网卡管理平台 - 数据库初始化脚本
-- MySQL 8.4.7 兼容
-- ============================================

CREATE DATABASE IF NOT EXISTS iot_card_platform 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE iot_card_platform;

-- 用户表 (三级架构)
DROP TABLE IF EXISTS `sys_users`;
CREATE TABLE `sys_users` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    `parent_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '上级用户ID',
    `user_level` TINYINT NOT NULL DEFAULT 1 COMMENT '用户层级: 1=超级管理员, 2=用户, 3=子用户',
    `name` VARCHAR(50) NOT NULL COMMENT '用户名称',
    `account` VARCHAR(50) NOT NULL COMMENT '用户账户',
    `password` VARCHAR(128) NOT NULL COMMENT '用户密码(加密)',
    `phone` VARCHAR(20) DEFAULT NULL COMMENT '手机号',
    `email` VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    `avatar` VARCHAR(255) DEFAULT NULL COMMENT '头像URL',
    `alert_notify` JSON DEFAULT NULL COMMENT '告警通知配置',
    `quota` JSON DEFAULT NULL COMMENT '账户配额',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `status` ENUM('enable', 'disable') NOT NULL DEFAULT 'enable' COMMENT '状态',
    `last_login_at` DATETIME DEFAULT NULL COMMENT '最后登录时间',
    `last_login_ip` VARCHAR(50) DEFAULT NULL COMMENT '最后登录IP',
    `created_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人ID',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT NOT NULL DEFAULT 0 COMMENT '删除标记',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_account` (`account`),
    KEY `idx_parent_id` (`parent_id`),
    KEY `idx_user_level` (`user_level`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统用户表';

-- 菜单表
DROP TABLE IF EXISTS `sys_menus`;
CREATE TABLE `sys_menus` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '菜单ID',
    `parent_id` BIGINT UNSIGNED DEFAULT 0 COMMENT '父菜单ID',
    `user_level` TINYINT NOT NULL DEFAULT 0 COMMENT '适用层级: 0=通用, 1=超级管理员, 2=用户, 3=子用户',
    `code` VARCHAR(50) NOT NULL COMMENT '菜单编码',
    `name` VARCHAR(50) NOT NULL COMMENT '菜单名称',
    `type` ENUM('directory', 'menu', 'button') NOT NULL DEFAULT 'menu' COMMENT '类型',
    `icon` VARCHAR(50) DEFAULT NULL COMMENT '图标',
    `path` VARCHAR(255) DEFAULT NULL COMMENT '路由路径',
    `component` VARCHAR(255) DEFAULT NULL COMMENT '组件路径',
    `permission` VARCHAR(100) DEFAULT NULL COMMENT '权限标识',
    `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序',
    `is_visible` TINYINT NOT NULL DEFAULT 1 COMMENT '是否可见',
    `status` ENUM('enable', 'disable') NOT NULL DEFAULT 'enable' COMMENT '状态',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT NOT NULL DEFAULT 0 COMMENT '删除标记',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_code` (`code`),
    KEY `idx_parent_id` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统菜单表';

-- 用户菜单关联表
DROP TABLE IF EXISTS `sys_user_menus`;
CREATE TABLE `sys_user_menus` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    `menu_id` BIGINT UNSIGNED NOT NULL COMMENT '菜单ID',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `is_deleted` TINYINT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_menu` (`user_id`, `menu_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户菜单权限表';

-- 登录日志表
DROP TABLE IF EXISTS `sys_login_logs`;
CREATE TABLE `sys_login_logs` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '用户ID',
    `account` VARCHAR(50) DEFAULT NULL COMMENT '登录账户',
    `login_type` ENUM('normal', 'super') NOT NULL DEFAULT 'normal' COMMENT '登录类型',
    `operator_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '操作人ID(超级登录)',
    `is_success` TINYINT NOT NULL DEFAULT 1 COMMENT '是否成功',
    `fail_reason` VARCHAR(200) DEFAULT NULL COMMENT '失败原因',
    `ip` VARCHAR(50) DEFAULT NULL COMMENT 'IP地址',
    `user_agent` VARCHAR(500) DEFAULT NULL COMMENT 'User-Agent',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `is_deleted` TINYINT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='登录日志表';

-- 初始化超级管理员 (密码: admin123)
INSERT INTO `sys_users` (`id`, `parent_id`, `user_level`, `name`, `account`, `password`, `phone`, `status`, `quota`, `remark`)
VALUES (1, NULL, 1, '超级管理员', 'admin', '$2b$12$SrdjFNBnLZwVWcK64vvKFe.rIdM1rOUG3herNDGsIeFVkgrFGlrDW', '13800138000', 'enable', '{"max_cards": -1, "max_sub_users": -1}', '系统初始化超级管理员');

-- 初始化菜单
INSERT INTO `sys_menus` (`id`, `parent_id`, `user_level`, `code`, `name`, `type`, `icon`, `path`, `permission`, `sort_order`) VALUES
(1, 0, 0, 'dashboard', '仪表盘', 'menu', 'dashboard', '/dashboard', 'dashboard:view', 1),
(10, 0, 1, 'user_manage', '用户管理', 'directory', 'user', '/user', NULL, 10),
(11, 10, 1, 'user_list', '用户列表', 'menu', 'peoples', '/user/list', 'user:list', 1),
(12, 10, 1, 'user_add', '新增用户', 'button', NULL, NULL, 'user:add', 2),
(20, 0, 2, 'sub_user_manage', '子用户管理', 'directory', 'user', '/sub-user', NULL, 10),
(21, 20, 2, 'sub_user_list', '子用户列表', 'menu', 'peoples', '/sub-user/list', 'sub_user:list', 1),
(30, 0, 0, 'card_manage', '卡片管理', 'directory', 'sim-card', '/card', NULL, 20),
(31, 30, 0, 'card_list', '卡片列表', 'menu', 'list', '/card/list', 'card:list', 1);

COMMIT;
