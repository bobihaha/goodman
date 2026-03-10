-- 创建卡片用量历史表
CREATE TABLE IF NOT EXISTS card_usage_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '历史记录ID',
    card_id BIGINT NOT NULL COMMENT '卡片ID',
    iccid VARCHAR(30) NOT NULL COMMENT 'ICCID',
    data_used BIGINT NOT NULL DEFAULT 0 COMMENT '已用流量(MB)',
    data_total BIGINT NOT NULL COMMENT '总流量(MB)',
    period_type VARCHAR(20) NOT NULL COMMENT '周期类型: monthly/yearly',
    snapshot_date DATE NOT NULL COMMENT '快照日期',
    snapshot_type VARCHAR(20) NOT NULL COMMENT '快照类型: month_end/period_end',
    snapshot_month VARCHAR(7) NULL COMMENT '快照月份: YYYY-MM',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_card_id (card_id),
    INDEX idx_iccid (iccid),
    INDEX idx_snapshot_date (snapshot_date),
    UNIQUE KEY uq_card_snapshot (card_id, snapshot_type, snapshot_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='卡片用量历史记录';
