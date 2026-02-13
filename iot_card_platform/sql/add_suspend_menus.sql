-- 添加停卡管理菜单
-- 执行前请先查询是否已存在相关菜单，避免重复添加

-- 1. 添加停卡管理父菜单
INSERT INTO sys_menus (code, name, path, parent_id, sort, icon, status, created_at, updated_at)
VALUES ('suspend', '停卡管理', '/suspend', NULL, 8, 'warning', 'enable', NOW(), NOW());

-- 获取刚插入的父菜单ID（假设为80，实际执行时需要查询）
SET @parent_id = LAST_INSERT_ID();

-- 2. 添加停卡策略子菜单
INSERT INTO sys_menus (code, name, path, parent_id, sort, icon, status, created_at, updated_at)
VALUES ('suspend_policy', '停卡策略', '/suspend/policy', @parent_id, 1, 'setting', 'enable', NOW(), NOW());

-- 3. 添加停卡记录子菜单
INSERT INTO sys_menus (code, name, path, parent_id, sort, icon, status, created_at, updated_at)
VALUES ('suspend_logs', '停卡记录', '/suspend/logs', @parent_id, 2, 'document', 'enable', NOW(), NOW());

-- 4. 添加停卡告警子菜单
INSERT INTO sys_menus (code, name, path, parent_id, sort, icon, status, created_at, updated_at)
VALUES ('suspend_alerts', '停卡告警', '/suspend/alerts', @parent_id, 3, 'bell', 'enable', NOW(), NOW());

-- 5. 为超级管理员（user_id=1）分配菜单权限
INSERT INTO sys_user_menus (user_id, menu_id, created_at)
SELECT 1, id, NOW() FROM sys_menus WHERE code IN ('suspend', 'suspend_policy', 'suspend_logs', 'suspend_alerts');

-- 查询结果验证
SELECT id, code, name, path, parent_id, sort FROM sys_menus WHERE code LIKE '%suspend%' ORDER BY parent_id, sort;


