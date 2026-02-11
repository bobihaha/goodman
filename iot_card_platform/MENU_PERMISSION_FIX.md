# 权限菜单系统修复说明

## 问题描述
超级登录到子账户后，前端依然显示所有菜单，没有根据子账户的权限动态显示菜单。

## 问题原因
1. **前端菜单是硬编码的**：`MainLayout.vue` 中的 `menuList` 是写死的，没有从后端动态加载
2. **缺少菜单API调用**：前端没有调用后端的菜单接口获取用户的菜单权限
3. **超级管理员菜单未分配**：数据库中超级管理员只分配了部分菜单（13个），缺少核心菜单

## 解决方案

### 1. 创建菜单API模块
**文件**: `frontend/src/api/modules/menu.ts`

```typescript
export const menuApi = {
  getAllMenus(): Promise<Menu[]>           // 获取所有菜单
  getUserMenuIds(userId: number): Promise<number[]>  // 获取用户菜单ID
  setUserMenus(userId: number, menuIds: number[]): Promise<void>  // 设置用户菜单
}
```

### 2. 扩展用户类型定义
**文件**: `frontend/src/types/user.d.ts`

添加了完整的 `Menu` 接口，与后端 `sys_menus` 表对应。

### 3. 更新 Auth Store
**文件**: `frontend/src/stores/modules/auth.ts`

**新增状态**:
- `menus: ref<Menu[]>([])` - 用户菜单列表

**新增方法**:
- `loadUserMenus()` - 加载用户菜单
- `buildMenuTree()` - 构建菜单树结构

**修改方法**:
- `login()` - 登录后加载菜单
- `superLogin()` - 超级登录后加载目标用户的菜单
- `exitSuperLogin()` - 退出超级登录后重新加载原用户菜单
- `getUserInfo()` - 获取用户信息后加载菜单
- `logout()` - 登出时清空菜单

### 4. 更新主布局组件
**文件**: `frontend/src/components/layout/MainLayout.vue`

**修改**:
- 将硬编码的 `menuList` 改为从 `authStore.menus` 动态获取
- 添加 `iconMap` 映射，根据菜单 code 或 path 匹配图标
- 添加 `convertMenus()` 方法，将后端菜单格式转换为前端格式

### 5. 修复数据库菜单分配
**脚本**: `fix_admin_menus.py`（已执行并删除）

为超级管理员（用户ID=1）分配了所有25个菜单。

## 工作流程

### 登录流程
1. 用户登录 → `authStore.login()`
2. 保存 token 和用户信息
3. 调用 `loadUserMenus()` 加载用户菜单
4. 前端根据菜单数据动态渲染侧边栏

### 超级登录流程
1. 点击超级登录 → `authStore.superLogin(targetUserId)`
2. 保存原用户信息
3. 切换到目标用户的 token
4. 调用 `loadUserMenus()` 加载**目标用户的菜单**
5. 前端显示目标用户的菜单（权限受限）

### 退出超级登录流程
1. 点击退出超级登录 → `authStore.exitSuperLogin()`
2. 恢复原用户的 token
3. 调用 `loadUserMenus()` 重新加载**原用户的菜单**
4. 前端恢复显示原用户的完整菜单

## 后端API说明

### 获取所有菜单
```
GET /api/v1/sys-menus
```
返回所有菜单列表（仅超级管理员可访问）

### 获取用户菜单ID列表
```
GET /api/v1/sys-menus/user/{user_id}
```
返回指定用户的菜单ID数组

### 设置用户菜单权限
```
PUT /api/v1/sys-menus/user/{user_id}
Body: [menu_id1, menu_id2, ...]
```
为用户分配菜单权限（覆盖式）

## 数据库表结构

### sys_menus（菜单表）
- `id` - 菜单ID
- `parent_id` - 父菜单ID（0表示根菜单）
- `code` - 菜单编码
- `name` - 菜单名称
- `path` - 路由路径
- `icon` - 图标
- `type` - 类型（directory/menu/button）
- `permission` - 权限标识
- `sort_order` - 排序

### sys_user_menus（用户菜单关联表）
- `user_id` - 用户ID
- `menu_id` - 菜单ID

## 测试验证

### 测试步骤
1. 以超级管理员登录，应该看到所有菜单
2. 创建一个子用户，只分配部分菜单权限
3. 超级登录到子用户，应该只看到子用户的菜单
4. 退出超级登录，应该恢复看到所有菜单

### 预期结果
- ✅ 超级管理员看到所有菜单（25个）
- ✅ 子用户只看到分配的菜单
- ✅ 超级登录后菜单动态切换
- ✅ 退出超级登录后菜单恢复

## 注意事项

1. **菜单图标映射**：前端根据菜单的 `code` 或 `path` 匹配图标，如果新增菜单需要在 `iconMap` 中添加映射

2. **菜单树构建**：前端会自动将扁平的菜单列表构建为树形结构，根据 `parent_id` 字段

3. **权限控制**：
   - 菜单权限控制菜单的显示/隐藏
   - 操作权限（permissions）控制按钮的显示/隐藏
   - 两者是独立的，需要分别配置

4. **默认菜单**：如果用户没有分配任何菜单，前端会显示空菜单列表

## 后续优化建议

1. **添加菜单管理界面**：让超级管理员可以在前端界面中为用户分配菜单权限

2. **菜单缓存**：考虑将菜单数据缓存到 localStorage，减少API调用

3. **路由守卫增强**：在路由守卫中检查用户是否有访问该路由的菜单权限

4. **菜单权限可视化**：在用户管理页面显示用户的菜单权限树

5. **批量分配**：支持批量为多个用户分配相同的菜单权限

## 修改文件清单

- ✅ `frontend/src/api/modules/menu.ts` - 新建
- ✅ `frontend/src/api/index.ts` - 修改
- ✅ `frontend/src/types/user.d.ts` - 修改
- ✅ `frontend/src/stores/modules/auth.ts` - 修改
- ✅ `frontend/src/components/layout/MainLayout.vue` - 修改
- ✅ 数据库 `sys_user_menus` 表 - 修改（为用户ID=1分配所有菜单）

## 完成时间
2026-02-11 17:48

