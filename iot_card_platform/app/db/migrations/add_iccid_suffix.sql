-- 添加 iccid_suffix 字段
ALTER TABLE iot_cards ADD COLUMN iccid_suffix VARCHAR(6) NULL COMMENT 'ICCID后6位' AFTER iccid;

-- 创建索引
CREATE INDEX idx_iccid_suffix ON iot_cards(iccid_suffix);

-- 更新现有数据（从 iccid 提取后6位）
UPDATE iot_cards SET iccid_suffix = RIGHT(iccid, 6) WHERE iccid IS NOT NULL;
