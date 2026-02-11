-- 流量池模块数据库字段补充
-- 执行日期：2026-02-10

-- 1. 流量池表添加字段
ALTER TABLE traffic_pools
  ADD COLUMN sale_package_id BIGINT COMMENT '销售套餐ID（组池依据）' AFTER period_type,
  ADD COLUMN last_sync_at DATETIME COMMENT '最近同步时间' AFTER remark,
  ADD COLUMN package_flow BIGINT DEFAULT 0 COMMENT '套餐流量(MB)' AFTER data_used,
  ADD COLUMN addon_flow BIGINT DEFAULT 0 COMMENT '叠加流量包(MB)' AFTER package_flow,
  ADD INDEX idx_sale_package_id (sale_package_id);

-- 2. 卡片表添加字段
ALTER TABLE iot_cards
  ADD COLUMN network_status ENUM('open', 'close') DEFAULT 'open' COMMENT '网络状态' AFTER status,
  ADD COLUMN is_pool_card BOOLEAN DEFAULT FALSE COMMENT '是否为流量池卡' AFTER is_pool_member;

-- 3. 添加唯一索引防止重复创建流量池（MySQL不支持部分索引，改用普通唯一索引）
-- 注意：这个索引会包含 is_deleted 字段，需要在应用层确保不创建重复的流量池
CREATE UNIQUE INDEX idx_pool_unique 
ON traffic_pools(user_id, sale_package_id, is_deleted);

-- 4. 为现有数据设置默认值
UPDATE traffic_pools SET package_flow = data_total WHERE package_flow = 0;
UPDATE traffic_pools SET addon_flow = 0 WHERE addon_flow IS NULL;
UPDATE iot_cards SET network_status = 'open' WHERE network_status IS NULL;
UPDATE iot_cards SET is_pool_card = FALSE WHERE is_pool_card IS NULL;

-- 5. 查看修改结果
DESCRIBE traffic_pools;
DESCRIBE iot_cards;

