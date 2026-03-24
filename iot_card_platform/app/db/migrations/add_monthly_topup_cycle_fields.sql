ALTER TABLE iot_cards
    ADD COLUMN addon_flow BIGINT NOT NULL DEFAULT 0 COMMENT '当月补量(MB)' AFTER data_used_month,
    ADD COLUMN addon_flow_month VARCHAR(7) NULL COMMENT '补量生效月份(YYYY-MM)' AFTER addon_flow;

ALTER TABLE traffic_pools
    ADD COLUMN addon_flow_month VARCHAR(7) NULL COMMENT '叠加流量生效月份(YYYY-MM)' AFTER addon_flow;

UPDATE iot_cards
SET addon_flow_month = DATE_FORMAT(CURDATE(), '%Y-%m')
WHERE addon_flow > 0
  AND (addon_flow_month IS NULL OR addon_flow_month = '');

UPDATE traffic_pools
SET addon_flow_month = DATE_FORMAT(CURDATE(), '%Y-%m')
WHERE addon_flow > 0
  AND (addon_flow_month IS NULL OR addon_flow_month = '');
