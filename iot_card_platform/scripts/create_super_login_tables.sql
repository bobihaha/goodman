-- 创建超级登录日志表
-- 用于记录超级登录操作的审计日志

USE iot_card_platform;

-- 1. 创建超级登录日志表
CREATE TABLE IF NOT EXISTS sys_super_login_logs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
  original_user_id BIGINT NOT NULL COMMENT '原用户ID',
  target_user_id BIGINT NOT NULL COMMENT '目标用户ID',
  login_at DATETIME NOT NULL COMMENT '登录时间',
  logout_at DATETIME DEFAULT NULL COMMENT '退出时间',
  ip VARCHAR(50) DEFAULT NULL COMMENT 'IP地址',
  user_agent VARCHAR(500) DEFAULT NULL COMMENT '浏览器信息',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  INDEX idx_original_user (original_user_id),
  INDEX idx_target_user (target_user_id),
  INDEX idx_login_at (login_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='超级登录日志表';

-- 2. 创建操作日志表（用于记录所有关键操作）
CREATE TABLE IF NOT EXISTS sys_operation_logs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
  user_id BIGINT NOT NULL COMMENT '操作用户ID',
  operation_type VARCHAR(50) NOT NULL COMMENT '操作类型',
  operation_module VARCHAR(50) NOT NULL COMMENT '操作模块',
  operation_desc VARCHAR(500) DEFAULT NULL COMMENT '操作描述',
  request_method VARCHAR(10) DEFAULT NULL COMMENT '请求方法',
  request_url VARCHAR(500) DEFAULT NULL COMMENT '请求URL',
  request_params TEXT DEFAULT NULL COMMENT '请求参数',
  response_status INT DEFAULT NULL COMMENT '响应状态码',
  ip VARCHAR(50) DEFAULT NULL COMMENT 'IP地址',
  user_agent VARCHAR(500) DEFAULT NULL COMMENT '浏览器信息',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  
  INDEX idx_user_id (user_id),
  INDEX idx_operation_type (operation_type),
  INDEX idx_operation_module (operation_module),
  INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表';

-- 3. 插入一些测试数据（可选）
-- INSERT INTO sys_super_login_logs (original_user_id, target_user_id, login_at, ip, user_agent)
-- VALUES (1, 2, NOW(), '127.0.0.1', 'Mozilla/5.0');





