# 流量池模块修改说明 - 自动组池

## 📋 修改内容

根据新的业务需求，流量池模块已从"手动创建+自动创建"改为"仅支持自动组池"。

### 1. 组池规则变更

**旧规则**：
- ✅ 支持手动创建流量池
- ✅ 支持自动组池（根据套餐package_id）

**新规则**：
- ❌ 删除手动创建流量池功能
- ✅ 只支持自动组池
- ✅ 组池条件：
  - 卡类型是流量池卡
  - 是月包套餐（period_type = 'monthly'）
  - 相同销售套餐ID（sale_package_id）
  - 激活后自动组池

### 2. 前端修改清单

#### 2.1 类型定义修改 (`types/pool.d.ts`)

**删除**：
- `PoolType` 类型（manual/auto）
- `PoolFormData` 接口（创建流量池表单）
- `pool_type` 字段
- `package_id` 字段

**新增**：
- `PoolUpdateData` 接口（只能修改告警阈值、停卡阈值、备注）
- `sale_package_id` 字段（销售套餐ID，组池依据）
- `sale_package_name` 字段（销售套餐名称）

**修改后的 Pool 接口**：
```typescript
export interface Pool {
  id: number
  name: string
  user_id: number
  sale_package_id: number        // 销售套餐ID（组池依据）
  carrier: Carrier
  flow_size: number
  period_type: PeriodType        // 固定为 monthly
  card_count: number
  data_total: number
  data_used: number
  data_remaining: number
  usage_percent: number
  alert_threshold?: number
  stop_threshold?: number
  is_alert: boolean
  status: PoolStatus
  remark?: string
  created_at: string
  updated_at?: string
  user_name?: string
  sale_package_name?: string     // 销售套餐名称
}
```

#### 2.2 API接口修改 (`api/modules/pool.ts`)

**删除**：
- `createPool()` - 创建流量池接口

**保留**：
- `updatePool()` - 更新流量池（只能修改告警阈值、停卡阈值、备注）
- 其他所有接口保持不变

#### 2.3 常量定义修改 (`constants/pool.ts`)

**删除**：
- `POOL_TYPE_MAP` - 流量池类型映射
- `POOL_TYPE_OPTIONS` - 流量池类型选项

#### 2.4 流量池列表页面修改 (`views/pools/list/index.vue`)

**搜索栏修改**：
- ❌ 删除"周期类型"筛选（固定为月包）
- ❌ 删除"流量池类型"筛选（只有自动组池）
- ✅ 新增"销售套餐ID"筛选

**表格列修改**：
- ❌ 删除"周期"列（固定为月包）
- ❌ 删除"类型"列（只有自动组池）
- ✅ 新增"销售套餐ID"列
- ✅ 新增"销售套餐"列（显示套餐名称）

**操作按钮修改**：
- ❌ 删除"创建流量池"按钮
- ✅ 保留"编辑"按钮（只能修改阈值和备注）
- ✅ 保留"添加卡片"、"充值"、"启用/禁用"等按钮

**标题修改**：
- 从"流量池列表"改为"流量池列表（自动组池）"

#### 2.5 流量池表单对话框修改 (`components/PoolFormDialog.vue`)

**功能变更**：
- ❌ 删除创建流量池功能
- ✅ 只保留编辑功能（修改告警阈值、停卡阈值、备注）

**表单字段**：
- ❌ 删除"流量池名称"字段
- ❌ 删除"运营商"字段
- ❌ 删除"单卡流量"字段
- ❌ 删除"周期类型"字段
- ✅ 保留"告警阈值"字段
- ✅ 保留"停卡阈值"字段
- ✅ 保留"备注"字段

**新增说明**：
- 添加提示信息："流量池由系统自动创建，只能修改告警阈值、停卡阈值和备注"

### 3. 后端需要实现的逻辑

#### 3.1 自动组池触发时机

**触发条件**：
```python
# 卡片激活时触发
if card.status == 'activated' and card.is_pool_card and card.period_type == 'monthly':
    # 自动组池
    auto_create_or_join_pool(card)
```

#### 3.2 自动组池逻辑

```python
def auto_create_or_join_pool(card: Card):
    """
    自动组池逻辑
    
    规则：
    1. 卡类型是流量池卡（is_pool_card = True）
    2. 是月包套餐（period_type = 'monthly'）
    3. 相同销售套餐ID（sale_package_id）
    4. 激活后自动组池
    """
    # 查找是否已存在相同销售套餐ID的流量池
    pool = db.query(TrafficPool).filter(
        TrafficPool.user_id == card.user_id,
        TrafficPool.sale_package_id == card.sale_package_id,
        TrafficPool.status == 'enable'
    ).first()
    
    if pool:
        # 已存在流量池，加入该流量池
        add_card_to_pool(pool.id, card.id)
    else:
        # 不存在流量池，创建新流量池
        sale_package = db.query(SalePackage).filter(
            SalePackage.id == card.sale_package_id
        ).first()
        
        pool_name = f"{sale_package.name}-流量池-{datetime.now().strftime('%Y%m%d')}"
        
        new_pool = TrafficPool(
            name=pool_name,
            user_id=card.user_id,
            sale_package_id=card.sale_package_id,
            carrier=card.carrier,
            flow_size=card.flow_size,
            period_type='monthly',
            alert_threshold=80,
            stop_threshold=100,
            status='enable'
        )
        db.add(new_pool)
        db.commit()
        
        # 将卡片加入新创建的流量池
        add_card_to_pool(new_pool.id, card.id)
```

#### 3.3 流量池命名规则

**格式**：`{销售套餐名称}-流量池-{创建日期}`

**示例**：
- `移动1G月包-流量池-20260210`
- `联通2G月包-流量池-20260210`

#### 3.4 数据库表结构调整

**traffic_pools 表需要调整的字段**：

```sql
ALTER TABLE traffic_pools
  DROP COLUMN pool_type,           -- 删除流量池类型字段
  DROP COLUMN package_id,          -- 删除套餐ID字段
  ADD COLUMN sale_package_id BIGINT NOT NULL COMMENT '销售套餐ID',
  ADD COLUMN sale_package_name VARCHAR(100) COMMENT '销售套餐名称',
  ADD INDEX idx_sale_package_id (sale_package_id);
```

**iot_cards 表需要的字段**：

```sql
-- 确保卡片表有以下字段
ALTER TABLE iot_cards
  ADD COLUMN is_pool_card BOOLEAN DEFAULT FALSE COMMENT '是否为流量池卡',
  ADD INDEX idx_is_pool_card (is_pool_card);
```

### 4. 前端查询参数变更

**旧的查询参数**：
```typescript
{
  name?: string
  carrier?: Carrier
  period_type?: PeriodType      // 删除
  pool_type?: PoolType           // 删除
  status?: PoolStatus
}
```

**新的查询参数**：
```typescript
{
  name?: string
  carrier?: Carrier
  sale_package_id?: number       // 新增
  status?: PoolStatus
}
```

### 5. 用户操作流程变更

#### 旧流程：
1. 用户手动创建流量池
2. 用户手动添加卡片到流量池
3. 或者：卡片激活时自动加入流量池（如果启用了自动组池）

#### 新流程：
1. ✅ 卡片激活时，系统自动判断是否为流量池卡
2. ✅ 如果是流量池卡且是月包，自动查找或创建流量池
3. ✅ 自动将卡片加入流量池
4. ✅ 用户只能：
   - 查看流量池列表
   - 编辑流量池（修改阈值和备注）
   - 手动添加/移除卡片
   - 充值加油包
   - 启用/禁用流量池

### 6. 界面变化对比

#### 搜索栏
**之前**：
```
流量池名称 | 运营商 | 周期类型 | 流量池类型 | 状态
```

**现在**：
```
流量池名称 | 运营商 | 销售套餐ID | 状态
```

#### 表格列
**之前**：
```
ID | 名称 | 运营商 | 单卡流量 | 周期 | 类型 | 卡片数 | 流量使用情况 | 告警阈值 | 状态 | 操作
```

**现在**：
```
ID | 名称 | 运营商 | 单卡流量 | 销售套餐ID | 销售套餐 | 卡片数 | 流量使用情况 | 告警阈值 | 状态 | 操作
```

#### 操作按钮
**之前**：
```
[创建流量池] [导出]
```

**现在**：
```
[导出]
```

### 7. 测试要点

#### 7.1 自动组池测试
- [ ] 激活流量池卡（月包），验证是否自动创建流量池
- [ ] 激活第二张相同销售套餐的卡，验证是否加入已有流量池
- [ ] 激活非流量池卡，验证不会创建流量池
- [ ] 激活年包流量池卡，验证不会创建流量池

#### 7.2 流量池管理测试
- [ ] 查看流量池列表
- [ ] 按销售套餐ID筛选
- [ ] 编辑流量池（修改阈值和备注）
- [ ] 手动添加卡片到流量池
- [ ] 从流量池移除卡片
- [ ] 充值加油包
- [ ] 启用/禁用流量池

#### 7.3 边界情况测试
- [ ] 同一用户多个相同销售套餐的流量池
- [ ] 不同用户相同销售套餐的流量池（应该分开）
- [ ] 流量池满后继续添加卡片
- [ ] 删除流量池中的所有卡片

### 8. 注意事项

1. **数据迁移**：
   - 如果已有手动创建的流量池，需要迁移数据
   - 为现有流量池补充 `sale_package_id` 字段

2. **兼容性**：
   - 确保后端API返回的数据包含 `sale_package_id` 和 `sale_package_name`
   - 前端已删除对 `pool_type` 和 `package_id` 的依赖

3. **性能优化**：
   - 自动组池时需要加锁，避免并发创建重复流量池
   - 建议使用分布式锁或数据库唯一索引

4. **用户体验**：
   - 在卡片激活成功后，提示用户已自动加入流量池
   - 在流量池列表中显示流量池的创建方式（自动）

## 📝 总结

本次修改将流量池从"手动+自动"模式改为"纯自动"模式，简化了用户操作流程，提高了系统自动化程度。

**核心变化**：
- ❌ 删除手动创建流量池功能
- ✅ 卡片激活时自动组池
- ✅ 组池依据：流量池卡 + 月包 + 相同销售套餐ID
- ✅ 用户只能编辑流量池配置，不能创建

**前端修改文件**：
- `types/pool.d.ts` - 类型定义
- `api/modules/pool.ts` - API接口
- `constants/pool.ts` - 常量定义
- `views/pools/list/index.vue` - 列表页面
- `views/pools/list/components/PoolFormDialog.vue` - 表单对话框

**后端需要实现**：
- 卡片激活时的自动组池逻辑
- 流量池表结构调整
- API接口返回 `sale_package_id` 和 `sale_package_name`






