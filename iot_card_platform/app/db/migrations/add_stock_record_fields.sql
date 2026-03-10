-- 为出入库记录表添加业务字段
-- 用于支持按卡号查询完整的出入库历史记录

-- 入库记录卡片表
ALTER TABLE stock_in_record_cards ADD COLUMN test_expire_date DATE;
ALTER TABLE stock_in_record_cards ADD COLUMN silent_expire_date DATE;
ALTER TABLE stock_in_record_cards ADD COLUMN supplier_id BIGINT;
ALTER TABLE stock_in_record_cards ADD COLUMN supplier_name VARCHAR(100);
ALTER TABLE stock_in_record_cards ADD COLUMN base_package_id BIGINT;
ALTER TABLE stock_in_record_cards ADD COLUMN base_package_name VARCHAR(200);

-- 出库记录卡片表
ALTER TABLE stock_out_record_cards ADD COLUMN test_expire_date DATE;
ALTER TABLE stock_out_record_cards ADD COLUMN silent_expire_date DATE;
ALTER TABLE stock_out_record_cards ADD COLUMN supplier_id BIGINT;
ALTER TABLE stock_out_record_cards ADD COLUMN supplier_name VARCHAR(100);
ALTER TABLE stock_out_record_cards ADD COLUMN base_package_id BIGINT;
ALTER TABLE stock_out_record_cards ADD COLUMN base_package_name VARCHAR(200);
ALTER TABLE stock_out_record_cards ADD COLUMN sale_package_id BIGINT;
ALTER TABLE stock_out_record_cards ADD COLUMN sale_package_name VARCHAR(200);
ALTER TABLE stock_out_record_cards ADD COLUMN target_user_id BIGINT;
ALTER TABLE stock_out_record_cards ADD COLUMN target_user_name VARCHAR(100);

-- 添加索引加速ICCID查询
CREATE INDEX idx_stock_in_record_card_iccid ON stock_in_record_cards(iccid);
CREATE INDEX idx_stock_out_record_card_iccid ON stock_out_record_cards(iccid);
