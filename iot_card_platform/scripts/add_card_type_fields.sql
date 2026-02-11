-- 添加卡片类型和本月用量字段
-- 执行时间: 2026-02-11

USE iot_card_platform;

-- 1. 添加卡片类型字段
ALTER TABLE `iot_cards` 
ADD COLUMN `card_type` ENUM('single', 'pool') NOT NULL DEFAULT 'single' 
COMMENT '卡片类型: single=单卡(达量停机), pool=流量池卡' 
AFTER `period_type`;

-- 2. 添加本月用量字段
ALTER TABLE `iot_cards` 
ADD COLUMN `data_used_month` BIGINT NOT NULL DEFAULT 0 
COMMENT '本月已用流量(MB)' 
AFTER `data_total`;

-- 3. 为现有数据设置默认值
-- 如果卡片在流量池中，设置为流量池卡，否则为单卡
UPDATE `iot_cards` 
SET `card_type` = CASE 
    WHEN `is_pool_member` = 1 THEN 'pool' 
    ELSE 'single' 
END;

-- 4. 初始化本月用量（假设当前已用流量就是本月用量）
UPDATE `iot_cards` 
SET `data_used_month` = `data_used`;

-- 验证
SELECT 
    card_type,
    COUNT(*) as count
FROM iot_cards
GROUP BY card_type;

SELECT 
    '字段添加完成' as status,
    COUNT(*) as total_cards,
    SUM(CASE WHEN card_type = 'single' THEN 1 ELSE 0 END) as single_cards,
    SUM(CASE WHEN card_type = 'pool' THEN 1 ELSE 0 END) as pool_cards
FROM iot_cards;

