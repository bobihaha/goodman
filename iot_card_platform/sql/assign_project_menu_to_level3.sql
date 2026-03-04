-- 为所有三级用户分配项目管理菜单权限
-- 执行方式: mysql -u root -p < sql/assign_project_menu_to_level3.sql

USE iot_card_platform;

-- 获取项目管理菜单ID
SET @project_menu_id = (SELECT id FROM sys_menus WHERE code = 'projects' LIMIT 1);

-- 为所有三级用户（user_level=3）分配项目管理菜单
INSERT INTO sys_user_menus (user_id, menu_id, created_at)
SELECT u.id, @project_menu_id, NOW()
FROM sys_users u
WHERE u.user_level = 3
  AND u.is_deleted = 0
  AND NOT EXISTS (
    SELECT 1 FROM sys_user_menus um
    WHERE um.user_id = u.id AND um.menu_id = @project_menu_id
  );

-- 验证结果
SELECT '=== 已分配项目管理菜单的三级用户 ===' AS status;
SELECT u.id, u.name, u.account, COUNT(um.id) as menu_count
FROM sys_users u
LEFT JOIN sys_user_menus um ON u.id = um.user_id AND um.menu_id = @project_menu_id
WHERE u.user_level = 3 AND u.is_deleted = 0
GROUP BY u.id, u.name, u.account;
