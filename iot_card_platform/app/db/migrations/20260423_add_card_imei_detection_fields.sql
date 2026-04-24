ALTER TABLE `iot_cards`
    ADD COLUMN `latest_imei` VARCHAR(32) NULL COMMENT '最近一次获取的IMEI' AFTER `data_sync_at`,
    ADD COLUMN `previous_imei` VARCHAR(32) NULL COMMENT '上一次获取的IMEI' AFTER `latest_imei`,
    ADD COLUMN `imei_device_name` VARCHAR(100) NULL COMMENT '最近一次IMEI对应设备名称' AFTER `previous_imei`,
    ADD COLUMN `imei_checked_at` DATETIME NULL COMMENT 'IMEI检测时间' AFTER `imei_device_name`,
    ADD COLUMN `imei_separation_detected` TINYINT NOT NULL DEFAULT 0 COMMENT '是否检测到机卡分离: 0=否,1=是' AFTER `imei_checked_at`;

ALTER TABLE `iot_cards`
    MODIFY COLUMN `suspend_type` ENUM('none', 'manual', 'expired', 'pool_exceed', 'card_exceed', 'device_separation')
    NOT NULL DEFAULT 'none' COMMENT '停卡类型';
