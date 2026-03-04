-- 检查项目管理菜单和三级用户权限
USE iot_card_platform;

-- 1. 检查项目管理菜单是否存在
SELECT '=== 项目管理菜单 ===' AS status;
SELECT id, code, name, path, user_level FROM sys_menus WHERE code = 'projects';

-- 2. 检查三级用户列表
SELECT '=== 三级用户列表 ===' AS status;
SELECT id, name, account, user_level, parent_id FROM sys_users WHERE user_level = 3 AND is_deleted = 0;

-- 3. 检查三级用户的菜单权限
SELECT '=== 三级用户菜单权限 ===' AS status;
SELECT u.id, u.name, u.account, m.code, m.name as menu_name
FROM sys_users u
LEFT JOIN sys_user_menus um ON u.id = um.user_id
LEFT JOIN sys_menus m ON um.menu_id = m.id
WHERE u.user_level = 3 AND u.is_deleted = 0
ORDER BY u.id, m.sort_order;
