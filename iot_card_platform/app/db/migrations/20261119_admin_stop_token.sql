-- NULL 表示未强制锁定；旧卡默认不锁定。
ALTER TABLE iot_cards ADD COLUMN admin_stop_token VARCHAR(32) NULL;
