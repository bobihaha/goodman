ALTER TABLE `sys_users`
ADD COLUMN `h5_enabled` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否启用H5: 0=否, 1=是' AFTER `remark`,
ADD COLUMN `h5_slug` VARCHAR(32) NULL COMMENT 'H5专属访问标识' AFTER `h5_enabled`,
ADD COLUMN `h5_title` VARCHAR(100) NULL COMMENT 'H5标题' AFTER `h5_slug`,
ADD COLUMN `h5_logo` VARCHAR(255) NULL COMMENT 'H5 Logo' AFTER `h5_title`,
ADD COLUMN `h5_banner` VARCHAR(255) NULL COMMENT 'H5横幅图' AFTER `h5_logo`,
ADD COLUMN `h5_notice` VARCHAR(1000) NULL COMMENT 'H5公告文案' AFTER `h5_banner`,
ADD COLUMN `h5_contact_phone` VARCHAR(30) NULL COMMENT 'H5客服电话' AFTER `h5_notice`,
ADD COLUMN `h5_contact_wechat` VARCHAR(50) NULL COMMENT 'H5客服微信' AFTER `h5_contact_phone`,
ADD COLUMN `h5_theme` JSON NULL COMMENT 'H5主题配置' AFTER `h5_contact_wechat`,
ADD COLUMN `h5_allow_suspend` TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'H5是否允许停机: 0=否, 1=是' AFTER `h5_theme`,
ADD COLUMN `h5_allow_resume` TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'H5是否允许复机: 0=否, 1=是' AFTER `h5_allow_suspend`,
ADD COLUMN `h5_allow_remark` TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'H5是否允许备注: 0=否, 1=是' AFTER `h5_allow_resume`,
ADD COLUMN `h5_require_verify` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'H5是否要求验证码: 0=否, 1=是' AFTER `h5_allow_remark`,
ADD COLUMN `h5_status` VARCHAR(20) NULL DEFAULT 'enabled' COMMENT 'H5状态: enabled/disabled/expired' AFTER `h5_require_verify`,
ADD COLUMN `h5_last_reset_at` DATETIME NULL COMMENT 'H5最近重置时间' AFTER `h5_status`;

ALTER TABLE `sys_users`
ADD UNIQUE KEY `uk_sys_users_h5_slug` (`h5_slug`);

CREATE TABLE IF NOT EXISTS `card_h5_remark_logs` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL COMMENT '二级用户ID',
  `card_id` BIGINT NOT NULL COMMENT '卡片ID',
  `iccid` VARCHAR(30) NOT NULL COMMENT 'ICCID',
  `old_remark` VARCHAR(500) NULL COMMENT '旧备注',
  `new_remark` VARCHAR(500) NULL COMMENT '新备注',
  `source` VARCHAR(20) NOT NULL DEFAULT 'h5' COMMENT '来源',
  `operator_name` VARCHAR(50) NULL COMMENT '操作人姓名',
  `operator_phone` VARCHAR(20) NULL COMMENT '操作人手机号',
  `client_ip` VARCHAR(50) NULL COMMENT '客户端IP',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_card_h5_remark_logs_user_id` (`user_id`),
  KEY `idx_card_h5_remark_logs_card_id` (`card_id`),
  KEY `idx_card_h5_remark_logs_iccid` (`iccid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='H5卡片备注日志';
