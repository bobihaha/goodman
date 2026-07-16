SET @channel_profile_exists = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'channel_customer_relations'
      AND COLUMN_NAME = 'customer_profile'
);
SET @channel_profile_sql = IF(
    @channel_profile_exists = 0,
    'ALTER TABLE `channel_customer_relations` ADD COLUMN `customer_profile` VARCHAR(500) NULL COMMENT ''用户情况：设备、场景、规模'' AFTER `customer_phone`',
    'SELECT 1'
);
PREPARE channel_profile_stmt FROM @channel_profile_sql;
EXECUTE channel_profile_stmt;
DEALLOCATE PREPARE channel_profile_stmt;
