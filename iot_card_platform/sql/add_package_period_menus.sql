-- 套餐周期管理菜单
-- 顶级菜单：套餐周期管理
-- 子菜单：强制激活管理、修改套餐

SET NAMES utf8mb4;

INSERT INTO sys_menus (
    parent_id, user_level, code, name, type, icon, path, permission, sort_order, is_visible, status, created_at, updated_at
)
SELECT
    0, 1, 'package_period', '套餐周期管理', 'directory', 'Calendar', '/package-period', NULL, 66, 1, 'enable', NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM sys_menus WHERE code = 'package_period' AND is_deleted = 0
);

INSERT INTO sys_menus (
    parent_id, user_level, code, name, type, icon, path, permission, sort_order, is_visible, status, created_at, updated_at
)
SELECT
    parent.id, 1, 'package_period_force_activate', '强制激活管理', 'menu', 'Calendar', '/package-period/force-activate', NULL, 1, 1, 'enable', NOW(), NOW()
FROM sys_menus parent
WHERE parent.code = 'package_period'
  AND parent.is_deleted = 0
  AND NOT EXISTS (
      SELECT 1 FROM sys_menus WHERE code = 'package_period_force_activate' AND is_deleted = 0
  );

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
    parent_id, user_level, code, name, type, icon, path, permission, sort_order, is_visible, status, created_at, updated_at
)
SELECT
    parent.id, 1, 'package_period_change_package', '修改套餐', 'menu', 'Calendar', '/package-period/change-package', NULL, 2, 1, 'enable', NOW(), NOW()
FROM sys_menus parent
WHERE parent.code = 'package_period'
  AND parent.is_deleted = 0
  AND NOT EXISTS (
      SELECT 1 FROM sys_menus WHERE code = 'package_period_change_package'
  );

-- 为超级管理员分配菜单权限
-- 线上部分环境 sys_user_menus 只有 created_at，没有 updated_at，这里按兼容口径写入
UPDATE sys_user_menus um
JOIN sys_menus m
  ON m.id = um.menu_id
 AND m.code IN ('package_period', 'package_period_force_activate', 'package_period_change_package')
 AND m.is_deleted = 0
SET um.is_deleted = 0
WHERE um.user_id = 1;

INSERT INTO sys_user_menus (user_id, menu_id, created_at)
SELECT 1, m.id, NOW()
FROM sys_menus m
WHERE m.code IN ('package_period', 'package_period_force_activate', 'package_period_change_package')
  AND m.is_deleted = 0
  AND NOT EXISTS (
      SELECT 1
      FROM sys_user_menus um
      WHERE um.user_id = 1
        AND um.menu_id = m.id
        AND um.is_deleted = 0
  );
