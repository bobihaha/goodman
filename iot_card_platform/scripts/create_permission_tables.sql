-- 权限管理系统数据库表
-- 用于实现动态权限分配和控制

USE iot_card_platform;

-- 1. 权限表
CREATE TABLE IF NOT EXISTS sys_permissions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
  code VARCHAR(100) NOT NULL UNIQUE COMMENT '权限代码',
  name VARCHAR(100) NOT NULL COMMENT '权限名称',
  module VARCHAR(50) NOT NULL COMMENT '所属模块',
  description VARCHAR(500) DEFAULT NULL COMMENT '权限描述',
  sort_order INT DEFAULT 0 COMMENT '排序',
  is_deleted TINYINT DEFAULT 0 COMMENT '删除标记：0=未删除，1=已删除',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  INDEX idx_module (module),
  INDEX idx_code (code),
  INDEX idx_is_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统权限表';

-- 2. 用户权限关联表
CREATE TABLE IF NOT EXISTS sys_user_permissions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
  user_id BIGINT NOT NULL COMMENT '用户ID',
  permission_id BIGINT NOT NULL COMMENT '权限ID',
  is_deleted TINYINT DEFAULT 0 COMMENT '删除标记：0=未删除，1=已删除',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  UNIQUE KEY uk_user_permission (user_id, permission_id, is_deleted),
  INDEX idx_user_id (user_id),
  INDEX idx_permission_id (permission_id),
  INDEX idx_is_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户权限关联表';

-- 3. 插入基础权限数据
INSERT INTO sys_permissions (code, name, module, description, sort_order) VALUES
-- 卡片管理权限
('card:view', '查看卡片', 'card', '查看卡片列表和详情', 100),
('card:create', '创建卡片', 'card', '创建新卡片', 101),
('card:edit', '编辑卡片', 'card', '编辑卡片信息', 102),
('card:delete', '删除卡片', 'card', '删除卡片', 103),
('card:activate', '激活卡片', 'card', '激活卡片', 104),
('card:suspend', '停用卡片', 'card', '停用/复机卡片', 105),
('card:export', '导出卡片', 'card', '导出卡片数据', 106),
('card:view_customer', '查看客户信息', 'card', '查看卡片关联的客户信息', 107),
('card:transfer', '划拨卡片', 'card', '划拨卡片给其他用户', 108),

-- 流量池管理权限
('pool:view', '查看流量池', 'pool', '查看流量池列表和详情', 200),
('pool:create', '创建流量池', 'pool', '创建新流量池', 201),
('pool:edit', '编辑流量池', 'pool', '编辑流量池信息', 202),
('pool:delete', '删除流量池', 'pool', '删除流量池', 203),
('pool:add_card', '添加卡片', 'pool', '添加卡片到流量池', 204),
('pool:remove_card', '移除卡片', 'pool', '从流量池移除卡片', 205),
('pool:view_customer', '查看客户信息', 'pool', '查看流量池关联的客户信息', 206),

-- 用户管理权限
('user:view', '查看用户', 'user', '查看用户列表和详情', 300),
('user:create', '创建用户', 'user', '创建新用户', 301),
('user:edit', '编辑用户', 'user', '编辑用户信息', 302),
('user:delete', '删除用户', 'user', '删除用户', 303),
('user:reset_password', '重置密码', 'user', '重置用户密码', 304),
('user:super_login', '超级登录', 'user', '超级登录到下级用户', 305),
('user:manage_permission', '管理权限', 'user', '管理用户权限', 306),

-- 套餐管理权限
('package:view', '查看套餐', 'package', '查看套餐列表和详情', 400),
('package:create', '创建套餐', 'package', '创建新套餐', 401),
('package:edit', '编辑套餐', 'package', '编辑套餐信息', 402),
('package:delete', '删除套餐', 'package', '删除套餐', 403),
('package:view_supplier', '查看供应商信息', 'package', '查看套餐关联的供应商信息', 404),

-- 库存管理权限
('stock:view', '查看库存', 'stock', '查看库存列表和详情', 500),
('stock:in', '卡片入库', 'stock', '卡片入库操作', 501),
('stock:out', '卡片出库', 'stock', '卡片出库操作', 502),
('stock:edit', '编辑库存', 'stock', '编辑库存信息', 503),
('stock:view_customer', '查看客户信息', 'stock', '查看出入库关联的客户信息', 504),

-- 供应商管理权限
('supplier:view', '查看供应商', 'supplier', '查看供应商列表和详情', 600),
('supplier:create', '创建供应商', 'supplier', '创建新供应商', 601),
('supplier:edit', '编辑供应商', 'supplier', '编辑供应商信息', 602),
('supplier:delete', '删除供应商', 'supplier', '删除供应商', 603),

-- 停卡策略权限
('suspend:view', '查看停卡策略', 'suspend', '查看停卡策略列表和详情', 700),
('suspend:create', '创建停卡策略', 'suspend', '创建新停卡策略', 701),
('suspend:edit', '编辑停卡策略', 'suspend', '编辑停卡策略', 702),
('suspend:delete', '删除停卡策略', 'suspend', '删除停卡策略', 703),

-- 系统管理权限
('system:view', '查看系统设置', 'system', '查看系统设置', 800),
('system:config', '系统配置', 'system', '修改系统配置', 801),
('system:logs', '查看日志', 'system', '查看系统日志', 802),

-- 仪表盘权限
('dashboard:view', '查看仪表盘', 'dashboard', '查看仪表盘数据', 900);

-- 4. 为超级管理员分配所有权限
INSERT INTO sys_user_permissions (user_id, permission_id)
SELECT 1, id FROM sys_permissions WHERE is_deleted = 0;

-- 查看插入结果
SELECT 
    COUNT(*) as total_permissions,
    COUNT(DISTINCT module) as total_modules
FROM sys_permissions 
WHERE is_deleted = 0;

SELECT 
    module,
    COUNT(*) as permission_count
FROM sys_permissions 
WHERE is_deleted = 0
GROUP BY module
ORDER BY module;


