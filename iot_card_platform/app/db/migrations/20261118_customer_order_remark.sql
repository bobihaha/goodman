-- 独立保存客户订单备注，兼容旧应用和后台出库备注。
SET @previous_order_lock_timeout = @@SESSION.lock_wait_timeout;
SET SESSION lock_wait_timeout = 5;
SET @order_remark_sql = IF(
    EXISTS (SELECT 1 FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = 'stock_out_records' AND column_name = 'customer_remark'),
    'SELECT 1',
    'ALTER TABLE stock_out_records ADD COLUMN customer_remark VARCHAR(500) NULL COMMENT ''客户订单备注'', ALGORITHM=INSTANT'
);
PREPARE order_stmt FROM @order_remark_sql;
EXECUTE order_stmt;
DEALLOCATE PREPARE order_stmt;
SET SESSION lock_wait_timeout = @previous_order_lock_timeout;
