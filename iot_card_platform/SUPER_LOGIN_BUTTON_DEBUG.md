# 超级登录按钮不显示问题排查

## 问题描述
用户管理页面中，超级登录按钮不显示。

## 已完成的修复

### 1. 数据库字段修复 ✅
```sql
ALTER TABLE sys_super_login_logs 
ADD COLUMN is_deleted TINYINT DEFAULT 0;
```

### 2. 添加调试日志 ✅
在 `canSuperLogin()` 函数中添加了详细的调试日志。

### 3. 确保用户信息加载 ✅
在页面 `onMounted` 时确保获取当前用户信息。

## 排查步骤

### 步骤1：检查后端数据
```bash
# 1. 登录获取Token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"account":"admin","password":"admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['data']['access_token'])")

# 2. 获取当前用户信息
curl -s -X GET "http://localhost:8000/api/v1/auth/profile" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# 3. 获取用户列表
curl -s -X GET "http://localhost:8000/api/v1/users?page=1&page_size=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**预期结果**：
- 当前用户包含 `user_level: 1`
- 用户列表中的用户包含 `user_level: 2`

### 步骤2：检查前端控制台
打开浏览器开发者工具（F12），查看控制台输出：

```
当前用户: 超级管理员 user_level: 1
目标用户: 上海无发信息科技有限公司 user_level: 2 parent_id: 1
✅ 超级管理员可以登录到普通用户
```

### 步骤3：检查按钮渲染
在浏览器控制台执行：
```javascript
// 检查 authStore
console.log('authStore.userInfo:', window.$nuxt?.$store?.state?.auth?.userInfo)

// 或者在 Vue DevTools 中查看
// Components -> Users -> authStore
```

### 步骤4：检查条件判断
```javascript
// 在浏览器控制台
const currentUser = { user_level: 1 }
const targetUser = { user_level: 2, parent_id: 1 }

// 超级管理员 -> 普通用户
console.log('条件1:', currentUser.user_level === 1 && targetUser.user_level === 2)
// 应该输出: true
```

## 可能的原因

### 原因1：用户信息未加载
**症状**：控制台显示 "当前用户信息未加载"

**解决方案**：
```typescript
// 在 App.vue 或路由守卫中确保加载用户信息
const authStore = useAuthStore()
if (authStore.token && !authStore.userInfo) {
  await authStore.getUserInfo()
}
```

### 原因2：user_level 字段缺失
**症状**：控制台显示 `user_level: undefined`

**解决方案**：
检查类型定义 `frontend/src/types/user.d.ts`：
```typescript
export interface User {
  id: number
  user_level: number  // 确保有这个字段
  // ...
}
```

### 原因3：条件判断错误
**症状**：控制台显示 "❌ 不满足超级登录条件"

**检查**：
- 当前用户的 `user_level` 是否为 1
- 目标用户的 `user_level` 是否为 2
- 目标用户的 `parent_id` 是否正确

### 原因4：v-if 条件问题
**检查模板代码**：
```vue
<el-button
  v-if="canSuperLogin(row)"
  type="success"
  link
  :icon="SwitchButton"
  @click="handleSuperLogin(row)"
>
  超级登录
</el-button>
```

确保：
- `canSuperLogin` 函数已定义
- `SwitchButton` 图标已导入
- `row` 对象包含完整的用户信息

## 测试用例

### 测试1：超级管理员查看用户列表
```
当前用户: admin (user_level: 1)
用户列表:
  - 用户A (user_level: 2) -> 应该显示"超级登录"按钮 ✅
  - 用户B (user_level: 2) -> 应该显示"超级登录"按钮 ✅
  - 用户C (user_level: 1) -> 不应该显示按钮 ❌
```

### 测试2：普通用户查看用户列表
```
当前用户: 用户A (user_level: 2, id: 5)
用户列表:
  - 子用户1 (user_level: 3, parent_id: 5) -> 应该显示"超级登录"按钮 ✅
  - 子用户2 (user_level: 3, parent_id: 6) -> 不应该显示按钮 ❌
  - 用户B (user_level: 2) -> 不应该显示按钮 ❌
```

## 快速验证脚本

在浏览器控制台执行：
```javascript
// 1. 检查当前用户
const authStore = useAuthStore()
console.log('当前用户:', authStore.userInfo)

// 2. 检查用户列表
const userList = document.querySelectorAll('.el-table__row')
console.log('用户列表行数:', userList.length)

// 3. 检查超级登录按钮
const superLoginButtons = document.querySelectorAll('button:contains("超级登录")')
console.log('超级登录按钮数量:', superLoginButtons.length)
```

## 临时解决方案

如果问题仍然存在，可以临时强制显示按钮进行测试：
```vue
<el-button
  v-if="true"  <!-- 临时改为 true -->
  type="success"
  link
  :icon="SwitchButton"
  @click="handleSuperLogin(row)"
>
  超级登录
</el-button>
```

然后查看点击按钮后的错误信息。

## 最终检查清单

- [ ] 后端 `/api/v1/auth/profile` 返回包含 `user_level`
- [ ] 后端 `/api/v1/users` 返回的用户包含 `user_level`
- [ ] 前端 `authStore.userInfo` 不为 null
- [ ] 前端 `authStore.userInfo.user_level` 有值
- [ ] 用户列表中的用户对象包含 `user_level`
- [ ] `canSuperLogin()` 函数逻辑正确
- [ ] `SwitchButton` 图标已正确导入
- [ ] 浏览器控制台无错误信息

## 联系支持

如果以上步骤都无法解决问题，请提供：
1. 浏览器控制台完整日志
2. Network 标签中的 API 请求响应
3. Vue DevTools 中的组件状态截图
4. 当前用户和目标用户的完整信息


