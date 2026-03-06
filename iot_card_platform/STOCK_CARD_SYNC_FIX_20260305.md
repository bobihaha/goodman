# 库存卡状态同步问题修复 (2026-03-05)

## 问题描述

卡片 89860625540001749903 存在以下问题：
- 状态：stock（库存）
- 已用流量：38 MB（说明已激活使用）
- user_id：NULL（未分配给用户）
- activated_at：NULL
- expired_at：NULL
- 数据同步时间：2026-02-25（已过期）

## 根本原因

1. **库存卡被排除在同步之外** - `sync_service.py` 只同步 `user_id != NULL` 的卡片
2. **状态转换规则不处理 stock 状态** - `card_status_service.py` 只处理 testing/silent/activated
3. **流量池统计未自动更新** - 流量同步后没有触发流量池统计更新

## 修复内容

### 1. 扩展状态转换规则

**文件**: `app/services/card_status_service.py`

**改动**: 添加规则0处理 stock 状态
```python
# 规则0: stock → testing/silent/activated
if card.status == CardStatus.stock:
    if card.test_expire_date and today <= card.test_expire_date:
        card.status = CardStatus.testing
    elif card.silent_expire_date and today <= card.silent_expire_date:
        card.status = CardStatus.silent
    elif card.data_used > 0:
        card.status = CardStatus.activated
        card.activated_at = today
        card.expired_at = calculate_expiry_date(...)
```

### 2. 修改同步逻辑

**文件**: `app/services/sync_service.py`

**改动**: 允许同步已激活的库存卡
```python
# 第7行：添加导入
from sqlalchemy import select, or_, and_

# 第561-567行：修改过滤条件
query = query.where(
    or_(
        IotCardModel.user_id.isnot(None),
        and_(IotCardModel.user_id.is_(None), IotCardModel.status == CardStatus.activated)
    )
)
```

### 3. 流量池统计自动更新

**文件**: `app/services/sync_service.py`

**改动**: 流量同步后更新流量池统计
```python
# 第136-145行：添加流量池统计更新
pool_ids = set()
for card in cards:
    if card.pool_id:
        pool_ids.add(card.pool_id)

if pool_ids:
    from app.crud.pool_crud import pool_crud
    for pool_id in pool_ids:
        await pool_crud.update_stats(db, pool_id)
```

### 4. 手动修复问题卡片

**SQL**:
```sql
UPDATE iot_cards
SET status = 'activated',
    activated_at = '2026-02-25',
    expired_at = DATE_ADD('2026-02-25', INTERVAL 12 MONTH)
WHERE iccid = '89860625540001749903';
```

### 5. 手动更新流量池统计

**SQL**:
```sql
UPDATE traffic_pools tp
SET
    card_count = (SELECT COUNT(*) FROM iot_cards WHERE pool_id = tp.id AND is_deleted = 0),
    data_total = (SELECT COALESCE(SUM(data_total), 0) FROM iot_cards WHERE pool_id = tp.id AND is_deleted = 0),
    data_used = (SELECT COALESCE(SUM(data_used), 0) FROM iot_cards WHERE pool_id = tp.id AND is_deleted = 0)
WHERE is_deleted = 0;
```

## 验证结果

**卡片修复**:
- 状态：stock → activated ✅
- 激活日期：2026-02-25 ✅
- 到期日期：2027-02-25 ✅

**流量池统计**:
| pool_id | 卡数 | 总流量 | 已用流量 |
|---------|------|--------|---------|
| 1 | 1 | 5120 MB | 3076 MB |
| 7 | 1 | 5120 MB | 815 MB |
| 8 | 3 | 11264 MB | 7070 MB |
| 9 | 3 | 6144 MB | 157 MB |
| 10 | 1 | 1024 MB | 38 MB |

## 影响范围

- 已激活的库存卡现在会被定时任务同步
- 流量池统计在每次流量同步后自动更新
- 库存卡有流量使用时会自动转为 activated 状态

## 部署说明

重启后端服务后，定时任务会在5分钟内自动同步最新流量并更新流量池统计。
