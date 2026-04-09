-- 变更目标：为卡片列表和备注关联查询补充复合索引
-- 风险级别：低
-- 执行前提：低峰期执行，先在预发库验证

SET @schema_name = DATABASE();

SET @sql = IF(
    (
        SELECT COUNT(1)
        FROM information_schema.statistics
        WHERE table_schema = @schema_name
          AND table_name = 'iot_cards'
          AND index_name = 'idx_iot_cards_user_deleted_id'
    ) = 0,
    'CREATE INDEX idx_iot_cards_user_deleted_id ON iot_cards (user_id, is_deleted, id)',
    'SELECT ''idx_iot_cards_user_deleted_id exists'''
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    (
        SELECT COUNT(1)
        FROM information_schema.statistics
        WHERE table_schema = @schema_name
          AND table_name = 'iot_cards'
          AND index_name = 'idx_iot_cards_user_status_deleted_id'
    ) = 0,
    'CREATE INDEX idx_iot_cards_user_status_deleted_id ON iot_cards (user_id, status, is_deleted, id)',
    'SELECT ''idx_iot_cards_user_status_deleted_id exists'''
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    (
        SELECT COUNT(1)
        FROM information_schema.statistics
        WHERE table_schema = @schema_name
          AND table_name = 'iot_cards'
          AND index_name = 'idx_iot_cards_user_project_deleted_id'
    ) = 0,
    'CREATE INDEX idx_iot_cards_user_project_deleted_id ON iot_cards (user_id, project_id, is_deleted, id)',
    'SELECT ''idx_iot_cards_user_project_deleted_id exists'''
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    (
        SELECT COUNT(1)
        FROM information_schema.statistics
        WHERE table_schema = @schema_name
          AND table_name = 'iot_cards'
          AND index_name = 'idx_iot_cards_user_pool_deleted_id'
    ) = 0,
    'CREATE INDEX idx_iot_cards_user_pool_deleted_id ON iot_cards (user_id, pool_id, is_deleted, id)',
    'SELECT ''idx_iot_cards_user_pool_deleted_id exists'''
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    (
        SELECT COUNT(1)
        FROM information_schema.statistics
        WHERE table_schema = @schema_name
          AND table_name = 'card_user_remarks'
          AND index_name = 'idx_card_user_remarks_user_deleted_card'
    ) = 0,
    'CREATE INDEX idx_card_user_remarks_user_deleted_card ON card_user_remarks (user_id, is_deleted, card_id)',
    'SELECT ''idx_card_user_remarks_user_deleted_card exists'''
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
