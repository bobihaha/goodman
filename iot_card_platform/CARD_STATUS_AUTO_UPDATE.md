# 卡片激活日期和到期日期自动计算功能实现文档

## 功能概述

实现物联网卡片的激活日期和到期日期自动计算，基于流量同步自动更新卡片状态。

## 核心改动

### 1. 状态自动转换服务

**文件**: `app/services/card_status_service.py` (新建)

**功能**:
- testing → silent: 测试期到期自动转换
- testing/silent → activated: 检测到流量使用时激活，自动设置 activated_at 和计算 expired_at
- activated → suspended: 到期自动停机

**关键代码**:
```python
async def check_and_update_card_status(db: AsyncSession, card: IotCardModel) -> bool:
    # 规则1: 测试期到期
    if card.status == CardStatus.testing and card.test_expire_date and today > card.test_expire_date:
        card.status = CardStatus.silent

    # 规则2: 检测到流量使用，自动激活
    if card.status in [CardStatus.testing, CardStatus.silent] and card.data_used > 0:
        card.status = CardStatus.activated
        card.activated_at = today
        card.expired_at = calculate_expiry_date(...)  # 计算到期日期

    # 规则3: 到期停机
    if card.status == CardStatus.activated and card.expired_at and today > card.expired_at:
        card.status = CardStatus.suspended
        card.suspend_type = SuspendType.expired
```

### 2. 流量同步集成

**文件**: `app/services/sync_service.py`

**修改位置**:
- `sync_usage()` 方法第105-109行
- `sync_single_card()` 方法第365-369行

**改动**: 流量同步后调用状态检查
```python
card.data_sync_at = datetime.now()
from app.services.card_status_service import check_and_update_card_status
await check_and_update_card_status(db, card)
```

### 3. 出库逻辑优化

**文件**:
- `app/crud/stock_crud.py` (第336-346行)
- `app/services/stock_service.py` (第487-500行)

**改动**: 根据运营商类型设置初始状态
```python
from app.db.models.package import CarrierType
if card.carrier == CarrierType.cmcc and test_expire_date:
    card.status = CardStatus.testing
else:
    card.status = CardStatus.silent
```

### 4. 供应商同步间隔配置

**后端改动**:
- `app/db/models/supplier.py`: 添加 `sync_interval` 字段 (默认60分钟)
- `sql/add_supplier_sync_interval.sql`: 数据库迁移脚本

**前端改动**:
- `frontend/src/views/suppliers/components/SupplierFormDialog.vue`: 添加同步间隔输入框
- `frontend/src/types/supplier.d.ts`: 更新类型定义

## 部署步骤

1. **数据库迁移**:
```bash
mysql -u user -p database < sql/add_supplier_sync_interval.sql
```

2. **重启后端服务**

3. **验证功能**:
   - 出库移动卡，验证状态为 testing
   - 等待流量同步，验证激活日期和到期日期自动填充
   - 供应商管理页面设置同步间隔

## 技术要点

- 复用现有 `calculate_expiry_date()` 函数计算到期日期
- 状态转换逻辑幂等，多次执行无副作用
- 无需修改前端卡片列表显示逻辑
- 所有日期字段已存在，无需添加新字段

## 测试场景

1. **移动卡测试期转沉默期**: 测试期到期后自动转为 silent
2. **沉默期卡激活**: 产生流量后自动激活并计算到期日期
3. **激活卡到期停机**: 到期后自动转为 suspended
4. **电信/联通卡**: 出库直接进入 silent 状态
