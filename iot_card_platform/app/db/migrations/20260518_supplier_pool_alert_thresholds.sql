SET NAMES utf8mb4;

ALTER TABLE `supplier_traffic_pools`
    ADD COLUMN `alert_thresholds` VARCHAR(100) NOT NULL DEFAULT '60,80,100' COMMENT '邮件提醒阈值列表(%)' AFTER `alert_threshold`,
    ADD COLUMN `last_alert_threshold` INT DEFAULT NULL COMMENT '最近提醒阈值(%)' AFTER `last_alert_usage_percent`;

UPDATE `supplier_traffic_pools`
SET `alert_thresholds` = CASE
    WHEN `alert_threshold` IS NOT NULL THEN CAST(`alert_threshold` AS CHAR)
    ELSE '60,80,100'
END
WHERE `alert_thresholds` IS NULL OR `alert_thresholds` = '';

UPDATE `sys_menus`
SET `name` = '供应商流量池管理'
WHERE `code` = 'supplier_traffic_pools';
