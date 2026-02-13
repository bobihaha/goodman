-- 添加 period_count 字段到 iot_cards 表
-- 用于存储套餐周期数量（月包：月数，年包：年数）

-- 添加 period_count 字段
ALTER TABLE iot_cards 
ADD COLUMN period_count INT DEFAULT 1 COMMENT '套餐周期数量: 月包=月数(3/6/12等), 年包=年数(1/2/3等)' 
AFTER period_type;

-- 添加 stock_out_date 字段（出库日期）
ALTER TABLE iot_cards 
ADD COLUMN stock_out_date DATE NULL COMMENT '出库日期' 
AFTER stock_out_at;



-- 添加 period_count 字段
ALTER TABLE iot_cards 
ADD COLUMN period_count INT DEFAULT 1 COMMENT '套餐周期数量: 月包=月数(3/6/12等), 年包=年数(1/2/3等)' 
AFTER period_type;

-- 添加 stock_out_date 字段（出库日期）
ALTER TABLE iot_cards 
ADD COLUMN stock_out_date DATE NULL COMMENT '出库日期' 
AFTER stock_out_at;



-- 添加 period_count 字段
ALTER TABLE iot_cards 
ADD COLUMN period_count INT DEFAULT 1 COMMENT '套餐周期数量: 月包=月数(3/6/12等), 年包=年数(1/2/3等)' 
AFTER period_type;

-- 添加 stock_out_date 字段（出库日期）
ALTER TABLE iot_cards 
ADD COLUMN stock_out_date DATE NULL COMMENT '出库日期' 
AFTER stock_out_at;



-- 添加 period_count 字段
ALTER TABLE iot_cards 
ADD COLUMN period_count INT DEFAULT 1 COMMENT '套餐周期数量: 月包=月数(3/6/12等), 年包=年数(1/2/3等)' 
AFTER period_type;

-- 添加 stock_out_date 字段（出库日期）
ALTER TABLE iot_cards 
ADD COLUMN stock_out_date DATE NULL COMMENT '出库日期' 
AFTER stock_out_at;



-- 添加 period_count 字段
ALTER TABLE iot_cards 
ADD COLUMN period_count INT DEFAULT 1 COMMENT '套餐周期数量: 月包=月数(3/6/12等), 年包=年数(1/2/3等)' 
AFTER period_type;

-- 添加 stock_out_date 字段（出库日期）
ALTER TABLE iot_cards 
ADD COLUMN stock_out_date DATE NULL COMMENT '出库日期' 
AFTER stock_out_at;



-- 添加 period_count 字段
ALTER TABLE iot_cards 
ADD COLUMN period_count INT DEFAULT 1 COMMENT '套餐周期数量: 月包=月数(3/6/12等), 年包=年数(1/2/3等)' 
AFTER period_type;

-- 添加 stock_out_date 字段（出库日期）
ALTER TABLE iot_cards 
ADD COLUMN stock_out_date DATE NULL COMMENT '出库日期' 
AFTER stock_out_at;



-- 添加 period_count 字段
ALTER TABLE iot_cards 
ADD COLUMN period_count INT DEFAULT 1 COMMENT '套餐周期数量: 月包=月数(3/6/12等), 年包=年数(1/2/3等)' 
AFTER period_type;

-- 添加 stock_out_date 字段（出库日期）
ALTER TABLE iot_cards 
ADD COLUMN stock_out_date DATE NULL COMMENT '出库日期' 
AFTER stock_out_at;



-- 添加 period_count 字段
ALTER TABLE iot_cards 
ADD COLUMN period_count INT DEFAULT 1 COMMENT '套餐周期数量: 月包=月数(3/6/12等), 年包=年数(1/2/3等)' 
AFTER period_type;

-- 添加 stock_out_date 字段（出库日期）
ALTER TABLE iot_cards 
ADD COLUMN stock_out_date DATE NULL COMMENT '出库日期' 
AFTER stock_out_at;

