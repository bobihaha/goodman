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
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_account` (`account`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='登录日志表';

-- 操作日志表
DROP TABLE IF EXISTS `sys_operation_logs`;
CREATE TABLE `sys_operation_logs` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '用户ID',
    `user_name` VARCHAR(50) DEFAULT NULL COMMENT '用户名称',
    `module` VARCHAR(50) NOT NULL COMMENT '操作模块',
    `action` VARCHAR(50) NOT NULL COMMENT '操作动作',
    `target_type` VARCHAR(50) DEFAULT NULL COMMENT '目标类型',
    `target_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '目标ID',
    `target_name` VARCHAR(100) DEFAULT NULL COMMENT '目标名称',
    `detail` TEXT COMMENT '操作详情JSON',
    `ip` VARCHAR(50) DEFAULT NULL COMMENT 'IP地址',
    `is_success` TINYINT NOT NULL DEFAULT 1 COMMENT '是否成功',
    `error_msg` VARCHAR(500) DEFAULT NULL COMMENT '错误信息',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_module` (`module`),
    KEY `idx_action` (`action`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- 系统配置表
DROP TABLE IF EXISTS `sys_configs`;
CREATE TABLE `sys_configs` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `config_key` VARCHAR(100) NOT NULL COMMENT '配置键',
    `config_value` TEXT COMMENT '配置值',
    `config_type` VARCHAR(20) NOT NULL DEFAULT 'string' COMMENT '配置类型: string/number/json/boolean',
    `description` VARCHAR(200) DEFAULT NULL COMMENT '配置描述',
    `is_public` TINYINT NOT NULL DEFAULT 0 COMMENT '是否公开: 0=否, 1=是',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_config_key` (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- 通知模板表
DROP TABLE IF EXISTS `sys_notify_templates`;
CREATE TABLE `sys_notify_templates` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `code` VARCHAR(50) NOT NULL COMMENT '模板编码',
    `name` VARCHAR(100) NOT NULL COMMENT '模板名称',
    `type` ENUM('sms', 'email', 'wechat', 'webhook') NOT NULL DEFAULT 'sms' COMMENT '通知类型',
    `title` VARCHAR(200) DEFAULT NULL COMMENT '标题模板',
    `content` TEXT NOT NULL COMMENT '内容模板',
    `variables` JSON COMMENT '可用变量列表',
    `is_enabled` TINYINT NOT NULL DEFAULT 1 COMMENT '是否启用',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `created_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人ID',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_code` (`code`),
    KEY `idx_type` (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知模板表';

-- ============================================
-- 供应商与套餐管理模块
-- ============================================

-- 供应商表
DROP TABLE IF EXISTS `suppliers`;
CREATE TABLE `suppliers` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '供应商ID',
    `name` VARCHAR(100) NOT NULL COMMENT '供应商名称',
    `code` VARCHAR(50) NOT NULL COMMENT '供应商编码',
    `type` ENUM('cmcc', 'cucc', 'ctcc', 'mvno', 'other') NOT NULL DEFAULT 'other' COMMENT '供应商类型: cmcc=移动, cucc=联通, ctcc=电信, mvno=虚拟运营商, other=其他',
    `contact_name` VARCHAR(50) DEFAULT NULL COMMENT '联系人',
    `contact_phone` VARCHAR(20) DEFAULT NULL COMMENT '联系电话',
    `contact_email` VARCHAR(100) DEFAULT NULL COMMENT '联系邮箱',
    `api_url` VARCHAR(255) DEFAULT NULL COMMENT 'API地址',
    `api_key` VARCHAR(255) DEFAULT NULL COMMENT 'API Key',
    `api_secret` VARCHAR(255) DEFAULT NULL COMMENT 'API Secret',
    `api_config` JSON DEFAULT NULL COMMENT 'API配置(扩展字段)',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `status` ENUM('enable', 'disable') NOT NULL DEFAULT 'enable' COMMENT '状态',
    `created_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人ID',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT NOT NULL DEFAULT 0 COMMENT '删除标记',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_code` (`code`),
    KEY `idx_type` (`type`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='供应商表';

-- 底层套餐表 (供应商套餐)
-- 规格三要素: 运营商 + 流量 + 周期类型
DROP TABLE IF EXISTS `supplier_packages`;
CREATE TABLE `supplier_packages` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '套餐ID',
    `supplier_id` BIGINT UNSIGNED NOT NULL COMMENT '供应商ID',
    `name` VARCHAR(100) NOT NULL COMMENT '套餐名称',
    `code` VARCHAR(50) NOT NULL COMMENT '套餐编码',
    -- 规格三要素
    `carrier` ENUM('cmcc', 'cucc', 'ctcc') NOT NULL COMMENT '运营商: cmcc=移动, cucc=联通, ctcc=电信',
    `flow_size` BIGINT NOT NULL COMMENT '流量大小(MB)',
    `period_type` ENUM('monthly', 'yearly') NOT NULL DEFAULT 'monthly' COMMENT '周期类型: monthly=月包, yearly=年包',
    -- 有效期配置 (月包30天, 年包360天)
    `effective_days` INT NOT NULL DEFAULT 30 COMMENT '激活后有效天数(月包30/年包360)',
    `price_cost` DECIMAL(10, 2) NOT NULL COMMENT '成本价(元)',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `status` ENUM('enable', 'disable') NOT NULL DEFAULT 'enable' COMMENT '状态',
    `created_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人ID',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT NOT NULL DEFAULT 0 COMMENT '删除标记',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_code` (`code`),
    KEY `idx_supplier_id` (`supplier_id`),
    KEY `idx_carrier` (`carrier`),
    KEY `idx_period_type` (`period_type`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='底层套餐表(供应商套餐)';

-- 销售套餐表 (客户侧套餐)
-- 规格三要素: 运营商 + 流量 + 周期类型
DROP TABLE IF EXISTS `sale_packages`;
CREATE TABLE `sale_packages` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '套餐ID',
    `user_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '所属用户ID(NULL=平台套餐)',
    `base_package_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '关联底层套餐ID',
    `name` VARCHAR(100) NOT NULL COMMENT '套餐名称',
    `code` VARCHAR(50) NOT NULL COMMENT '套餐编码',
    -- 规格三要素
    `carrier` ENUM('cmcc', 'cucc', 'ctcc') NOT NULL COMMENT '运营商',
    `flow_size` BIGINT NOT NULL COMMENT '流量大小(MB)',
    `period_type` ENUM('monthly', 'yearly') NOT NULL DEFAULT 'monthly' COMMENT '周期类型',
    -- 有效期配置
    `effective_days` INT NOT NULL DEFAULT 30 COMMENT '激活后有效天数',
    -- 价格
    `price_cost` DECIMAL(10, 2) NOT NULL COMMENT '成本价(元)',
    `price_sale` DECIMAL(10, 2) NOT NULL COMMENT '销售价(元)',
    -- 展示配置
    `is_public` TINYINT NOT NULL DEFAULT 0 COMMENT '是否公开',
    `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `status` ENUM('enable', 'disable') NOT NULL DEFAULT 'enable' COMMENT '状态',
    `created_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人ID',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT NOT NULL DEFAULT 0 COMMENT '删除标记',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_code` (`code`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_base_package_id` (`base_package_id`),
    KEY `idx_carrier` (`carrier`),
    KEY `idx_period_type` (`period_type`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='销售套餐表';

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
(31, 30, 0, 'card_list', '卡片列表', 'menu', 'list', '/card/list', 'card:list', 1),
(32, 30, 0, 'card_search', '卡片搜索', 'button', NULL, NULL, 'card:search', 2),
(33, 30, 0, 'card_transfer', '卡片划拨', 'button', NULL, NULL, 'card:transfer', 3),
(34, 30, 0, 'card_remark', '卡片备注', 'button', NULL, NULL, 'card:remark', 4),
(35, 30, 0, 'card_export', '卡片导出', 'button', NULL, NULL, 'card:export', 5),
-- 供应商管理 (仅超级管理员)
(40, 0, 1, 'supplier_manage', '供应商管理', 'directory', 'supplier', '/supplier', NULL, 30),
(41, 40, 1, 'supplier_list', '供应商列表', 'menu', 'list', '/supplier/list', 'supplier:list', 1),
(42, 40, 1, 'supplier_add', '新增供应商', 'button', NULL, NULL, 'supplier:add', 2),
-- 底层套餐管理 (仅超级管理员)
(50, 0, 1, 'supplier_package', '底层套餐', 'directory', 'package', '/package/supplier', NULL, 31),
(51, 50, 1, 'supplier_package_list', '套餐列表', 'menu', 'list', '/package/supplier/list', 'supplier_package:list', 1),
(52, 50, 1, 'supplier_package_add', '新增套餐', 'button', NULL, NULL, 'supplier_package:add', 2),
-- 销售套餐管理 (超级管理员和用户)
(60, 0, 0, 'sale_package', '销售套餐', 'directory', 'price-tag', '/package/sale', NULL, 32),
(61, 60, 0, 'sale_package_list', '套餐列表', 'menu', 'list', '/package/sale/list', 'sale_package:list', 1),
(62, 60, 0, 'sale_package_add', '新增套餐', 'button', NULL, NULL, 'sale_package:add', 2);

-- ============================================
-- 物联网卡管理模块
-- ============================================

-- 物联网卡表
DROP TABLE IF EXISTS `iot_cards`;
CREATE TABLE `iot_cards` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '卡片ID',
    -- 卡片标识
    `iccid` VARCHAR(30) NOT NULL COMMENT 'ICCID',
    `imsi` VARCHAR(20) DEFAULT NULL COMMENT 'IMSI',
    `msisdn` VARCHAR(20) DEFAULT NULL COMMENT '号码',
    -- 归属关系
    `user_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '当前所属用户ID',
    `supplier_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '供应商ID',
    `batch_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '采购批次ID',
    `sale_package_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '销售套餐ID',
    -- 规格信息 (冗余，方便查询和组池)
    `carrier` ENUM('cmcc', 'cucc', 'ctcc') NOT NULL COMMENT '运营商',
    `flow_size` BIGINT NOT NULL COMMENT '套餐流量(MB)',
    `period_type` ENUM('monthly', 'yearly') NOT NULL COMMENT '周期类型',
    -- 生命周期日期 (格式: YYYY-MM-DD, 显示为 26/1/31)
    `test_expire_date` DATE DEFAULT NULL COMMENT '测试期到期日',
    `silent_expire_date` DATE DEFAULT NULL COMMENT '沉默期到期日',
    `activated_at` DATE DEFAULT NULL COMMENT '激活日',
    `expired_at` DATE DEFAULT NULL COMMENT '套餐过期日',
    -- 流量使用 (单位: MB)
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
    `created_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '删除标记',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_iccid` (`iccid`),
    KEY `idx_msisdn` (`msisdn`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_supplier_id` (`supplier_id`),
    KEY `idx_batch_id` (`batch_id`),
    KEY `idx_carrier` (`carrier`),
    KEY `idx_status` (`status`),
    KEY `idx_pool_id` (`pool_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='物联网卡表';

-- 卡片划拨记录表
DROP TABLE IF EXISTS `card_transfers`;
CREATE TABLE `card_transfers` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
    `card_id` BIGINT UNSIGNED NOT NULL COMMENT '卡片ID',
    `iccid` VARCHAR(30) NOT NULL COMMENT 'ICCID',
    `from_user_id` BIGINT UNSIGNED NOT NULL COMMENT '原用户ID',
    `to_user_id` BIGINT UNSIGNED NOT NULL COMMENT '目标用户ID',
    `operator_id` BIGINT UNSIGNED NOT NULL COMMENT '操作人ID',
    `remark` VARCHAR(200) DEFAULT NULL COMMENT '备注',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '删除标记',
    PRIMARY KEY (`id`),
    KEY `idx_card_id` (`card_id`),
    KEY `idx_from_user_id` (`from_user_id`),
    KEY `idx_to_user_id` (`to_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='卡片划拨记录表';

-- 采购批次表
DROP TABLE IF EXISTS `purchase_batches`;
CREATE TABLE `purchase_batches` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '批次ID',
    `batch_no` VARCHAR(50) NOT NULL COMMENT '批次号',
    `supplier_id` BIGINT UNSIGNED NOT NULL COMMENT '供应商ID',
    `package_id` BIGINT UNSIGNED NOT NULL COMMENT '底层套餐ID',
    -- 规格信息 (冗余)
    `carrier` ENUM('cmcc', 'cucc', 'ctcc') NOT NULL COMMENT '运营商',
    `flow_size` BIGINT NOT NULL COMMENT '套餐流量(MB)',
    `period_type` ENUM('monthly', 'yearly') NOT NULL COMMENT '周期类型',
    -- 生命周期配置
    `test_expire_date` DATE DEFAULT NULL COMMENT '测试期到期日',
    `silent_expire_date` DATE NOT NULL COMMENT '沉默期到期日',
    -- 数量统计
    `card_count` INT NOT NULL DEFAULT 0 COMMENT '卡片总数',
    `stocked_count` INT NOT NULL DEFAULT 0 COMMENT '已入库数',
    `out_count` INT NOT NULL DEFAULT 0 COMMENT '已出库数',
    `purchase_date` DATE NOT NULL COMMENT '采购日期',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `status` ENUM('pending', 'stocked', 'completed') DEFAULT 'pending' COMMENT '状态',
    `created_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '删除标记',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_batch_no` (`batch_no`),
    KEY `idx_supplier_id` (`supplier_id`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='采购批次表';

-- 入库记录表
DROP TABLE IF EXISTS `stock_in_records`;
CREATE TABLE `stock_in_records` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
    `record_no` VARCHAR(50) NOT NULL COMMENT '入库单号',
    `batch_id` BIGINT UNSIGNED NOT NULL COMMENT '批次ID',
    `card_count` INT NOT NULL DEFAULT 0 COMMENT '入库卡数',
    `success_count` INT NOT NULL DEFAULT 0 COMMENT '成功数',
    `fail_count` INT NOT NULL DEFAULT 0 COMMENT '失败数',
    `import_data` TEXT COMMENT '导入数据JSON',
    `fail_reason` TEXT COMMENT '失败原因JSON',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `status` ENUM('pending', 'confirmed') DEFAULT 'pending' COMMENT '状态',
    `confirmed_at` DATETIME DEFAULT NULL COMMENT '确认时间',
    `confirmed_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '确认人ID',
    `created_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '删除标记',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_record_no` (`record_no`),
    KEY `idx_batch_id` (`batch_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='入库记录表';

-- 出库记录表
DROP TABLE IF EXISTS `stock_out_records`;
CREATE TABLE `stock_out_records` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
    `record_no` VARCHAR(50) NOT NULL COMMENT '出库单号',
    `to_user_id` BIGINT UNSIGNED NOT NULL COMMENT '目标用户ID',
    `sale_package_id` BIGINT UNSIGNED NOT NULL COMMENT '销售套餐ID',
    `card_count` INT NOT NULL DEFAULT 0 COMMENT '出库卡数',
    `card_ids` TEXT COMMENT '卡片ID列表JSON',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `status` ENUM('pending', 'confirmed', 'cancelled') DEFAULT 'pending' COMMENT '状态',
    `confirmed_at` DATETIME DEFAULT NULL COMMENT '确认时间',
    `confirmed_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '确认人ID',
    `created_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '删除标记',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_record_no` (`record_no`),
    KEY `idx_to_user_id` (`to_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='出库记录表';

-- ============================================
-- 流量池管理模块
-- ============================================

-- 流量池表
DROP TABLE IF EXISTS `traffic_pools`;
CREATE TABLE `traffic_pools` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '流量池ID',
    `name` VARCHAR(100) NOT NULL COMMENT '流量池名称',
    -- 规格信息 (组池条件)
    `carrier` ENUM('cmcc', 'cucc', 'ctcc') NOT NULL COMMENT '运营商',
    `flow_size` BIGINT NOT NULL COMMENT '套餐流量(MB)',
    `period_type` ENUM('monthly', 'yearly') NOT NULL COMMENT '周期类型',
    -- 归属
    `user_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '所属用户ID(NULL=平台池)',
    -- 统计
    `card_count` INT NOT NULL DEFAULT 0 COMMENT '卡片数量',
    `data_total` BIGINT NOT NULL DEFAULT 0 COMMENT '总流量(MB)',
    `data_used` BIGINT NOT NULL DEFAULT 0 COMMENT '已用流量(MB)',
    -- 阈值设置
    `alert_threshold` INT DEFAULT NULL COMMENT '告警阈值百分比',
    `stop_threshold` INT DEFAULT NULL COMMENT '停卡阈值百分比',
    -- 状态
    `status` ENUM('enable', 'disable') NOT NULL DEFAULT 'enable' COMMENT '状态',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `created_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '删除标记',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_carrier` (`carrier`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='流量池表';

-- 流量池卡片变动日志表
DROP TABLE IF EXISTS `pool_card_logs`;
CREATE TABLE `pool_card_logs` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
    `pool_id` BIGINT UNSIGNED NOT NULL COMMENT '流量池ID',
    `card_id` BIGINT UNSIGNED NOT NULL COMMENT '卡片ID',
    `iccid` VARCHAR(30) NOT NULL COMMENT 'ICCID',
    `action` VARCHAR(20) NOT NULL COMMENT '操作: add/remove',
    `operator_id` BIGINT UNSIGNED NOT NULL COMMENT '操作人ID',
    `remark` VARCHAR(200) DEFAULT NULL COMMENT '备注',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '删除标记',
    PRIMARY KEY (`id`),
    KEY `idx_pool_id` (`pool_id`),
    KEY `idx_card_id` (`card_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='流量池卡片变动日志表';

-- ============================================
-- 停卡策略管理模块
-- ============================================

-- 停卡策略表
DROP TABLE IF EXISTS `suspend_policies`;
CREATE TABLE `suspend_policies` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '策略ID',
    `name` VARCHAR(100) NOT NULL COMMENT '策略名称',
    `description` VARCHAR(500) DEFAULT NULL COMMENT '策略描述',
    `policy_type` VARCHAR(20) NOT NULL COMMENT '策略类型: expired/pool_exceed/card_exceed',
    -- 阈值设置
    `warning_threshold` INT DEFAULT 80 COMMENT '警告阈值%',
    `critical_threshold` INT DEFAULT 90 COMMENT '紧急阈值%',
    `stop_threshold` INT DEFAULT 100 COMMENT '停卡阈值%',
    -- 作用范围
    `user_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '指定用户ID(NULL=全局)',
    `pool_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '指定流量池ID(NULL=全部)',
    -- 自动执行
    `auto_suspend` TINYINT NOT NULL DEFAULT 1 COMMENT '是否自动停卡',
    `auto_resume` TINYINT NOT NULL DEFAULT 0 COMMENT '是否自动复机',
    -- 通知设置
    `notify_warning` TINYINT NOT NULL DEFAULT 1 COMMENT '警告时通知',
    `notify_critical` TINYINT NOT NULL DEFAULT 1 COMMENT '紧急时通知',
    `notify_suspend` TINYINT NOT NULL DEFAULT 1 COMMENT '停卡时通知',
    -- 状态
    `is_enabled` TINYINT NOT NULL DEFAULT 1 COMMENT '是否启用',
    `created_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '删除标记',
    PRIMARY KEY (`id`),
    KEY `idx_policy_type` (`policy_type`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_pool_id` (`pool_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='停卡策略表';

-- 停卡/复机记录表
DROP TABLE IF EXISTS `suspend_logs`;
CREATE TABLE `suspend_logs` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
    `card_id` BIGINT UNSIGNED NOT NULL COMMENT '卡片ID',
    `iccid` VARCHAR(30) NOT NULL COMMENT 'ICCID',
    `action` ENUM('suspend', 'resume') NOT NULL COMMENT '操作类型',
    `suspend_type` VARCHAR(20) NOT NULL COMMENT '停卡类型: manual/expired/pool_exceed/card_exceed',
    `policy_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '触发策略ID',
    `pool_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '关联流量池ID',
    `reason` VARCHAR(500) DEFAULT NULL COMMENT '原因说明',
    `api_called` TINYINT NOT NULL DEFAULT 0 COMMENT '是否调用供应商API',
    `api_result` TEXT COMMENT 'API调用结果',
    `operator_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '操作人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '删除标记',
    PRIMARY KEY (`id`),
    KEY `idx_card_id` (`card_id`),
    KEY `idx_action` (`action`),
    KEY `idx_suspend_type` (`suspend_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='停卡/复机记录表';

-- 告警记录表
DROP TABLE IF EXISTS `alert_logs`;
CREATE TABLE `alert_logs` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
    `target_type` ENUM('card', 'pool') NOT NULL COMMENT '目标类型',
    `target_id` BIGINT UNSIGNED NOT NULL COMMENT '目标ID',
    `target_name` VARCHAR(100) DEFAULT NULL COMMENT '目标名称/ICCID',
    `alert_level` ENUM('warning', 'critical', 'exceed') NOT NULL COMMENT '告警级别',
    `usage_percent` INT NOT NULL COMMENT '当前用量百分比',
    `threshold` INT NOT NULL COMMENT '触发阈值',
    `policy_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '触发策略ID',
    `user_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '所属用户ID',
    `notified` TINYINT NOT NULL DEFAULT 0 COMMENT '是否已通知',
    `notified_at` DATETIME DEFAULT NULL COMMENT '通知时间',
    `handled` TINYINT NOT NULL DEFAULT 0 COMMENT '是否已处理',
    `handled_at` DATETIME DEFAULT NULL COMMENT '处理时间',
    `handled_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '处理人ID',
    `handle_remark` VARCHAR(500) DEFAULT NULL COMMENT '处理备注',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '删除标记',
    PRIMARY KEY (`id`),
    KEY `idx_target` (`target_type`, `target_id`),
    KEY `idx_alert_level` (`alert_level`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_handled` (`handled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='告警记录表';

-- ============================================
-- 数据同步管理模块
-- ============================================

-- 同步日志表
DROP TABLE IF EXISTS `sync_logs`;
CREATE TABLE `sync_logs` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '日志ID',
    `sync_no` VARCHAR(50) NOT NULL COMMENT '同步单号',
    `sync_type` ENUM('usage', 'lifecycle', 'status', 'single_card') NOT NULL COMMENT '同步类型: usage=流量用量, lifecycle=生命周期, status=状态, single_card=单卡',
    -- 同步范围
    `supplier_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '供应商ID',
    `card_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '卡片ID(单卡同步)',
    `iccid` VARCHAR(30) DEFAULT NULL COMMENT 'ICCID(单卡同步)',
    -- 同步统计
    `total_count` INT NOT NULL DEFAULT 0 COMMENT '总数',
    `success_count` INT NOT NULL DEFAULT 0 COMMENT '成功数',
    `fail_count` INT NOT NULL DEFAULT 0 COMMENT '失败数',
    -- 同步结果
    `status` ENUM('pending', 'running', 'success', 'failed', 'partial') NOT NULL DEFAULT 'pending' COMMENT '状态',
    `error_message` TEXT COMMENT '错误信息',
    `sync_data` JSON COMMENT '同步数据详情',
    -- 执行时间
    `started_at` DATETIME DEFAULT NULL COMMENT '开始时间',
    `finished_at` DATETIME DEFAULT NULL COMMENT '完成时间',
    `duration` INT DEFAULT NULL COMMENT '耗时(秒)',
    -- 操作人
    `triggered_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '触发人ID',
    `trigger_type` VARCHAR(20) DEFAULT NULL COMMENT '触发方式: manual=手动, auto=自动',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '删除标记',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_sync_no` (`sync_no`),
    KEY `idx_sync_type` (`sync_type`),
    KEY `idx_supplier_id` (`supplier_id`),
    KEY `idx_card_id` (`card_id`),
    KEY `idx_status` (`status`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='同步日志表';

-- 同步任务表 (定时任务配置)
DROP TABLE IF EXISTS `sync_tasks`;
CREATE TABLE `sync_tasks` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '任务ID',
    `task_name` VARCHAR(100) NOT NULL COMMENT '任务名称',
    `sync_type` ENUM('usage', 'lifecycle', 'status', 'single_card') NOT NULL COMMENT '同步类型',
    -- 任务配置
    `supplier_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '供应商ID(NULL=全部)',
    `cron_expression` VARCHAR(100) DEFAULT NULL COMMENT 'Cron表达式',
    -- 任务状态
    `is_enabled` TINYINT NOT NULL DEFAULT 1 COMMENT '是否启用',
    `last_run_at` DATETIME DEFAULT NULL COMMENT '上次运行时间',
    `next_run_at` DATETIME DEFAULT NULL COMMENT '下次运行时间',
    `last_status` ENUM('pending', 'running', 'success', 'failed', 'partial') DEFAULT NULL COMMENT '上次状态',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `created_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '删除标记',
    PRIMARY KEY (`id`),
    KEY `idx_sync_type` (`sync_type`),
    KEY `idx_is_enabled` (`is_enabled`),
    KEY `idx_next_run_at` (`next_run_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='同步任务表';

-- ============================================
-- 初始化示例数据
-- ============================================

-- 供应商示例数据
INSERT INTO `suppliers` (`id`, `name`, `code`, `type`, `contact_name`, `contact_phone`, `remark`) VALUES
(1, '中国移动物联网', 'CMCC_IOT', 'cmcc', '张经理', '13800138000', '中国移动官方合作渠道'),
(2, '中国联通物联网', 'CUCC_IOT', 'cucc', '李经理', '13900139000', '中国联通官方合作渠道'),
(3, '中国电信物联网', 'CTCC_IOT', 'ctcc', '王经理', '13700137000', '中国电信官方合作渠道');

-- 底层套餐示例数据 (规格: 运营商+流量+周期)
INSERT INTO `supplier_packages` (`id`, `supplier_id`, `name`, `code`, `carrier`, `flow_size`, `period_type`, `effective_days`, `price_cost`, `remark`) VALUES
-- 移动月包
(1, 1, '移动1G/月', 'CMCC_1G_M', 'cmcc', 1024, 'monthly', 30, 10.00, '移动1GB月套餐'),
(2, 1, '移动3G/月', 'CMCC_3G_M', 'cmcc', 3072, 'monthly', 30, 25.00, '移动3GB月套餐'),
(3, 1, '移动5G/月', 'CMCC_5G_M', 'cmcc', 5120, 'monthly', 30, 35.00, '移动5GB月套餐'),
-- 移动年包 (360天)
(4, 1, '移动1G/年', 'CMCC_1G_Y', 'cmcc', 1024, 'yearly', 360, 80.00, '移动1GB年套餐(360天)'),
(5, 1, '移动5G/年', 'CMCC_5G_Y', 'cmcc', 5120, 'yearly', 360, 300.00, '移动5GB年套餐(360天)'),
-- 联通月包
(6, 2, '联通1G/月', 'CUCC_1G_M', 'cucc', 1024, 'monthly', 30, 9.00, '联通1GB月套餐'),
(7, 2, '联通3G/月', 'CUCC_3G_M', 'cucc', 3072, 'monthly', 30, 22.00, '联通3GB月套餐'),
-- 电信月包
(8, 3, '电信1G/月', 'CTCC_1G_M', 'ctcc', 1024, 'monthly', 30, 11.00, '电信1GB月套餐');

-- 销售套餐示例数据 (平台公开套餐)
INSERT INTO `sale_packages` (`id`, `user_id`, `base_package_id`, `name`, `code`, `carrier`, `flow_size`, `period_type`, `effective_days`, `price_cost`, `price_sale`, `is_public`, `sort_order`, `remark`) VALUES
(1, NULL, 1, '标准移动1G/月', 'SALE_CMCC_1G_M', 'cmcc', 1024, 'monthly', 30, 10.00, 15.00, 1, 1, '销售用移动1GB月套餐'),
(2, NULL, 2, '标准移动3G/月', 'SALE_CMCC_3G_M', 'cmcc', 3072, 'monthly', 30, 25.00, 35.00, 1, 2, '销售用移动3GB月套餐'),
(3, NULL, 4, '标准移动1G/年', 'SALE_CMCC_1G_Y', 'cmcc', 1024, 'yearly', 360, 80.00, 120.00, 1, 3, '销售用移动1GB年套餐'),
(4, NULL, 6, '标准联通1G/月', 'SALE_CUCC_1G_M', 'cucc', 1024, 'monthly', 30, 9.00, 14.00, 1, 4, '销售用联通1GB月套餐');

-- 测试用户 (代理商)
INSERT INTO `sys_users` (`id`, `parent_id`, `user_level`, `name`, `account`, `password`, `phone`, `status`, `remark`)
VALUES (2, 1, 2, '测试代理商', 'agent01', '$2b$12$SrdjFNBnLZwVWcK64vvKFe.rIdM1rOUG3herNDGsIeFVkgrFGlrDW', '13800138001', 'enable', '测试代理商账号');

-- 测试子用户
INSERT INTO `sys_users` (`id`, `parent_id`, `user_level`, `name`, `account`, `password`, `phone`, `status`, `remark`)
VALUES (3, 2, 3, '测试子用户', 'subuser01', '$2b$12$SrdjFNBnLZwVWcK64vvKFe.rIdM1rOUG3herNDGsIeFVkgrFGlrDW', '13800138002', 'enable', '测试子用户账号');

-- 物联网卡示例数据 (分配给测试代理商)
INSERT INTO `iot_cards` (`iccid`, `imsi`, `msisdn`, `user_id`, `supplier_id`, `sale_package_id`, `carrier`, `flow_size`, `period_type`, `test_expire_date`, `silent_expire_date`, `activated_at`, `expired_at`, `data_used`, `data_total`, `status`, `remark`, `stock_in_at`, `stock_out_at`) VALUES
-- 已激活的卡
('89860012345678901234', '460001234567890', '14712345678', 2, 1, 1, 'cmcc', 1024, 'monthly', '2026-01-15', '2026-02-15', '2026-01-10', '2026-02-10', 512, 1024, 'activated', '设备A-路灯监控', '2026-01-01 10:00:00', '2026-01-05 10:00:00'),
('89860012345678901235', '460001234567891', '14712345679', 2, 1, 1, 'cmcc', 1024, 'monthly', '2026-01-15', '2026-02-15', '2026-01-10', '2026-02-10', 800, 1024, 'activated', '设备B-水表监测', '2026-01-01 10:00:00', '2026-01-05 10:00:00'),
('89860012345678901236', '460001234567892', '14712345680', 2, 1, 2, 'cmcc', 3072, 'monthly', '2026-01-20', '2026-03-20', '2026-01-15', '2026-02-15', 1500, 3072, 'activated', '设备C-摄像头', '2026-01-01 10:00:00', '2026-01-05 10:00:00'),
-- 沉默期的卡
('89860012345678901237', '460001234567893', '14712345681', 2, 1, 1, 'cmcc', 1024, 'monthly', '2026-01-31', '2026-04-30', NULL, NULL, 0, 1024, 'silent', '待分配设备', '2026-01-10 10:00:00', '2026-01-12 10:00:00'),
('89860012345678901238', '460001234567894', '14712345682', 2, 2, 4, 'cucc', 1024, 'monthly', '2026-01-31', '2026-04-30', NULL, NULL, 0, 1024, 'silent', NULL, '2026-01-10 10:00:00', '2026-01-12 10:00:00'),
-- 库存卡 (未出库)
('89860012345678901239', '460001234567895', '14712345683', NULL, 1, NULL, 'cmcc', 1024, 'monthly', '2026-01-31', '2026-04-30', NULL, NULL, 0, 1024, 'stock', NULL, '2026-01-14 10:00:00', NULL),
('89860012345678901240', '460001234567896', '14712345684', NULL, 3, NULL, 'ctcc', 1024, 'monthly', '2026-01-31', '2026-05-31', NULL, NULL, 0, 1024, 'stock', NULL, '2026-01-14 10:00:00', NULL),
-- 分配给子用户的卡
('89860012345678901241', '460001234567897', '14712345685', 3, 1, 1, 'cmcc', 1024, 'monthly', '2026-01-15', '2026-02-15', '2026-01-10', '2026-02-10', 256, 1024, 'activated', '子用户设备', '2026-01-01 10:00:00', '2026-01-05 10:00:00'),
-- 年包卡
('89860012345678901242', '460001234567898', '14712345686', 2, 1, 3, 'cmcc', 1024, 'yearly', '2026-01-31', '2026-04-30', '2026-01-01', '2026-12-27', 100, 1024, 'activated', '年包设备-智能电表', '2026-01-01 10:00:00', '2026-01-05 10:00:00');

-- ============================================
-- 系统配置初始化
-- ============================================

INSERT INTO `sys_configs` (`config_key`, `config_value`, `config_type`, `description`, `is_public`) VALUES
-- 告警规则配置
('alert_warning_threshold', '80', 'number', '流量告警阈值(百分比)', 0),
('alert_critical_threshold', '90', 'number', '流量紧急阈值(百分比)', 0),
('alert_stop_threshold', '100', 'number', '流量停卡阈值(百分比)', 0),
('alert_expired_days', '7', 'number', '到期预警天数', 0),
('alert_auto_suspend', 'true', 'boolean', '超限自动停卡', 0),
('alert_auto_notify', 'true', 'boolean', '告警自动通知', 0),
-- 系统参数配置
('system_name', '物联网卡管理平台', 'string', '系统名称', 1),
('system_logo', '/logo.png', 'string', '系统Logo', 1),
('system_copyright', 'Copyright © 2026', 'string', '版权信息', 1),
('page_size_default', '20', 'number', '默认分页大小', 0),
('session_timeout', '7200', 'number', '会话超时(秒)', 0),
('password_min_length', '6', 'number', '密码最小长度', 0),
-- 通知配置
('notify_sms_enabled', 'false', 'boolean', '启用短信通知', 0),
('notify_email_enabled', 'false', 'boolean', '启用邮件通知', 0),
('notify_wechat_enabled', 'false', 'boolean', '启用微信通知', 0),
('notify_webhook_enabled', 'false', 'boolean', '启用Webhook通知', 0);

-- 通知模板初始化
INSERT INTO `sys_notify_templates` (`code`, `name`, `type`, `title`, `content`, `variables`, `is_enabled`, `remark`) VALUES
('alert_warning', '流量预警通知', 'sms', '流量预警', '【物联网卡】您的卡片{iccid}流量已使用{usage_percent}%，请注意监控。', '["iccid", "usage_percent", "data_used", "data_total"]', 1, '流量达到告警阈值时发送'),
('alert_critical', '流量紧急通知', 'sms', '流量紧急', '【物联网卡】您的卡片{iccid}流量已使用{usage_percent}%，即将停卡，请及时处理！', '["iccid", "usage_percent", "data_used", "data_total"]', 1, '流量达到紧急阈值时发送'),
('alert_suspend', '停卡通知', 'sms', '卡片停机通知', '【物联网卡】您的卡片{iccid}已被停机，原因：{reason}。', '["iccid", "reason", "suspend_time"]', 1, '卡片停机时发送'),
('alert_resume', '复机通知', 'sms', '卡片复机通知', '【物联网卡】您的卡片{iccid}已恢复正常使用。', '["iccid", "resume_time"]', 1, '卡片复机时发送'),
('alert_expired', '到期预警通知', 'sms', '卡片到期预警', '【物联网卡】您的卡片{iccid}将于{expire_date}到期，请及时续费。', '["iccid", "expire_date", "days_left"]', 1, '卡片即将到期时发送'),
('pool_warning', '流量池预警', 'sms', '流量池预警', '【物联网卡】流量池"{pool_name}"用量已达{usage_percent}%，请注意监控。', '["pool_name", "usage_percent", "data_used", "data_total"]', 1, '流量池达到告警阈值时发送'),
('pool_suspend', '流量池停卡通知', 'sms', '流量池停卡', '【物联网卡】流量池"{pool_name}"已超限，池内所有卡片已停机。', '["pool_name", "card_count"]', 1, '流量池超限停卡时发送');

COMMIT;
