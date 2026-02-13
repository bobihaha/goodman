-- 添加停卡管理菜单

-- 1. 添加停卡管理父菜单
INSERT INTO sys_menus (code, name, path, parent_id, sort, icon, status, created_at, updated_at)
VALUES ('suspend', '停卡管理', '/suspend', NULL, 8, 'warning', 'enable', NOW(), NOW());

-- 获取刚插入的父菜单ID（假设为80）
SET @parent_id = LAST_INSERT_ID();

-- 2. 添加停卡策略子菜单
INSERT INTO sys_menus (code, name, path, parent_id, sort, icon, status, created_at, updated_at)
VALUES ('suspend_policy', '停卡策略', '/suspend/policy', @parent_id, 1, 'setting', 'enable', NOW(), NOW());

-- 3. 添加停卡记录子菜单
INSERT INTO sys_menus (code, name, path, parent_id, sort, icon, status, created_at, updated_at)
VALUES ('suspend_logs', '停卡记录', '/suspend/logs', @parent_id, 2, 'document', 'enable', NOW(), NOW());

-- 4. 为超级管理员（user_id=1）分配菜单权限
INSERT INTO sys_user_menus (user_id, menu_id, created_at)
SELECT 1, id, NOW() FROM sys_menus WHERE code IN ('suspend', 'suspend_policy', 'suspend_logs') AND is_deleted = 0;

-- 查看结果
SELECT id, code, name, path, parent_id, sort FROM sys_menus WHERE code LIKE 'suspend%' AND is_deleted = 0;
