# 用户管理模块配置文档

## 二级用户默认配置

### 1. 默认权限模块

创建二级用户时，系统自动分配以下模块的所有权限：

| 模块代码 | 模块名称 | 说明 |
|---------|---------|------|
| `dashboard` | 仪表盘 | 数据概览和统计 |
| `user` | 客户管理 | 子用户管理 |
| `card` | 卡片管理 | 物联网卡管理 |
| `package` | 续费管理 | 套餐和续费 |
| `pool` | 流量池管理 | 流量池操作 |
| `system` | 设置 | 系统配置 |

**不包含的模块**：
- `stock` - 库存管理（仅超级管理员）
- `supplier` - 供应商管理（仅超级管理员）
- `suspend` - 停卡策略（仅超级管理员）

### 2. 默认菜单

创建二级用户时，系统自动分配以下菜单：

| 菜单代码 | 菜单名称 |
|---------|---------|
| `dashboard` | 仪表盘 |
| `users` | 客户管理 |
| `cards` | 卡片管理 |
| `renewal` | 续费管理 |
| `pools` | 流量池管理 |
| `system_config` | 系统配置 |

### 3. 默认通知设置

```json
{
  "alert_notify": {
    "sms": true,
    "email": true
  }
}
```

- **短信通知**：默认开启
- **邮件通知**：默认开启

### 4. 默认配额设置

```json
{
  "quota": {
    "max_cards": 100,
    "max_sub_users": 5,
    "pool_stop_threshold": 100
  }
}
```

| 配置项 | 默认值 | 说明 |
|-------|-------|------|
| `max_cards` | 100 | 最大卡片数量 |
| `max_sub_users` | 5 | 最大子用户数量 |
| `pool_stop_threshold` | 100 | 流量池停卡阈值（%） |

**停卡阈值说明**：
- 当流量池用量达到此阈值时，池内所有卡片将被自动停卡
- 默认值 100% 表示用完才停卡
- 可设置范围：50% - 200%

## 三级用户默认配置

### 1. 权限继承

三级用户（子用户）自动继承父用户（二级用户）的所有菜单权限，并额外添加：

| 菜单代码 | 菜单名称 |
|---------|---------|
| `projects` | 项目管理 |

### 2. 通知和配额

三级用户的通知设置和配额设置与二级用户相同。

## 实现位置

### 后端

**文件**: `app/services/sys_user_service.py`

**关键方法**：
- `_assign_default_permissions_for_user()` - 分配默认权限
- `_assign_default_menus_for_user()` - 分配默认菜单
- `_assign_default_menus_for_sub_user()` - 分配子用户菜单

**Schema**: `app/schemas/sys_user.py`
```python
class UserCreate(BaseModel):
    alert_notify: Optional[Dict[str, Any]] = Field(
        default={"sms": True, "email": True}
    )
    quota: Optional[Dict[str, Any]] = Field(
        default={
            "max_cards": 100,
            "max_sub_users": 5,
            "pool_stop_threshold": 100
        }
    )
```

### 前端

**文件**: `frontend/src/views/users/components/UserFormDialog.vue`

**默认值设置**：
```typescript
const formData = reactive<UserCreateRequest>({
  alert_notify: {
    sms: true,
    email: true
  },
  quota: {
    max_cards: 100,
    max_sub_users: 5,
    pool_stop_threshold: 100
  }
})
```

## 注意事项

1. **权限分配失败不影响用户创建**：如果权限或菜单分配失败，系统会记录警告日志但不会阻止用户创建
2. **前端缓存**：修改默认值后需要清除浏览器缓存或硬刷新（Ctrl+Shift+R / Cmd+Shift+R）
3. **数据库依赖**：权限和菜单分配依赖于数据库中已存在的权限和菜单数据
