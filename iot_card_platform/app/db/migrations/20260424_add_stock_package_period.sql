-- 为入库批次和入库记录增加“套餐周期数量”字段
-- 用于记录入库时实际选择的套餐周期，方便库存管理和后续出库发货识别

ALTER TABLE purchase_batches
    ADD COLUMN package_period_count INT NULL COMMENT '入库套餐周期数量' AFTER period_type;

ALTER TABLE stock_in_records
    ADD COLUMN package_period_count INT NULL COMMENT '入库套餐周期数量' AFTER silent_expire_date;

-- 用底层套餐默认周期回填历史数据
UPDATE purchase_batches pb
LEFT JOIN supplier_packages sp ON pb.package_id = sp.id
SET pb.package_period_count = CASE
    WHEN pb.period_type = 'monthly' THEN COALESCE(sp.period_months, 1)
    WHEN pb.period_type = 'yearly' THEN COALESCE(NULLIF(sp.period_days DIV 360, 0), 1)
    ELSE 1
END
WHERE pb.package_period_count IS NULL;

UPDATE stock_in_records sir
LEFT JOIN purchase_batches pb ON sir.batch_id = pb.id
LEFT JOIN supplier_packages sp ON sir.package_id = sp.id
SET sir.package_period_count = COALESCE(
    pb.package_period_count,
    CASE
        WHEN sp.period_type = 'monthly' THEN COALESCE(sp.period_months, 1)
        WHEN sp.period_type = 'yearly' THEN COALESCE(NULLIF(sp.period_days DIV 360, 0), 1)
        ELSE 1
    END
)
WHERE sir.package_period_count IS NULL;
