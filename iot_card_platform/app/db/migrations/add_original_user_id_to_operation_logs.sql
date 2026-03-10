-- 添加 original_user_id 字段到操作日志表
ALTER TABLE sys_operation_logs 
ADD COLUMN original_user_id BIGINT UNSIGNED NULL COMMENT '原始用户ID(超级登录时)' AFTER user_name,
ADD INDEX idx_original_user_id (original_user_id);
