-- 为三级用户分配完整的菜单权限（继承二级用户的菜单 + 项目管理）
USE iot_card_platform;

-- 为每个三级用户分配其父用户（二级用户）的所有菜单 + 项目管理菜单
INSERT INTO sys_user_menus (user_id, menu_id, created_at)
SELECT DISTINCT
    sub_user.id as user_id,
    parent_menu.menu_id,
    NOW()
FROM sys_users sub_user
INNER JOIN sys_users parent_user ON sub_user.parent_id = parent_user.id
INNER JOIN sys_user_menus parent_menu ON parent_user.id = parent_menu.user_id
WHERE sub_user.user_level = 3
  AND sub_user.is_deleted = 0
  AND parent_user.is_deleted = 0
  AND NOT EXISTS (
    SELECT 1 FROM sys_user_menus existing
    WHERE existing.user_id = sub_user.id
      AND existing.menu_id = parent_menu.menu_id
  );

-- 确保所有三级用户都有项目管理菜单
SET @project_menu_id = (SELECT id FROM sys_menus WHERE code = 'projects' LIMIT 1);

INSERT INTO sys_user_menus (user_id, menu_id, created_at)
SELECT u.id, @project_menu_id, NOW()
FROM sys_users u
WHERE u.user_level = 3
  AND u.is_deleted = 0
  AND NOT EXISTS (
    SELECT 1 FROM sys_user_menus um
    WHERE um.user_id = u.id AND um.menu_id = @project_menu_id
  );

-- 验证
SELECT '=== 三级用户菜单分配情况 ===' AS status;
SELECT u.id, u.name, u.account, COUNT(um.menu_id) as menu_count
FROM sys_users u
LEFT JOIN sys_user_menus um ON u.id = um.user_id
WHERE u.user_level = 3 AND u.is_deleted = 0
GROUP BY u.id, u.name, u.account;
