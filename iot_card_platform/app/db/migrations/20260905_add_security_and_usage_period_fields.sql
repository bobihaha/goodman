-- 变更目标：支持令牌主动失效，并分离供应商用量月份与平台抓取时间
-- 执行前提：确认以下字段尚未创建；执行前完成数据库备份

ALTER TABLE `sys_users`
    ADD COLUMN `token_version` INT NOT NULL DEFAULT 0 COMMENT '令牌版本，改密或退出时递增' AFTER `password`;

ALTER TABLE `iot_cards`
    CHANGE COLUMN `data_sync_at` `data_sync_at` DATETIME DEFAULT NULL COMMENT '平台抓取流量时间',
    ADD COLUMN `data_source_at` DATETIME DEFAULT NULL COMMENT '供应商用量快照时间' AFTER `data_sync_at`,
    ADD COLUMN `data_usage_month` VARCHAR(7) DEFAULT NULL COMMENT '当前用量所属月份(YYYY-MM)' AFTER `data_source_at`,
    ADD KEY `idx_iot_cards_data_usage_month` (`data_usage_month`);

SHOW COLUMNS FROM `sys_users` WHERE Field = 'token_version';
SHOW COLUMNS FROM `iot_cards` WHERE Field IN ('data_source_at', 'data_usage_month');
