# 卡片列表功能完善 - 更新说明

## 更新时间
2026-02-11

## 功能概述
完善卡片列表功能，添加缺失字段，支持通过粘贴ICCID进行批量操作。

## 一、数据库变更

### 1. 新增字段
在 `iot_cards` 表中添加以下字段：

- `card_type`: 卡片类型（single=单卡，pool=流量池卡）
  - 单卡：达量就停机，没有流量池功能
  - 流量池卡：可以共享流量池流量
  
- `data_used_month`: 本月已用流量（MB）

### 2. 迁移脚本
执行脚本：`scripts/add_card_type_fields.sql`

```bash
mysql -u root -p iot_card_platform < scripts/add_card_type_fields.sql
```

## 二、后端变更

### 1. 模型更新 (`app/db/models/iot_card.py`)
- 添加 `CardType` 枚举类型
- 添加 `card_type` 字段
- 添加 `data_used_month` 字段
- 更新 `to_dict()` 方法返回新字段

### 2. API接口新增 (`app/api/v1/iot_card.py`)
新增以下批量操作接口，支持通过ICCID列表操作：

- `POST /cards/batch/transfer-by-iccids` - 通过ICCID批量划拨
- `POST /cards/batch/remark-by-iccids` - 通过ICCID批量备注
- `POST /cards/batch/renew-by-iccids` - 通过ICCID批量续费
- `POST /cards/batch/suspend-by-iccids` - 通过ICCID批量停机
- `POST /cards/batch/resume-by-iccids` - 通过ICCID批量复机

### 3. 服务层更新 (`app/services/iot_card_service.py`)
实现以上5个批量操作方法，支持：
- 输入ICCID列表
- 返回成功/失败详情
- 权限验证
- 事务处理

## 三、前端变更

### 1. 类型定义更新 (`frontend/src/types/card.d.ts`)
- 添加 `CardType` 类型
- 在 `Card` 接口中添加 `card_type`、`card_type_name`、`data_used_month` 字段

### 2. API接口更新 (`frontend/src/api/modules/card.ts`)
添加新的批量操作API方法：
- `batchTransferByIccids()`
- `batchRemarkByIccids()`
- `batchRenewByIccids()`
- `batchSuspendByIccids()`
- `batchResumeByIccids()`

### 3. 卡片列表页面更新 (`frontend/src/views/cards/list/index.vue`)

#### 新增列：
1. **卡片类型** - 显示"单卡"或"流量池卡"
2. **本月用量** - 显示本月已用流量
3. **套餐总量** - 显示套餐总流量
4. **已用量** - 显示累计已用流量
5. **测试期** - 显示测试期到期日
6. **沉默期** - 显示沉默期到期日
7. **激活日期** - 显示激活日期
8. **出库日期** - 显示出库日期

#### 操作栏调整：
- 保留"批量查询"按钮
- 所有批量操作按钮不再依赖勾选，直接打开对话框输入ICCID

### 4. 新增对话框组件

#### BatchQueryDialog.vue
- 支持粘贴多个ICCID（每行一个或逗号分隔）
- 显示查询结果（找到的卡片 + 未找到的ICCID）
- 支持复制未找到的ICCID

#### BatchRenewDialog.vue
- 支持粘贴ICCID批量续费
- 选择续费月数（1/3/6/12个月）
- 显示成功/失败详情

#### BatchSuspendDialog.vue
- 支持粘贴ICCID批量停机
- 可选填写停机原因
- 显示成功/失败详情

#### BatchResumeDialog.vue
- 支持粘贴ICCID批量复机
- 显示成功/失败详情

#### 已有对话框更新
- `BatchTransferDialog.vue` - 已支持粘贴ICCID
- `BatchRemarkDialog.vue` - 已支持粘贴ICCID

## 四、使用说明

### 1. 批量操作流程
1. 点击对应的批量操作按钮（划拨/备注/续费/停机/复机）
2. 在弹出的对话框中粘贴ICCID列表
   - 支持每行一个ICCID
   - 支持逗号分隔
   - 自动去重
3. 填写必要参数（如划拨目标用户、备注内容等）
4. 点击确认执行操作
5. 查看操作结果（成功/失败详情）

### 2. 卡片类型说明
- **单卡**：独立计费，达量停机，不共享流量池
- **流量池卡**：可以加入流量池，共享流量池流量

### 3. 流量字段说明
- **本月用量**：当前计费周期内的已用流量
- **套餐总量**：卡片套餐的总流量额度
- **已用量**：累计已用流量（可能跨多个计费周期）

## 五、注意事项

1. **数据库迁移**
   - 必须先执行数据库迁移脚本
   - 迁移会自动为现有卡片设置类型（在池中=流量池卡，否则=单卡）

2. **权限控制**
   - 子用户无权执行划拨操作
   - 用户只能操作自己的卡片
   - 超级管理员可以操作所有卡片

3. **批量操作限制**
   - 单次最多操作10000张卡片
   - 操作失败的卡片会显示具体原因
   - 支持复制失败的ICCID继续处理

4. **性能优化**
   - 批量操作使用事务处理
   - 大批量操作建议分批执行
   - 操作结果实时反馈

## 六、测试建议

1. **功能测试**
   - 测试各个批量操作功能
   - 测试ICCID解析（换行、逗号、去重）
   - 测试权限控制

2. **边界测试**
   - 测试空ICCID列表
   - 测试超过10000个ICCID
   - 测试不存在的ICCID
   - 测试无权限的ICCID

3. **UI测试**
   - 验证新增列显示正确
   - 验证对话框交互流畅
   - 验证成功/失败结果展示

## 七、后续优化建议

1. 添加批量操作进度条（大批量时）
2. 支持导出批量操作结果
3. 添加批量操作历史记录
4. 优化大批量操作性能（异步队列）

