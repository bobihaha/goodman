-- 修复 stock_in_record_cards, stock_out_record_cards, stock_recycle_record_cards 表
-- 添加缺失的 is_deleted 字段

-- 1. 为 stock_in_record_cards 添加 is_deleted 字段
ALTER TABLE stock_in_record_cards 
ADD COLUMN is_deleted TINYINT DEFAULT 0 COMMENT '删除标记：0=未删除，1=已删除';

-- 2. 为 stock_out_record_cards 添加 is_deleted 字段
ALTER TABLE stock_out_record_cards 
ADD COLUMN is_deleted TINYINT DEFAULT 0 COMMENT '删除标记：0=未删除，1=已删除';

-- 3. 为 stock_recycle_record_cards 添加 is_deleted 字段
ALTER TABLE stock_recycle_record_cards 
ADD COLUMN is_deleted TINYINT DEFAULT 0 COMMENT '删除标记：0=未删除，1=已删除';

-- 验证修改
SHOW COLUMNS FROM stock_in_record_cards;
SHOW COLUMNS FROM stock_out_record_cards;
SHOW COLUMNS FROM stock_recycle_record_cards;


