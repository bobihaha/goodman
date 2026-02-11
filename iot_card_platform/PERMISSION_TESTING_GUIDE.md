# 权限管理系统测试指南

## 一、测试前准备

### 1. 确保服务运行

**后端服务**：
```bash
cd /Users/huiren/Documents/goodman/iot_card_platform
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端服务**：
```bash
cd /Users/huiren/Documents/goodman/iot_card_platform/frontend
npm run dev
```

### 2. 初始化权限数据

执行SQL脚本创建权限表和初始数据：
```bash
mysql -u root -p iot_card_platform < scripts/create_permission_tables.sql
```

这将创建：
- `permissions` 表（权限表）
- `user_permissions` 表（用户权限关联表）
- 45个预置权限数据

## 二、功能测试

### 测试1：权限管理页面

**访问路径**：系统设置 > 权限管理

**测试步骤**：
1. 登录系统（使用超级管理员账号）
2. 点击左侧菜单"系统设置"
3. 点击子菜单"权限管理"
4. 验证页面正常加载，显示权限列表

**预期结果**：
- 显示45个预置权限
- 权限按模块分组显示
- 可以看到权限代码、名称、模块、描述等信息

**测试功能**：
- ✅ 分页功能（每页10/20/50/100条）
- ✅ 模块筛选（9个模块下拉选择）
- ✅ 关键词搜索（权限名称/代码）
- ✅ 新建权限
- ✅ 编辑权限
- ✅ 删除权限

### 测试2：新建权限

**测试步骤**：
1. 在权限管理页面点击"新建权限"按钮
2. 填写表单：
   - 权限代码：`test:view`
   - 权限名称：`测试查看`
   - 所属模块：选择"系统管理"
   - 模块名称：自动填充"系统管理"
   - 描述：`这是一个测试权限`
3. 点击"确定"

**预期结果**：
- 表单验证通过
- 提示"创建成功"
- 列表自动刷新，显示新创建的权限

**验证点**：
- 权限代码格式验证（必须是 `模块:操作` 格式）
- 必填字段验证
- 模块选择后自动填充模块名称

### 测试3：编辑权限

**测试步骤**：
1. 在权限列表中找到任意权限
2. 点击"编辑"按钮
3. 修改权限名称或描述
4. 点击"确定"

**预期结果**：
- 表单回显原有数据
- 修改成功后提示"更新成功"
- 列表刷新显示修改后的数据

### 测试4：删除权限

**测试步骤**：
1. 在权限列表中找到测试权限
2. 点击"删除"按钮
3. 确认删除

**预期结果**：
- 弹出确认对话框
- 确认后提示"删除成功"
- 列表刷新，该权限消失

### 测试5：用户权限分配

**访问路径**：客户管理

**测试步骤**：
1. 进入"客户管理"页面
2. 找到任意用户
3. 点击"分配权限"按钮
4. 在弹出的对话框中：
   - 查看按模块分组的权限列表
   - 展开/折叠模块
   - 勾选部分权限
   - 使用搜索功能查找权限
   - 点击模块标题的复选框全选/取消全选
5. 点击"确定"保存

**预期结果**：
- 对话框显示用户名称
- 权限按9个模块分组显示
- 可以展开/折叠每个模块
- 搜索功能正常工作
- 模块全选/取消全选功能正常
- 底部显示已选权限数量
- 保存成功后提示"权限分配成功"

**验证点**：
- 模块全选：勾选模块复选框，该模块所有权限被选中
- 模块取消全选：取消模块复选框，该模块所有权限被取消
- 部分选中状态：模块复选框显示为半选状态
- 搜索过滤：输入关键词后只显示匹配的权限
- 已选数量：实时更新已选权限数量

### 测试6：权限指令（v-permission）

**测试场景**：在任意页面使用权限指令控制按钮显示

**示例代码**：
```vue
<template>
  <!-- 单个权限 -->
  <el-button v-permission="'card:edit'">编辑卡片</el-button>
  
  <!-- 多个权限（任意一个） -->
  <el-button v-permission="['card:edit', 'card:delete']">操作</el-button>
  
  <!-- 多个权限（全部拥有） -->
  <el-button v-permission-all="['card:edit', 'card:delete']">批量操作</el-button>
</template>
```

**测试步骤**：
1. 为测试用户分配 `card:view` 权限（不分配 `card:edit`）
2. 使用该用户登录
3. 访问卡片管理页面

**预期结果**：
- 有 `v-permission="'card:view'"` 的按钮显示
- 有 `v-permission="'card:edit'"` 的按钮隐藏
- 有 `v-permission="['card:view', 'card:edit']"` 的按钮显示（任意一个）
- 有 `v-permission-all="['card:view', 'card:edit']"` 的按钮隐藏（需要全部）

### 测试7：权限检查方法

**测试场景**：在组件逻辑中检查权限

**示例代码**：
```typescript
import { useAuthStore } from '@/stores/modules/auth'

const authStore = useAuthStore()

// 检查单个权限
if (authStore.hasPermission('card:edit')) {
  console.log('有编辑权限')
}

// 检查多个权限
if (authStore.hasPermission(['card:edit', 'card:delete'])) {
  console.log('有编辑或删除权限')
}
```

**测试步骤**：
1. 在浏览器控制台执行上述代码
2. 验证返回结果是否正确

**预期结果**：
- 有权限时返回 `true`
- 无权限时返回 `false`

## 三、API测试

### 测试环境
- 后端地址：http://localhost:8000
- API文档：http://localhost:8000/docs

### 1. 获取权限列表（分页）

**请求**：
```bash
curl -X GET "http://localhost:8000/api/v1/permissions?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**预期响应**：
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "items": [...],
    "total": 45,
    "page": 1,
    "page_size": 10,
    "pages": 5
  }
}
```

### 2. 按模块获取权限

**请求**：
```bash
curl -X GET "http://localhost:8000/api/v1/permissions/modules" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**预期响应**：
```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "module": "card",
      "module_name": "卡片管理",
      "permissions": [...]
    },
    ...
  ]
}
```

### 3. 获取用户权限

**请求**：
```bash
curl -X GET "http://localhost:8000/api/v1/permissions/user/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**预期响应**：
```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "id": 1,
      "user_id": 1,
      "permission_id": 1,
      "permission": {...},
      "assigned_at": "2026-02-11T15:30:00"
    },
    ...
  ]
}
```

### 4. 分配用户权限

**请求**：
```bash
curl -X POST "http://localhost:8000/api/v1/permissions/user/1/assign" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"permission_ids": [1, 2, 3, 4, 5]}'
```

**预期响应**：
```json
{
  "code": 200,
  "msg": "权限分配成功",
  "data": null
}
```

### 5. 检查用户权限

**请求**：
```bash
curl -X GET "http://localhost:8000/api/v1/permissions/user/1/check/card:view" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**预期响应**：
```json
{
  "code": 200,
  "msg": "success",
  "data": true
}
```

## 四、数据库验证

### 查询权限表
```sql
-- 查看所有权限
SELECT * FROM permissions ORDER BY module, id;

-- 按模块统计权限数量
SELECT module, module_name, COUNT(*) as count 
FROM permissions 
GROUP BY module, module_name;
```

### 查询用户权限
```sql
-- 查看用户1的所有权限
SELECT u.id, u.account, u.name, p.code, p.name as permission_name
FROM users u
JOIN user_permissions up ON u.id = up.user_id
JOIN permissions p ON up.permission_id = p.id
WHERE u.id = 1;

-- 统计每个用户的权限数量
SELECT u.id, u.account, u.name, COUNT(up.permission_id) as permission_count
FROM users u
LEFT JOIN user_permissions up ON u.id = up.user_id
GROUP BY u.id, u.account, u.name;
```

## 五、边界测试

### 1. 权限代码格式验证
- ✅ 正确格式：`card:view`
- ❌ 错误格式：`cardview`、`card_view`、`Card:View`

### 2. 重复权限代码
- 尝试创建相同权限代码的权限
- 预期：数据库唯一约束报错

### 3. 删除已分配的权限
- 删除已分配给用户的权限
- 预期：需要先解除用户关联或级联删除

### 4. 大量权限分配
- 为用户分配所有45个权限
- 验证性能和界面响应

### 5. 权限搜索
- 搜索中文：`查看`
- 搜索英文：`view`
- 搜索代码：`card:`
- 验证搜索结果准确性

## 六、常见问题

### 1. API返回401未授权
**原因**：未登录或token过期
**解决**：重新登录获取新token

### 2. 权限指令不生效
**原因**：
- 权限数据未加载
- 指令语法错误
- 权限代码不匹配

**解决**：
- 检查 `authStore.permissions` 是否有数据
- 检查指令使用语法
- 检查权限代码拼写

### 3. 权限分配后不生效
**原因**：前端缓存未更新
**解决**：刷新页面重新加载用户信息

### 4. 模块全选不工作
**原因**：权限ID类型不匹配
**解决**：确保 `permission_id` 为数字类型

## 七、测试检查清单

- [ ] 权限管理页面正常访问
- [ ] 权限列表正常显示
- [ ] 分页功能正常
- [ ] 模块筛选正常
- [ ] 关键词搜索正常
- [ ] 新建权限成功
- [ ] 编辑权限成功
- [ ] 删除权限成功
- [ ] 用户权限分配对话框正常打开
- [ ] 权限按模块分组显示
- [ ] 模块展开/折叠正常
- [ ] 权限搜索功能正常
- [ ] 模块全选/取消全选正常
- [ ] 权限保存成功
- [ ] v-permission 指令正常工作
- [ ] v-permission-all 指令正常工作
- [ ] hasPermission 方法返回正确
- [ ] API接口返回正确数据
- [ ] 数据库数据正确保存

## 八、性能测试

### 1. 权限列表加载时间
- 测试加载45个权限的时间
- 预期：< 500ms

### 2. 权限分配保存时间
- 测试分配45个权限的时间
- 预期：< 1s

### 3. 权限搜索响应时间
- 测试搜索关键词的响应时间
- 预期：实时响应（< 100ms）

### 4. 页面渲染性能
- 测试权限管理页面的渲染时间
- 预期：< 1s

---

**测试完成标准**：
- 所有功能测试通过
- 所有API测试通过
- 数据库数据正确
- 无明显性能问题
- 用户体验良好

**测试报告模板**：
```
测试日期：2026-02-11
测试人员：[姓名]
测试环境：开发环境
测试结果：通过/失败
问题列表：
1. [问题描述]
2. [问题描述]
改进建议：
1. [建议内容]
2. [建议内容]
```


