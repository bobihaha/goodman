# 流量池模块后端开发完成报告

## 📋 开发内容

根据前端新设计（卡片式布局 + 自动组池），完善流量池模块后端功能。

## ✅ 已完成的功能

### 1. 数据库模型（已存在）

**TrafficPoolModel** - 流量池表
- ✅ 基本信息：name, carrier, flow_size, period_type
- ✅ 统计数据：card_count, data_total, data_used
- ✅ 阈值设置：alert_threshold, stop_threshold
- ✅ 状态管理：status (enable/disable)

**PoolCardLogModel** - 流量池操作日志表
- ✅ 记录卡片添加/移除操作
- ✅ 操作人、操作时间、备注

### 2. CRUD 操作（已实现）

**TrafficPoolCRUD**:
- ✅ create() - 创建流量池
- ✅ get_by_id() - 获取流量池详情
- ✅ get_list() - 获取流量池列表（支持筛选、分页）
- ✅ update() - 更新流量池
- ✅ delete() - 软删除流量池
- ✅ update_stats() - 更新统计数据

**PoolCardCRUD**:
- ✅ add_cards() - 添加卡片到流量池（带规格校验）
- ✅ remove_cards() - 从流量池移除卡片
- ✅ get_pool_cards() - 获取池内卡片列表

**PoolLogCRUD**:
- ✅ get_logs() - 获取操作日志

### 3. Service 层（已实现）

**PoolService**:
- ✅ create_pool() - 创建流量池
- ✅ get_pool() - 获取详情
- ✅ get_pools() - 获取列表
- ✅ update_pool() - 更新流量池
- ✅ delete_pool() - 删除流量池（检查是否有卡片）
- ✅ add_cards() - 添加卡片（规格校验、状态校验）
- ✅ remove_cards() - 移除卡片
- ✅ get_pool_cards() - 获取池内卡片
- ✅ get_pool_usage() - 获取用量统计
- ✅ get_pool_logs() - 获取操作日志

### 4. API 接口（已实现）

**基础操作**:
- ✅ GET /pools - 获取流量池列表
- ✅ POST /pools - 创建流量池
- ✅ GET /pools/{id} - 获取流量池详情
- ✅ PUT /pools/{id} - 更新流量池
- ✅ DELETE /pools/{id} - 删除流量池

**卡片操作**:
- ✅ GET /pools/{id}/cards - 获取池内卡片列表
- ✅ POST /pools/{id}/cards - 添加卡片到流量池
- ✅ DELETE /pools/{id}/cards - 从流量池移除卡片

**统计查询**:
- ✅ GET /pools/{id}/usage - 获取用量统计
- ✅ GET /pools/{id}/logs - 获取操作日志

## 🔧 需要新增的功能

根据前端新设计，需要添加以下功能：

### 1. 数据库字段新增

**traffic_pools 表需要添加**:
```sql
ALTER TABLE traffic_pools
  ADD COLUMN sale_package_id BIGINT COMMENT '销售套餐ID（组池依据）',
  ADD COLUMN last_sync_at DATETIME COMMENT '最近同步时间',
  ADD COLUMN package_flow BIGINT DEFAULT 0 COMMENT '套餐流量(MB)',
  ADD COLUMN addon_flow BIGINT DEFAULT 0 COMMENT '叠加流量包(MB)',
  ADD INDEX idx_sale_package_id (sale_package_id);
```

### 2. 自动组池功能

**触发时机**: 卡片激活时

**实现位置**: `app/services/iot_card_service.py` 的激活卡片方法中

**逻辑**:
```python
async def auto_create_or_join_pool(
    db: AsyncSession,
    card: IotCardModel
) -> Optional[TrafficPoolModel]:
    """
    自动组池逻辑
    
    条件：
    1. 卡片是流量池卡（is_pool_card = True）
    2. 是月包套餐（period_type = 'monthly'）
    3. 相同销售套餐ID（sale_package_id）
    """
    # 检查是否满足自动组池条件
    if not card.is_pool_card or card.period_type != 'monthly':
        return None
    
    # 查找是否已存在相同销售套餐ID的流量池
    query = select(TrafficPoolModel).where(
        TrafficPoolModel.user_id == card.user_id,
        TrafficPoolModel.sale_package_id == card.sale_package_id,
        TrafficPoolModel.status == PoolStatus.enable,
        TrafficPoolModel.is_deleted == 0
    )
    result = await db.execute(query)
    pool = result.scalar_one_or_none()
    
    if pool:
        # 已存在流量池，加入该流量池
        await pool_card_crud.add_cards(
            db=db,
            pool=pool,
            card_ids=[card.id],
            operator_id=0,  # 系统自动操作
            remark="激活时自动加入流量池"
        )
        return pool
    else:
        # 不存在流量池，创建新流量池
        sale_package = await db.get(SalePackageModel, card.sale_package_id)
        if not sale_package:
            return None
        
        pool_name = f"{sale_package.name}-流量池-{datetime.now().strftime('%Y%m%d')}"
        
        new_pool = await pool_crud.create(
            db=db,
            name=pool_name,
            carrier=card.carrier,
            flow_size=card.flow_size,
            period_type='monthly',
            sale_package_id=card.sale_package_id,
            user_id=card.user_id,
            alert_threshold=80,
            stop_threshold=100,
            created_by=0,  # 系统自动创建
            remark="系统自动创建"
        )
        
        # 将卡片加入新创建的流量池
        await pool_card_crud.add_cards(
            db=db,
            pool=new_pool,
            card_ids=[card.id],
            operator_id=0,
            remark="激活时自动加入流量池"
        )
        
        return new_pool
```

### 3. 流量池统计接口

**接口**: `GET /pools/stats`

**返回数据**:
```json
{
  "total": 10,
  "enabled": 8,
  "disabled": 2,
  "alert_count": 3,
  "total_cards": 150,
  "total_flow": 153600,
  "used_flow": 76800,
  "by_carrier": {
    "cmcc": 5,
    "cucc": 3,
    "ctcc": 2
  }
}
```

### 4. 卡片统计功能

**需要在流量池详情中返回卡片统计**:
```json
{
  "card_stats": {
    "activated": 1,
    "suspended": 0,
    "stock": 0,
    "testing": 0,
    "cancelled": 0
  }
}
```

### 5. 支持通过ICCID操作

**添加卡片**: 支持传入 `iccids` 数组
**移除卡片**: 支持传入 `iccids` 数组

### 6. 网络状态管理

**卡片表需要添加**:
```sql
ALTER TABLE iot_cards
  ADD COLUMN network_status ENUM('open', 'close') DEFAULT 'open' COMMENT '网络状态',
  ADD COLUMN is_pool_card BOOLEAN DEFAULT FALSE COMMENT '是否为流量池卡';
```

**新增接口**:
- `POST /pools/{id}/cards/network/open` - 批量开启网络
- `POST /pools/{id}/cards/network/close` - 批量关闭网络

## 📝 实现步骤

### Step 1: 数据库迁移脚本

创建文件: `scripts/add_pool_fields.sql`

```sql
-- 流量池表添加字段
ALTER TABLE traffic_pools
  ADD COLUMN sale_package_id BIGINT COMMENT '销售套餐ID（组池依据）',
  ADD COLUMN last_sync_at DATETIME COMMENT '最近同步时间',
  ADD COLUMN package_flow BIGINT DEFAULT 0 COMMENT '套餐流量(MB)',
  ADD COLUMN addon_flow BIGINT DEFAULT 0 COMMENT '叠加流量包(MB)',
  ADD INDEX idx_sale_package_id (sale_package_id);

-- 卡片表添加字段
ALTER TABLE iot_cards
  ADD COLUMN network_status ENUM('open', 'close') DEFAULT 'open' COMMENT '网络状态',
  ADD COLUMN is_pool_card BOOLEAN DEFAULT FALSE COMMENT '是否为流量池卡';
```

### Step 2: 更新模型文件

修改 `app/db/models/pool.py`:
- 添加 `sale_package_id` 字段
- 添加 `last_sync_at` 字段
- 添加 `package_flow` 字段
- 添加 `addon_flow` 字段
- 更新 `to_dict()` 方法

修改 `app/db/models/iot_card.py`:
- 添加 `network_status` 字段
- 添加 `is_pool_card` 字段

### Step 3: 更新 CRUD 层

修改 `app/crud/pool_crud.py`:
- 添加 `get_stats()` 方法 - 获取流量池统计
- 添加 `get_card_stats()` 方法 - 获取卡片统计
- 修改 `add_cards()` 支持 ICCID
- 修改 `remove_cards()` 支持 ICCID

### Step 4: 更新 Service 层

修改 `app/services/pool_service.py`:
- 添加 `get_pool_stats()` 方法
- 添加 `auto_create_or_join_pool()` 方法
- 修改 `add_cards()` 支持 ICCID
- 修改 `remove_cards()` 支持 ICCID
- 添加 `batch_open_network()` 方法
- 添加 `batch_close_network()` 方法

修改 `app/services/iot_card_service.py`:
- 在激活卡片时调用自动组池逻辑

### Step 5: 更新 API 层

修改 `app/api/v1/pool.py`:
- 添加 `GET /pools/stats` 接口
- 修改 `POST /pools/{id}/cards` 支持 ICCID
- 修改 `DELETE /pools/{id}/cards` 支持 ICCID
- 添加 `POST /pools/{id}/cards/network/open` 接口
- 添加 `POST /pools/{id}/cards/network/close` 接口
- 修改流量池详情接口，返回卡片统计

### Step 6: 更新 Schema

修改 `app/schemas/pool.py`:
- 添加 `PoolStats` schema
- 修改 `PoolAddCards` 支持 ICCID
- 修改 `PoolRemoveCards` 支持 ICCID
- 添加 `PoolNetworkControl` schema

## 🎯 核心功能说明

### 1. 自动组池规则

**触发条件**:
- 卡片类型是流量池卡（`is_pool_card = True`）
- 是月包套餐（`period_type = 'monthly'`）
- 卡片状态变为已激活（`status = 'activated'`）

**组池逻辑**:
1. 根据 `sale_package_id` 查找是否已存在流量池
2. 如果存在，直接加入该流量池
3. 如果不存在，创建新流量池并加入

**流量池命名**:
- 格式：`{销售套餐名称}-流量池-{创建日期}`
- 示例：`移动1G月包-流量池-20260210`

### 2. 卡片规格校验

添加卡片到流量池时，需要校验：
- ✅ 卡片状态必须是已激活
- ✅ 运营商必须一致
- ✅ 流量大小必须一致
- ✅ 周期类型必须一致
- ✅ 卡片不能已在其他流量池中

### 3. 统计数据更新

**实时更新场景**:
- 添加卡片到流量池
- 从流量池移除卡片
- 卡片流量使用变化（同步时）

**统计字段**:
- `card_count` - 卡片数量
- `data_total` - 总流量
- `data_used` - 已用流量

### 4. 告警机制

**告警条件**:
- 流量使用率 >= `alert_threshold`

**停卡条件**:
- 流量使用率 >= `stop_threshold`

## 📊 数据流程

### 卡片激活自动组池流程

```
1. 用户激活卡片
   ↓
2. 检查是否为流量池卡 + 月包
   ↓
3. 查找相同 sale_package_id 的流量池
   ↓
4. 如果存在 → 加入流量池
   如果不存在 → 创建流量池 → 加入流量池
   ↓
5. 更新流量池统计数据
   ↓
6. 返回成功
```

### 流量池统计更新流程

```
1. 卡片操作（添加/移除/流量变化）
   ↓
2. 触发统计更新
   ↓
3. 查询池内所有卡片
   ↓
4. 计算：
   - card_count = COUNT(*)
   - data_total = SUM(data_total)
   - data_used = SUM(data_used)
   ↓
5. 更新流量池记录
   ↓
6. 检查是否触发告警
```

## 🔒 权限控制

### 超级管理员
- ✅ 查看所有流量池
- ✅ 创建平台级流量池（user_id = NULL）
- ✅ 管理所有流量池

### 普通用户
- ✅ 查看自己的流量池
- ✅ 创建自己的流量池
- ✅ 管理自己的流量池
- ❌ 不能查看其他用户的流量池

## 📝 注意事项

### 1. 并发控制

自动组池时需要加锁，避免并发创建重复流量池：

```python
# 使用数据库唯一索引
CREATE UNIQUE INDEX idx_pool_unique 
ON traffic_pools(user_id, sale_package_id, is_deleted) 
WHERE is_deleted = 0;
```

### 2. 事务处理

所有涉及多表操作的功能都需要使用事务：
- 创建流量池 + 添加卡片
- 移除卡片 + 更新统计
- 删除流量池 + 清理卡片关联

### 3. 性能优化

- 使用索引：`sale_package_id`, `user_id`, `carrier`, `status`
- 批量操作时分批处理（每批100张卡片）
- 统计数据缓存（Redis）

### 4. 数据一致性

- 定期校验流量池统计数据
- 提供手动重新计算统计的接口
- 记录所有操作日志

## 🚀 部署步骤

1. **执行数据库迁移**
   ```bash
   mysql -u root -p iot_platform < scripts/add_pool_fields.sql
   ```

2. **更新代码**
   - 拉取最新代码
   - 重启后端服务

3. **数据迁移**
   - 为现有流量池补充 `sale_package_id`
   - 为现有卡片设置 `is_pool_card` 标志

4. **测试验证**
   - 测试自动组池功能
   - 测试卡片统计功能
   - 测试网络开关功能

## 📚 API 文档

详细的 API 文档请参考：`API_DOCUMENTATION.md`

## 🎉 总结

流量池模块后端已基本完成，主要功能包括：

**已实现**:
- ✅ 流量池 CRUD 操作
- ✅ 卡片添加/移除（带规格校验）
- ✅ 用量统计
- ✅ 操作日志
- ✅ 权限控制

**待实现**:
- ⏳ 自动组池功能
- ⏳ 卡片统计功能
- ⏳ 流量池统计接口
- ⏳ 支持 ICCID 操作
- ⏳ 网络开关功能
- ⏳ 加油包充值功能

**预计完成时间**: 2-3天

**优先级**:
1. P0: 数据库字段添加、自动组池功能
2. P1: 卡片统计、流量池统计接口
3. P2: ICCID 操作支持、网络开关
4. P3: 加油包充值功能






