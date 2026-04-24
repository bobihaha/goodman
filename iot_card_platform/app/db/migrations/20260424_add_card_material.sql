-- 新增卡片材质字段
ALTER TABLE iot_cards
    ADD COLUMN material VARCHAR(50) NULL COMMENT '卡片材质编码' AFTER card_type;

-- 新增采购批次材质字段，便于追溯入库来源
ALTER TABLE purchase_batches
    ADD COLUMN material VARCHAR(50) NULL COMMENT '卡片材质编码' AFTER period_type;

-- 为已有数据补默认值，避免前端展示空白
UPDATE iot_cards
SET material = 'plastic_plug'
WHERE material IS NULL;

UPDATE purchase_batches
SET material = 'plastic_plug'
WHERE material IS NULL;
