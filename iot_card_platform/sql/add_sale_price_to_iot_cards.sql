-- 添加套餐单价字段到 iot_cards 表
-- 用于记录出库时的套餐单价，实现续费价格锁定

-- 1. 添加字段
ALTER TABLE iot_cards
ADD COLUMN sale_price DECIMAL(10, 2) NULL COMMENT '套餐单价(元/周期) - 出库时记录' AFTER sale_package_id;

-- 2. 为已有卡片回填单价（从关联的销售套餐获取）
UPDATE iot_cards ic
INNER JOIN sale_packages sp ON ic.sale_package_id = sp.id
SET ic.sale_price = sp.price_sale
WHERE ic.sale_price IS NULL AND ic.sale_package_id IS NOT NULL;

-- 3. 验证迁移结果
SELECT
    COUNT(*) as total_cards,
    COUNT(sale_price) as has_price,
    COUNT(*) - COUNT(sale_price) as missing_price
FROM iot_cards
WHERE is_deleted = 0;
