-- 套餐周期管理增加“修改套餐”菜单，仅分配给超级管理员。
SET NAMES utf8mb4;

UPDATE sys_menus menu
JOIN sys_menus parent
  ON parent.code = 'package_period'
 AND parent.is_deleted = 0
SET menu.parent_id = parent.id,
    menu.user_level = 1,
    menu.name = '修改套餐',
    menu.type = 'menu',
    menu.icon = 'Calendar',
    menu.path = '/package-period/change-package',
    menu.permission = NULL,
    menu.sort_order = 2,
    menu.is_visible = 1,
    menu.status = 'enable',
    menu.is_deleted = 0,
    menu.updated_at = NOW()
WHERE menu.code = 'package_period_change_package';

INSERT INTO sys_menus (
    parent_id, user_level, code, name, type, icon, path, permission,
    sort_order, is_visible, status, created_at, updated_at
)
SELECT
    parent.id, 1, 'package_period_change_package', '修改套餐', 'menu', 'Calendar',
    '/package-period/change-package', NULL, 2, 1, 'enable', NOW(), NOW()
FROM sys_menus parent
WHERE parent.code = 'package_period'
  AND parent.is_deleted = 0
  AND NOT EXISTS (
      SELECT 1
      FROM sys_menus
      WHERE code = 'package_period_change_package'
  );

UPDATE sys_user_menus user_menus
JOIN sys_users users
  ON users.id = user_menus.user_id
 AND users.user_level = 1
 AND users.is_deleted = 0
JOIN sys_menus menus
  ON menus.id = user_menus.menu_id
 AND menus.code = 'package_period_change_package'
 AND menus.is_deleted = 0
SET user_menus.is_deleted = 0;

INSERT INTO sys_user_menus (user_id, menu_id, created_at)
SELECT users.id, menus.id, NOW()
FROM sys_users users
JOIN sys_menus menus
  ON menus.code = 'package_period_change_package'
 AND menus.is_deleted = 0
WHERE users.user_level = 1
  AND users.is_deleted = 0
  AND NOT EXISTS (
      SELECT 1
      FROM sys_user_menus user_menus
      WHERE user_menus.user_id = users.id
        AND user_menus.menu_id = menus.id
        AND user_menus.is_deleted = 0
  );
