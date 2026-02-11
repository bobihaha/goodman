# 用户管理与权限系统 - 待开发功能清单

## 📋 当前状态分析

### ✅ 已完成功能

#### 后端已实现
1. **基础认证功能**
   - ✅ 用户登录 (`POST /api/v1/auth/login`)
   - ✅ 退出登录 (`POST /api/v1/auth/logout`)
   - ✅ 刷新令牌 (`POST /api/v1/auth/refresh`)
   - ✅ 获取用户信息 (`GET /api/v1/auth/profile`)
   - ✅ 获取用户权限 (`GET /api/v1/auth/permissions`)
   - ✅ 超级登录 (`POST /api/v1/auth/super-login`)

2. **用户管理基础**
   - ✅ 用户注册 (`POST /api/v1/users/register`)
   - ✅ 用户列表 (`GET /api/v1/users/list`)
   - ✅ 数据模型定义 (UserCreate, UserUpdate, UserInfo)
   - ✅ 用户状态枚举 (enable/disable)
   - ✅ 用户级别定义 (1-超管, 2-用户, 3-子用户)

#### 前端已实现
1. **用户列表页面** (`/views/users/index.vue`)
   - ✅ 用户列表展示
   - ✅ 关键词搜索（账号/姓名/手机号）
   - ✅ 状态筛选
   - ✅ 分页功能
   - ✅ 启用/禁用用户
   - ✅ 删除用户

2. **用户表单组件** (`UserFormDialog.vue`)
   - ✅ 创建用户
   - ✅ 编辑用户
   - ✅ 表单验证

3. **密码管理组件** (`ResetPasswordDialog.vue`)
   - ✅ 重置密码功能

4. **API接口** (`/api/modules/user.ts`)
   - ✅ 基础CRUD接口
   - ✅ 状态更新接口
   - ✅ 密码更新接口

---

## ❌ 待开发功能

### P0 核心功能（必须实现）

#### 1. 超级登录功能 ⭐⭐⭐
**优先级**: P0  
**工作量**: 2-3天

**后端需求**：
- ✅ 超级登录API已实现 (`POST /api/v1/auth/super-login`)
- ✅ Token包含超级登录标识 (`is_super_login`, `original_user_id`)
- ❌ 需要添加退出超级登录API (`POST /api/v1/auth/exit-super-login`)
- ❌ 需要添加超级登录日志记录表和API

**前端需求**：
- ❌ 用户列表添加"超级登录"按钮
- ❌ 创建超级登录提示横幅组件 (`SuperLoginBanner.vue`)
- ❌ 在 MainLayout 中显示超级登录状态
- ❌ 实现"退出超级登录"功能
- ❌ 更新 auth store 支持超级登录状态管理
- ❌ 添加超级登录权限检查

**功能流程**：
```
1. 用户点击"超级登录"按钮
2. 调用 POST /api/v1/auth/super-login { target_user_id }
3. 保存原用户Token到 localStorage
4. 使用新Token刷新页面
5. 顶部显示超级登录横幅
6. 点击"退出超级登录"恢复原用户身份
```

**超级登录横幅设计**：
```vue
<div class="super-login-banner">
  <el-alert
    type="warning"
    :closable="false"
    show-icon
  >
    <template #title>
      <span>⚠️ 当前处于超级登录模式，正在以 <strong>{{ targetUserName }}</strong> 的身份操作</span>
      <el-button type="primary" size="small" @click="exitSuperLogin">
        退出超级登录
      </el-button>
    </template>
  </el-alert>
</div>
```

---

#### 2. 权限管理系统 ⭐⭐⭐
**优先级**: P0  
**工作量**: 3-4天

**后端需求**：
- ❌ 创建权限表 (`sys_permissions`)
- ❌ 创建角色权限关联表 (`sys_role_permissions`)
- ❌ 创建用户权限关联表 (`sys_user_permissions`)
- ❌ 实现权限CRUD API
- ❌ 实现权限分配API (`POST /api/v1/users/{id}/permissions`)
- ❌ 实现权限查询API (`GET /api/v1/users/{id}/permissions`)
- ❌ 在登录响应中返回用户权限列表

**前端需求**：
- ❌ 创建权限常量定义 (`/constants/permission.ts`)
- ❌ 创建权限管理组件 (`PermissionManager.vue`)
- ❌ 在用户详情页添加"权限管理"标签页
- ❌ 实现权限树形选择器
- ❌ 创建 `v-permission` 指令控制按钮显示
- ❌ 在路由守卫中检查菜单权限
- ❌ 更新 auth store 存储用户权限

**权限模块定义**：
```typescript
// constants/permission.ts
export const PERMISSIONS = {
  // 卡片管理
  CARD_VIEW: 'card:view',
  CARD_CREATE: 'card:create',
  CARD_EDIT: 'card:edit',
  CARD_ACTIVATE: 'card:activate',
  CARD_SUSPEND: 'card:suspend',
  CARD_EXPORT: 'card:export',
  CARD_VIEW_CUSTOMER: 'card:view_customer',
  
  // 流量池管理
  POOL_VIEW: 'pool:view',
  POOL_CREATE: 'pool:create',
  POOL_EDIT: 'pool:edit',
  POOL_VIEW_CUSTOMER: 'pool:view_customer',
  
  // 用户管理
  USER_VIEW: 'user:view',
  USER_CREATE: 'user:create',
  USER_EDIT: 'user:edit',
  USER_RESET_PASSWORD: 'user:reset_password',
  USER_SUPER_LOGIN: 'user:super_login',
  USER_MANAGE_PERMISSION: 'user:manage_permission',
  
  // 套餐管理
  PACKAGE_VIEW: 'package:view',
  PACKAGE_CREATE: 'package:create',
  PACKAGE_EDIT: 'package:edit',
  PACKAGE_VIEW_SUPPLIER: 'package:view_supplier',
  
  // 库存管理
  STOCK_VIEW: 'stock:view',
  STOCK_IN: 'stock:in',
  STOCK_OUT: 'stock:out',
  STOCK_EDIT: 'stock:edit',
  STOCK_VIEW_CUSTOMER: 'stock:view_customer',
  
  // 系统管理
  SYSTEM_VIEW: 'system:view',
  SYSTEM_CONFIG: 'system:config',
  SYSTEM_LOGS: 'system:logs'
}
```

**权限指令使用**：
```vue
<!-- 只有拥有权限的用户才能看到按钮 -->
<el-button v-permission="'card:create'">创建卡片</el-button>
<el-button v-permission="['card:edit', 'card:delete']">编辑</el-button>
```

---

#### 3. 用户层级管理 ⭐⭐
**优先级**: P0  
**工作量**: 2天

**后端需求**：
- ❌ 完善用户创建API，支持指定 `parent_id` 和 `user_level`
- ❌ 添加子用户列表API (`GET /api/v1/users/{id}/sub-users`)
- ❌ 添加用户树形结构API (`GET /api/v1/users/tree`)
- ❌ 验证用户只能管理自己的下级用户

**前端需求**：
- ❌ 用户列表改为树形表格展示
- ❌ 创建用户时选择父级用户
- ❌ 创建用户时自动设置 `user_level`
- ❌ 显示用户层级关系
- ❌ 限制用户只能操作下级用户

**用户层级规则**：
```
超级管理员 (user_level = 1)
  ├── 可以创建 user_level = 2 的用户
  ├── 可以管理所有用户
  └── 可以超级登录到任何下级账号

普通用户 (user_level = 2)
  ├── 可以创建 user_level = 3 的子用户
  ├── 只能管理自己的子用户
  └── 可以超级登录到子用户账号

子用户 (user_level = 3)
  ├── 不能创建下级用户
  ├── 只能查看自己的数据
  └── 不能超级登录
```

---

### P1 重要功能（建议实现）

#### 4. 角色模板系统 ⭐⭐
**优先级**: P1  
**工作量**: 2天

**功能描述**：
预定义常用角色模板，快速分配权限

**角色模板**：
1. **售后服务角色** (`after_sales`)
   - 可查看卡片和供应商信息
   - 不能查看客户信息
   - 权限：`card:view`, `card:export`, `package:view`, `package:view_supplier`, `pool:view`

2. **仓库管理角色** (`warehouse`)
   - 可查看库存和出入库
   - 不能查看客户信息
   - 权限：`stock:view`, `stock:in`, `stock:out`, `stock:edit`, `card:view`

3. **普通用户角色** (`user`)
   - 完整权限（可查看客户信息）
   - 权限：所有业务权限

**后端需求**：
- ❌ 在用户表添加 `role_type` 字段
- ❌ 创建角色模板配置表
- ❌ 实现角色模板API (`GET /api/v1/roles/templates`)
- ❌ 应用角色模板API (`POST /api/v1/users/{id}/apply-role`)

**前端需求**：
- ❌ 创建角色选择组件
- ❌ 在用户表单中添加角色选择
- ❌ 在权限管理中支持"使用角色模板"
- ❌ 显示用户当前角色

---

#### 5. 数据权限过滤 ⭐⭐
**优先级**: P1  
**工作量**: 2天

**功能描述**：
根据用户权限自动过滤敏感数据

**客户信息字段**：
```typescript
const CUSTOMER_SENSITIVE_FIELDS = [
  'user_id',
  'user_name',
  'user_phone',
  'user_email',
  'user_address',
  'user_company'
]
```

**实现方式**：
1. **后端过滤**：根据用户权限返回不同字段
2. **前端过滤**：根据权限隐藏敏感字段

**前端需求**：
- ❌ 创建数据过滤工具函数 (`utils/dataFilter.ts`)
- ❌ 在卡片列表中根据权限隐藏客户列
- ❌ 在卡片详情中根据权限隐藏客户信息区域
- ❌ 在流量池中根据权限隐藏客户信息
- ❌ 在导出功能中根据权限过滤字段

**使用示例**：
```vue
<el-table-column
  v-if="hasPermission('card:view_customer')"
  prop="user_name"
  label="所属客户"
/>
```

---

#### 6. 操作日志记录 ⭐
**优先级**: P1  
**工作量**: 1-2天

**功能描述**：
记录用户的关键操作，便于审计

**需要记录的操作**：
- 超级登录/退出超级登录
- 创建/编辑/删除用户
- 修改用户权限
- 重置密码
- 批量操作（划拨、停复机等）

**后端需求**：
- ❌ 创建操作日志表 (`sys_operation_logs`)
- ❌ 实现日志记录中间件
- ❌ 实现日志查询API (`GET /api/v1/logs/operations`)

**前端需求**：
- ❌ 创建操作日志页面 (`/views/system/logs.vue`)
- ❌ 在用户详情中显示该用户的操作日志
- ❌ 支持按操作类型、时间范围筛选

---

### P2 增强功能（可选实现）

#### 7. 用户配额管理 ⭐
**优先级**: P2  
**工作量**: 1天

**功能描述**：
限制用户可创建的卡片数量和子用户数量

**已有字段**：
```typescript
quota: {
  max_cards: number      // 最大卡片数
  max_sub_users: number  // 最大子用户数
}
```

**需要实现**：
- ❌ 在创建卡片时检查配额
- ❌ 在创建子用户时检查配额
- ❌ 在用户列表显示配额使用情况
- ❌ 配额不足时给出明确提示

---

#### 8. 告警通知设置 ⭐
**优先级**: P2  
**工作量**: 1天

**功能描述**：
用户可设置接收告警通知的方式

**已有字段**：
```typescript
alert_notify: {
  sms: boolean      // 短信通知
  email: boolean    // 邮件通知
}
```

**需要实现**：
- ❌ 在用户表单中添加告警通知设置
- ❌ 在用户详情中显示通知设置
- ❌ 实现短信/邮件通知功能（需要对接第三方服务）

---

#### 9. 用户头像上传 ⭐
**优先级**: P2  
**工作量**: 1天

**功能描述**：
用户可上传自定义头像

**需要实现**：
- ❌ 实现文件上传API (`POST /api/v1/upload/avatar`)
- ❌ 创建头像上传组件 (`AvatarUpload.vue`)
- ❌ 在用户表单中添加头像上传
- ❌ 在用户列表和详情中显示头像

---

## 📅 开发计划

### 第一阶段：核心功能（5-7天）
1. **Day 1-2**: 超级登录功能
   - 后端：退出超级登录API、日志记录
   - 前端：超级登录按钮、横幅组件、状态管理

2. **Day 3-5**: 权限管理系统
   - 后端：权限表、权限API
   - 前端：权限常量、权限组件、v-permission指令

3. **Day 6-7**: 用户层级管理
   - 后端：子用户API、树形结构API
   - 前端：树形表格、层级关系展示

### 第二阶段：重要功能（4-5天）
4. **Day 8-9**: 角色模板系统
   - 后端：角色模板配置、应用角色API
   - 前端：角色选择组件、模板应用

5. **Day 10-11**: 数据权限过滤
   - 后端：根据权限过滤数据
   - 前端：数据过滤工具、条件渲染

6. **Day 12**: 操作日志记录
   - 后端：日志表、日志API
   - 前端：日志查询页面

### 第三阶段：增强功能（3天）
7. **Day 13**: 用户配额管理
8. **Day 14**: 告警通知设置
9. **Day 15**: 用户头像上传

**总计**: 12-15天

---

## 🎯 开发优先级建议

### 立即开始（P0）
1. ✅ 超级登录功能 - 核心需求
2. ✅ 权限管理系统 - 基础设施
3. ✅ 用户层级管理 - 多租户核心

### 尽快实现（P1）
4. 角色模板系统 - 提升易用性
5. 数据权限过滤 - 数据安全
6. 操作日志记录 - 审计需求

### 后续优化（P2）
7. 用户配额管理 - 资源控制
8. 告警通知设置 - 用户体验
9. 用户头像上传 - 个性化

---

## 📝 数据库表设计

### 1. 权限表 (sys_permissions)
```sql
CREATE TABLE sys_permissions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  code VARCHAR(100) NOT NULL UNIQUE COMMENT '权限代码',
  name VARCHAR(100) NOT NULL COMMENT '权限名称',
  module VARCHAR(50) NOT NULL COMMENT '所属模块',
  description VARCHAR(500) COMMENT '权限描述',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_module (module)
) COMMENT='系统权限表';
```

### 2. 用户权限关联表 (sys_user_permissions)
```sql
CREATE TABLE sys_user_permissions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL COMMENT '用户ID',
  permission_id BIGINT NOT NULL COMMENT '权限ID',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_user_permission (user_id, permission_id),
  INDEX idx_user_id (user_id)
) COMMENT='用户权限关联表';
```

### 3. 超级登录日志表 (sys_super_login_logs)
```sql
CREATE TABLE sys_super_login_logs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  original_user_id BIGINT NOT NULL COMMENT '原用户ID',
  target_user_id BIGINT NOT NULL COMMENT '目标用户ID',
  login_at DATETIME NOT NULL COMMENT '登录时间',
  logout_at DATETIME COMMENT '退出时间',
  ip VARCHAR(50) COMMENT 'IP地址',
  user_agent VARCHAR(500) COMMENT '浏览器信息',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_original_user (original_user_id),
  INDEX idx_target_user (target_user_id),
  INDEX idx_login_at (login_at)
) COMMENT='超级登录日志表';
```

### 4. 操作日志表 (sys_operation_logs)
```sql
CREATE TABLE sys_operation_logs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL COMMENT '操作用户ID',
  operation_type VARCHAR(50) NOT NULL COMMENT '操作类型',
  operation_module VARCHAR(50) NOT NULL COMMENT '操作模块',
  operation_desc VARCHAR(500) COMMENT '操作描述',
  request_method VARCHAR(10) COMMENT '请求方法',
  request_url VARCHAR(500) COMMENT '请求URL',
  request_params TEXT COMMENT '请求参数',
  response_status INT COMMENT '响应状态码',
  ip VARCHAR(50) COMMENT 'IP地址',
  user_agent VARCHAR(500) COMMENT '浏览器信息',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user_id (user_id),
  INDEX idx_operation_type (operation_type),
  INDEX idx_created_at (created_at)
) COMMENT='操作日志表';
```

---

## 🔧 技术实现要点

### 1. 超级登录Token设计
```typescript
interface SuperLoginToken {
  access_token: string
  refresh_token: string
  user_id: number              // 当前登录的用户ID
  original_user_id: number     // 原用户ID
  is_super_login: boolean      // 是否超级登录模式
  super_login_at: string       // 超级登录时间
}
```

### 2. 权限检查中间件
```python
# 后端权限检查装饰器
def require_permission(permission: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if permission not in current_user.permissions:
                raise HTTPException(status_code=403, detail="没有权限")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### 3. 前端权限指令
```typescript
// directives/permission.ts
export const permission = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    const { value } = binding
    const permissions = useAuthStore().permissions
    
    if (value && !hasPermission(value, permissions)) {
      el.parentNode?.removeChild(el)
    }
  }
}

function hasPermission(value: string | string[], permissions: string[]): boolean {
  if (Array.isArray(value)) {
    return value.some(p => permissions.includes(p))
  }
  return permissions.includes(value)
}
```

---

## ✅ 验收标准

### 超级登录功能
- [ ] 上级用户可以超级登录到下级用户
- [ ] 超级登录后顶部显示提示横幅
- [ ] 可以正常退出超级登录
- [ ] 超级登录操作被记录到日志
- [ ] 非上下级关系不能超级登录

### 权限管理系统
- [ ] 可以为用户分配权限
- [ ] 权限立即生效，无需重新登录
- [ ] v-permission指令正常工作
- [ ] 路由守卫正确拦截无权限访问
- [ ] 按钮根据权限显示/隐藏

### 用户层级管理
- [ ] 用户列表以树形结构展示
- [ ] 可以创建子用户并指定父级
- [ ] 用户只能管理自己的下级用户
- [ ] 层级关系清晰可见

---

## 📚 参考文档

- [FRONTEND_PRD.md](./FRONTEND_PRD.md) - 前端PRD文档
- [Element Plus 文档](https://element-plus.org/)
- [Vue Router 权限控制](https://router.vuejs.org/guide/advanced/navigation-guards.html)
- [JWT 最佳实践](https://jwt.io/introduction)


