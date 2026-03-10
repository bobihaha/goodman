# 模块2: 用户管理模块 - 代码审查报告

**审查时间**: 2026-03-06
**优先级**: 🟠 HIGH
**审查状态**: ✅ 已完成

---

## 📋 审查范围

### 后端文件
- `app/api/v1/sys_user.py` - 用户管理API路由
- `app/services/sys_user_service.py` - 用户服务层
- `app/crud/sys_user_crud.py` - 数据库操作层
- `app/db/models/sys_user.py` - 用户数据模型

---

## 🔴 CRITICAL 问题

### 1. 用户删除未检查关联数据
**文件**: `app/services/sys_user_service.py:59-69`
**问题**: 删除用户时仅检查子用户，未检查卡片、项目等关联数据
**风险**:
- 数据孤岛：卡片owner_id指向不存在的用户
- 外键约束错误
- 业务数据丢失

**代码片段**:
```python
async def delete_user(cls, db: AsyncSession, operator: CurrentUser, user_id: int) -> bool:
    # 仅检查子用户
    child_count = await sys_user_crud.count_children(db, user_id)
    if child_count > 0:
        raise BusinessException(code=400, msg="该用户下有子用户，无法删除")

    return await sys_user_crud.delete(db, user_id)
```

**建议**: 检查所有关联数据
```python
# 检查卡片
from app.crud.iot_card_crud import iot_card_crud
card_count = await iot_card_crud.count_by_owner(db, user_id)
if card_count > 0:
    raise BusinessException(msg=f"该用户下有{card_count}张卡片，无法删除")

# 检查项目
from app.crud.project_crud import project_crud
project_count = await project_crud.count_by_user(db, user_id)
if project_count > 0:
    raise BusinessException(msg=f"该用户下有{project_count}个项目，无法删除")
```

---

### 2. 密码复杂度验证缺失
**文件**: `app/services/sys_user_service.py:16-42, 91-109`
**问题**: 创建用户、修改密码、重置密码时未验证密码强度
**风险**:
- 弱密码导致账户被破解
- 暴力破解攻击

**建议**: 添加密码复杂度验证
```python
import re

def validate_password_strength(password: str) -> bool:
    """密码必须包含大小写字母、数字，长度8-20位"""
    if len(password) < 8 or len(password) > 20:
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True

# 在创建/修改密码前调用
if not validate_password_strength(user_data.password):
    raise BusinessException(msg="密码必须包含大小写字母和数字，长度8-20位")
```

---

## 🟠 HIGH 问题

### 3. 账户名格式未验证
**文件**: `app/services/sys_user_service.py:16-18`
**问题**: 未验证账户名格式（长度、字符类型）
**风险**: 特殊字符导致SQL注入或显示异常

**建议**:
```python
import re

def validate_account(account: str) -> bool:
    """账户名：4-20位字母数字下划线"""
    return bool(re.match(r'^[a-zA-Z0-9_]{4,20}$', account))

if not validate_account(user_data.account):
    raise BusinessException(msg="账户名格式错误：4-20位字母数字下划线")
```

---

### 4. 手机号/邮箱格式未验证
**文件**: `app/services/sys_user_service.py:16-42`
**问题**: 创建用户时未验证手机号和邮箱格式
**风险**: 无效联系方式导致通知失败

**建议**:
```python
import re

def validate_phone(phone: str) -> bool:
    """中国大陆手机号"""
    return bool(re.match(r'^1[3-9]\d{9}$', phone))

def validate_email(email: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

if user_data.phone and not validate_phone(user_data.phone):
    raise BusinessException(msg="手机号格式错误")
if user_data.email and not validate_email(user_data.email):
    raise BusinessException(msg="邮箱格式错误")
```

---

### 5. 子用户配额检查时机不当
**文件**: `app/services/sys_user_service.py:132-144`
**问题**: 配额检查在事务外，存在并发竞态条件
**风险**: 高并发下可能超出配额限制

**建议**: 使用数据库锁
```python
from sqlalchemy import select
from app.db.models.sys_user import SysUserModel

# 使用 FOR UPDATE 锁定用户记录
stmt = select(SysUserModel).where(SysUserModel.id == operator.id).with_for_update()
user = (await db.execute(stmt)).scalar_one_or_none()

current_count = await sys_user_crud.count_children(db, operator.id)
if current_count >= max_sub_users:
    raise BusinessException(msg=f"子用户数量已达上限({max_sub_users}个)")
```

---

## 🟡 MEDIUM 问题

### 6. 权限检查逻辑复杂
**文件**: `app/services/sys_user_service.py:120-129`
**问题**: `_check_manage_permission` 逻辑嵌套复杂，难以维护
**建议**: 重构为策略模式
```python
@staticmethod
def _check_manage_permission(operator: CurrentUser, target: SysUserModel):
    # 自己管理自己
    if operator.id == target.id:
        return

    # 超管管理二级用户
    if operator.is_super_admin() and target.is_user():
        return

    # 二级用户管理自己的三级用户
    if operator.is_user() and target.is_sub_user() and target.parent_id == operator.id:
        return

    raise PermissionDeniedException()
```

---

### 7. 菜单分配逻辑耦合
**文件**: `app/services/sys_user_service.py:146-171`
**问题**: 用户服务直接操作菜单表，违反单一职责原则
**建议**: 提取到独立的菜单服务
```python
# 在 sys_menu_service.py 中
async def assign_menus_to_sub_user(db: AsyncSession, user_id: int, parent_id: int):
    """为三级用户分配菜单"""
    ...

# 在 sys_user_service.py 中调用
from app.services.sys_menu_service import sys_menu_service
await sys_menu_service.assign_menus_to_sub_user(db, user.id, parent_id)
```

---

### 8. 查询未使用索引优化
**文件**: `app/crud/sys_user_crud.py:21-38`
**问题**: `get_users_by_parent` 使用 LIKE 查询，未考虑全文索引
**建议**: 添加全文索引或使用 Elasticsearch

---

## 🟢 LOW 问题

### 9. 缺少操作日志
**问题**: 用户创建、删除、状态变更未记录操作日志
**建议**: 添加审计日志表

---

### 10. 密码修改未强制重新登录
**文件**: `app/services/sys_user_service.py:91-99`
**问题**: 修改密码后旧token仍然有效
**建议**: 修改密码后清除Redis中的token

---

## ✅ 优点

1. ✅ 三级用户体系设计清晰
2. ✅ 权限隔离严格（parent_id过滤）
3. ✅ 密码使用bcrypt加密
4. ✅ 软删除机制（is_deleted）
5. ✅ 子用户配额控制

---

## 📊 问题统计

| 级别 | 数量 | 必须修复 |
|------|------|----------|
| 🔴 CRITICAL | 2 | ✅ 是 |
| 🟠 HIGH | 3 | ✅ 建议 |
| 🟡 MEDIUM | 3 | ⚠️ 可选 |
| 🟢 LOW | 2 | ❌ 否 |

---

## 🔧 修复优先级

1. **立即修复**:
   - 用户删除关联数据检查
   - 密码复杂度验证

2. **本周修复**:
   - 账户名格式验证
   - 手机号/邮箱格式验证
   - 子用户配额并发控制

3. **下次迭代**:
   - 权限检查逻辑重构
   - 菜单分配解耦
   - 查询性能优化
