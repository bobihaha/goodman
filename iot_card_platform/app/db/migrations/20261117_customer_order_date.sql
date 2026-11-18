-- 历史记录保留空日期，避免按当前卡归属或操作时间误还原。
-- 仅限制本次连接的元数据锁等待，超时由执行方退出并检查当前结构。
SET @previous_order_lock_timeout = @@SESSION.lock_wait_timeout;
SET SESSION lock_wait_timeout = 5;

SET @order_date_sql = IF(
    EXISTS (SELECT 1 FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = 'stock_out_records' AND column_name = 'stock_out_date'),
    'SELECT 1',
    'ALTER TABLE stock_out_records ADD COLUMN stock_out_date DATE NULL COMMENT ''客户订单日期（手填出库日期）'', ALGORITHM=INSTANT'
);
PREPARE order_stmt FROM @order_date_sql;
EXECUTE order_stmt;
DEALLOCATE PREPARE order_stmt;

SET @order_index_sql = IF(
    EXISTS (SELECT 1 FROM information_schema.statistics
            WHERE table_schema = DATABASE() AND table_name = 'stock_out_records' AND index_name = 'idx_customer_order_date'),
    'SELECT 1',
    'ALTER TABLE stock_out_records ADD INDEX idx_customer_order_date (to_user_id, stock_out_date, id), ALGORITHM=INPLACE, LOCK=NONE'
);
PREPARE order_stmt FROM @order_index_sql;
EXECUTE order_stmt;
DEALLOCATE PREPARE order_stmt;

SET SESSION lock_wait_timeout = @previous_order_lock_timeout;
