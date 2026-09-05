-- 变更目标：为客户用量告警保存触发时的流量快照，确保邮件历史数据一致
-- 风险级别：低（仅新增可空字段）
-- 执行前提：确认 alert_logs 表存在且以下字段尚未创建

ALTER TABLE `alert_logs`
    ADD COLUMN `data_used_snapshot` BIGINT DEFAULT NULL COMMENT '告警时已用流量快照(MB)' AFTER `threshold`,
    ADD COLUMN `data_total_snapshot` BIGINT DEFAULT NULL COMMENT '告警时总流量快照(MB)' AFTER `data_used_snapshot`,
    ADD COLUMN `remaining_flow_snapshot` BIGINT DEFAULT NULL COMMENT '告警时剩余流量快照(MB)' AFTER `data_total_snapshot`,
    ADD COLUMN `sync_at_snapshot` DATETIME DEFAULT NULL COMMENT '告警时流量同步时间快照' AFTER `remaining_flow_snapshot`;

-- 校验字段
SHOW COLUMNS FROM `alert_logs` WHERE Field IN (
    'data_used_snapshot',
    'data_total_snapshot',
    'remaining_flow_snapshot',
    'sync_at_snapshot'
);
