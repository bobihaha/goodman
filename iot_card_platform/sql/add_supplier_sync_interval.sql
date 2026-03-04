-- 添加供应商同步间隔字段
ALTER TABLE suppliers ADD COLUMN sync_interval INT DEFAULT 60 COMMENT '同步间隔(分钟)';
