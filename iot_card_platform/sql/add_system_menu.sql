-- 添加系统设置菜单
-- 执行前请先查询是否已存在: SELECT * FROM sys_menus WHERE code = 'system';

-- 1. 添加系统设置菜单（顶级菜单，仅超级管理员可见）
INSERT INTO sys_menus (code, name, path, parent_id, sort, icon, status, created_at, updated_at)
VALUES ('system', '系统设置', '/system/config', NULL, 99, 'setting', 'enable', NOW(), NOW());

-- 2. 为超级管理员（user_id=1）分配菜单权限
INSERT INTO sys_user_menus (user_id, menu_id, created_at)
SELECT 1, id, NOW() FROM sys_menus WHERE code = 'system'
ON DUPLICATE KEY UPDATE created_at = NOW();

-- 验证
SELECT id, code, name, path, sort FROM sys_menus WHERE code = 'system';
