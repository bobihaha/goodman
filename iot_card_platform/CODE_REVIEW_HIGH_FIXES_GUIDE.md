# HIGH优先级问题修复指南

**创建时间**: 2026-03-06
**问题总数**: 25个

---

## 修复批次规划

### 批次1: 批量操作限制 (7个) - 防止系统过载
1. 卡片管理 - 批量操作无数量限制
2. 出入库 - 批量查询无数量限制
3. 同步服务 - 批量同步无数量限制
4. 停复机 - 批量操作无数量限制

### 批次2: 输入验证 (5个) - 数据质量
5. 用户管理 - 账户名格式未验证
6. 用户管理 - 手机号/邮箱格式未验证
7. 套餐管理 - 价格验证缺失

### 批次3: 权限和安全 (6个)
8. 卡片管理 - 划拨未验证目标用户状态
9. 同步服务 - 单卡同步权限校验不足
10. 权限管理 - 删除权限未检查关联
11. 权限管理 - 权限分配循环验证

### 批次4: 性能优化 (4个)
12. 套餐管理 - N+1查询问题严重
13. 卡片管理 - 关键词搜索性能问题
14. 套餐管理 - 规格三要素未强制唯一

### 批次5: 其他重要问题 (3个)
15. 认证模块 - 超级登录缺少操作审计
16. 供应商管理 - API密钥明文存储
17. 出入库 - 回收操作不可逆

---

## 详细修复方案

### 批次1: 批量操作限制

#### 1. 卡片管理 - 批量操作限制
**文件**: `app/services/iot_card_service.py`
**位置**: 批量更新备注、批量划拨
**修复**:
```python
MAX_BATCH_SIZE = 1000

# 在批量操作开始前添加
if len(card_ids) > MAX_BATCH_SIZE:
    raise BusinessException(msg=f"单次最多操作{MAX_BATCH_SIZE}张卡片")
```

#### 2. 出入库 - 批量查询限制
**文件**: `app/api/v1/stock.py`
**修复**: 添加page_size最大值限制

#### 3. 同步服务 - 批量同步限制
**文件**: `app/services/sync_service.py`
**修复**:
```python
MAX_SYNC_BATCH = 1000

cards = await self._get_cards_for_sync(db, supplier_id, iccid_list)
if len(cards) > MAX_SYNC_BATCH:
    raise BusinessException(msg=f"单次最多同步{MAX_SYNC_BATCH}张卡片")
```

#### 4. 停复机 - 批量操作限制
**文件**: `app/services/suspend_service.py`
**修复**:
```python
MAX_BATCH_SIZE = 500

if len(data.card_ids) > MAX_BATCH_SIZE:
    raise BusinessException(msg=f"单次最多操作{MAX_BATCH_SIZE}张卡片")
```

---

### 批次2: 输入验证

#### 5. 用户管理 - 账户名格式验证
**文件**: `app/utils/const.py`, `app/services/sys_user_service.py`
**修复**:
```python
# const.py
ACCOUNT_PATTERN = re.compile(r'^[a-zA-Z0-9_]{4,20}$')

def validate_account(account: str) -> bool:
    return bool(ACCOUNT_PATTERN.match(account))

# sys_user_service.py
from app.utils.const import validate_account

if not validate_account(user_data.account):
    raise BusinessException(msg="账户名格式错误：4-20位字母数字下划线")
```

#### 6. 手机号/邮箱格式验证
**文件**: `app/utils/const.py`
**修复**:
```python
PHONE_PATTERN = re.compile(r'^1[3-9]\d{9}$')
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def validate_phone(phone: str) -> bool:
    return bool(PHONE_PATTERN.match(phone)) if phone else True

def validate_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email)) if email else True
```

#### 7. 套餐管理 - 价格验证
**文件**: `app/services/package_service.py`
**修复**:
```python
if data.price is not None and data.price < 0:
    raise BusinessException(msg="价格不能为负数")
if data.cost is not None and data.cost < 0:
    raise BusinessException(msg="成本不能为负数")
```

---

### 批次3: 权限和安全

#### 8. 卡片划拨 - 验证目标用户状态
**文件**: `app/services/iot_card_service.py`
**修复**:
```python
from app.db.models.sys_user import UserStatus

if target_user.status != UserStatus.enable:
    raise BusinessException(msg="目标用户已被禁用")
```

#### 9. 单卡同步 - 权限校验
**文件**: `app/services/sync_service.py`
**修复**:
```python
from app.schemas.auth import UserLevel

# 在sync_single_card中添加
if current_user and current_user.user_level != UserLevel.SUPER_ADMIN.value:
    if card.user_id != current_user.id:
        raise BusinessException(code=403, msg="无权同步此卡片")
```

#### 10. 删除权限 - 检查关联
**文件**: `app/services/permission_service.py`
**修复**:
```python
user_count = await user_permission_crud.count_users_with_permission(db, permission_id)
if user_count > 0:
    raise BusinessException(msg=f"该权限被{user_count}个用户使用，无法删除")
```

#### 11. 权限分配 - 批量验证
**文件**: `app/services/permission_service.py`
**修复**:
```python
from sqlalchemy import select
stmt = select(PermissionModel.id).where(PermissionModel.id.in_(permission_ids))
valid_ids = set((await db.execute(stmt)).scalars().all())
invalid = set(permission_ids) - valid_ids
if invalid:
    raise BusinessException(msg=f"权限ID不存在: {invalid}")
```

---

## 修复进度跟踪

- [ ] 批次1: 批量操作限制 (4个)
- [ ] 批次2: 输入验证 (3个)
- [ ] 批次3: 权限和安全 (4个)
- [ ] 批次4: 性能优化 (3个)
- [ ] 批次5: 其他重要问题 (3个)

**总计**: 0/17 已修复
