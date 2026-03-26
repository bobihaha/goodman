CREATE TABLE IF NOT EXISTS `card_user_remarks` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `card_id` BIGINT NOT NULL COMMENT '卡片ID',
    `user_id` BIGINT NOT NULL COMMENT '备注所属用户ID',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注内容',
    `source` VARCHAR(20) NOT NULL DEFAULT 'system' COMMENT '来源: system/h5',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` INT DEFAULT 0 COMMENT '删除标记：0=未删除，1=已删除',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_card_user_remark_card_user` (`card_id`, `user_id`),
    KEY `idx_card_user_remarks_card_id` (`card_id`),
    KEY `idx_card_user_remarks_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='按用户隔离的卡片备注表';

INSERT INTO `card_user_remarks` (`card_id`, `user_id`, `remark`, `source`, `created_at`, `updated_at`, `is_deleted`)
SELECT
    c.id,
    c.user_id,
    c.remark,
    'legacy',
    NOW(),
    NOW(),
    0
FROM `iot_cards` c
WHERE c.is_deleted = 0
  AND c.user_id IS NOT NULL
  AND c.remark IS NOT NULL
  AND TRIM(c.remark) <> ''
ON DUPLICATE KEY UPDATE
    `remark` = VALUES(`remark`),
    `source` = VALUES(`source`),
    `updated_at` = VALUES(`updated_at`);
