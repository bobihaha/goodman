# 出库功能增强开发总结

## 📅 开发日期
2026-02-11

## 🎯 需求概述

增强出库功能，支持：
1. **套餐周期灵活配置**：月包（3/6/12/24/36/50/60个月）、年包（1/2/3/5/6年，360天/年）
2. **卡类型选择**：单卡（single）、流量池卡（pool），仅月包套餐显示
3. **出库日期管理**：出库日期、测试期、沉默期
4. **Excel批量出库**：支持固定格式Excel模板批量导入出库

## 📊 数据库变更

### 1. 新增字段

**iot_cards 表**：
```sql
-- 套餐周期数量
period_count INT DEFAULT 1 COMMENT '套餐周期数量: 月包=月数(3/6/12等), 年包=年数(1/2/3等)'

-- 出库日期
stock_out_date DATE NULL COMMENT '出库日期'
```

### 2. 执行迁移

```bash
# 执行数据库迁移脚本
mysql -u root -p iot_card_platform < scripts/add_period_count_field.sql
```

## 🔧 后端变更

### 1. 模型更新 (app/db/models/iot_card.py)

- ✅ 添加 `period_count` 字段
- ✅ 添加 `stock_out_date` 字段
- ✅ 更新 `to_dict()` 方法返回新字段

### 2. Schema 更新 (app/schemas/stock.py)

**StockOutCreate**：
```python
class StockOutCreate(BaseModel):
    card_ids: List[int]
    to_user_id: int
    sale_package_id: int
    period_count: int                    # 新增：套餐周期数量
    card_type: Optional[str]             # 新增：卡类型
    stock_out_date: date                 # 新增：出库日期
    test_expire_date: Optional[date]     # 新增：测试期
    silent_expire_date: date             # 新增：沉默期
    remark: Optional[str]
```

**ExcelStockOutItem**（新增）：
```python
class ExcelStockOutItem(BaseModel):
    iccid: str
    user_id: int
    sale_package_id: int
    period_count: int
    card_type: Optional[str]
    stock_out_date: date
    test_expire_date: Optional[date]
    silent_expire_date: date
    remark: Optional[str]
```

### 3. CRUD 更新 (app/crud/stock_crud.py)

**StockOutCRUD.create()**：
- ✅ 添加 `period_count` 参数
- ✅ 添加 `card_type` 参数
- ✅ 添加 `stock_out_date` 参数
- ✅ 添加 `test_expire_date` 参数
- ✅ 添加 `silent_expire_date` 参数
- ✅ 更新卡片时设置这些字段

### 4. Service 更新 (app/services/stock_service.py)

**stock_out()**：
- ✅ 添加新参数传递

**batch_stock_out_import()** (新增)：
- ✅ Excel批量出库逻辑
- ✅ 逐行处理Excel数据
- ✅ 验证卡片和套餐
- ✅ 返回成功/失败详情

### 5. API 更新 (app/api/v1/stock.py)

**POST /api/v1/stock/out**：
- ✅ 更新请求参数

**GET /api/v1/stock/out/template** (新增)：
- ✅ 返回Excel出库模板数据

**POST /api/v1/stock/out/batch-import** (新增)：
- ✅ Excel批量出库接口

## 📝 API 文档

### 1. 批量出库

**请求**：
```http
POST /api/v1/stock/out
Content-Type: application/json

{
  "card_ids": [1, 2, 3],
  "to_user_id": 10,
  "sale_package_id": 5,
  "period_count": 12,
  "card_type": "single",
  "stock_out_date": "2026-02-11",
  "test_expire_date": "2026-03-11",
  "silent_expire_date": "2026-04-11",
  "remark": "测试出库"
}
```

**响应**：
```json
{
  "code": 200,
  "msg": "成功出库 3 张卡片",
  "data": {
    "record_no": "OUT202602110001",
    "total": 3,
    "success": 3,
    "failed": 0
  }
}
```

### 2. 下载Excel出库模板

**请求**：
```http
GET /api/v1/stock/out/template
```

**响应**：
```json
{
  "code": 200,
  "msg": "出库模板数据获取成功",
  "data": [
    ["ICCID", "用户ID", "销售套餐ID", "套餐周期", "卡类型", "出库日期", "测试期截止日期", "沉默期截止日期", "备注"],
    ["89860123456789012345", "10", "5", "12", "single", "2026-02-11", "2026-03-11", "2026-04-11", "测试卡"],
    ["89860123456789012346", "10", "5", "12", "pool", "2026-02-11", "", "2026-04-11", "正式卡"]
  ]
}
```

### 3. Excel批量出库

**请求**：
```http
POST /api/v1/stock/out/batch-import
Content-Type: application/json

{
  "items": [
    {
      "iccid": "89860123456789012345",
      "user_id": 10,
      "sale_package_id": 5,
      "period_count": 12,
      "card_type": "single",
      "stock_out_date": "2026-02-11",
      "test_expire_date": "2026-03-11",
      "silent_expire_date": "2026-04-11",
      "remark": "测试卡"
    }
  ]
}
```

**响应**：
```json
{
  "code": 200,
  "msg": "批量出库完成：成功 1 张，失败 0 张",
  "data": {
    "total": 1,
    "success": 1,
    "failed": 0,
    "fail_details": null
  }
}
```

## 📋 Excel 模板格式

### 字段说明

| 列名 | 必填 | 类型 | 说明 | 示例 |
|------|------|------|------|------|
| ICCID | 是 | 字符串 | 19-20位数字 | 89860123456789012345 |
| 用户ID | 是 | 整数 | 目标用户ID | 10 |
| 销售套餐ID | 是 | 整数 | 销售套餐ID | 5 |
| 套餐周期 | 是 | 整数 | 月包=月数，年包=年数 | 12 |
| 卡类型 | 否 | 字符串 | single/pool，月包必填 | single |
| 出库日期 | 是 | 日期 | YYYY-MM-DD | 2026-02-11 |
| 测试期截止日期 | 否 | 日期 | YYYY-MM-DD | 2026-03-11 |
| 沉默期截止日期 | 是 | 日期 | YYYY-MM-DD | 2026-04-11 |
| 备注 | 否 | 字符串 | 备注信息 | 测试卡 |

### 套餐周期规则

**月包套餐**：
- 可选周期：3、6、12、24、36、50、60 个月
- 必须选择卡类型：single（单卡）或 pool（流量池卡）

**年包套餐**：
- 可选周期：1、2、3、5、6 年
- 注意：年包有效期是 360 天，不是 365 天
- 卡类型可不填（默认为 single）

## 🎨 前端开发指南

### 1. 出库表单字段

```typescript
interface StockOutForm {
  card_ids: number[]
  to_user_id: number
  sale_package_id: number
  period_count: number              // 套餐周期数量
  card_type?: 'single' | 'pool'     // 卡类型（月包显示）
  stock_out_date: string            // 出库日期 YYYY-MM-DD
  test_expire_date?: string         // 测试期 YYYY-MM-DD
  silent_expire_date: string        // 沉默期 YYYY-MM-DD
  remark?: string
}
```

### 2. 套餐周期选择器

```vue
<template>
  <el-form-item label="套餐周期" required>
    <el-select v-model="form.period_count">
      <!-- 月包选项 -->
      <el-option 
        v-if="packageType === 'monthly'"
        v-for="item in monthlyPeriods" 
        :key="item.value"
        :label="item.label" 
        :value="item.value"
      />
      <!-- 年包选项 -->
      <el-option 
        v-if="packageType === 'yearly'"
        v-for="item in yearlyPeriods" 
        :key="item.value"
        :label="item.label" 
        :value="item.value"
      />
    </el-select>
  </el-form-item>
</template>

<script setup lang="ts">
const monthlyPeriods = [
  { label: '3个月', value: 3 },
  { label: '6个月', value: 6 },
  { label: '12个月', value: 12 },
  { label: '24个月', value: 24 },
  { label: '36个月', value: 36 },
  { label: '50个月', value: 50 },
  { label: '60个月', value: 60 }
]

const yearlyPeriods = [
  { label: '1年', value: 1 },
  { label: '2年', value: 2 },
  { label: '3年', value: 3 },
  { label: '5年', value: 5 },
  { label: '6年', value: 6 }
]
</script>
```

### 3. 卡类型选择器（仅月包显示）

```vue
<el-form-item 
  v-if="packageType === 'monthly'" 
  label="卡类型" 
  required
>
  <el-radio-group v-model="form.card_type">
    <el-radio label="single">单卡（达量停机）</el-radio>
    <el-radio label="pool">流量池卡（共享流量）</el-radio>
  </el-radio-group>
</el-form-item>
```

### 4. Excel批量出库

```typescript
import * as XLSX from 'xlsx'

// 下载模板
const downloadTemplate = async () => {
  const { data } = await stockApi.getOutTemplate()
  const ws = XLSX.utils.aoa_to_sheet(data)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '出库模板')
  XLSX.writeFile(wb, '出库模板.xlsx')
}

// 上传Excel
const handleUpload = async (file: File) => {
  const data = await file.arrayBuffer()
  const workbook = XLSX.read(data)
  const worksheet = workbook.Sheets[workbook.SheetNames[0]]
  const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
  
  // 跳过表头，转换数据
  const items = jsonData.slice(1).map((row: any) => ({
    iccid: row[0],
    user_id: parseInt(row[1]),
    sale_package_id: parseInt(row[2]),
    period_count: parseInt(row[3]),
    card_type: row[4] || null,
    stock_out_date: row[5],
    test_expire_date: row[6] || null,
    silent_expire_date: row[7],
    remark: row[8] || null
  }))
  
  // 调用批量出库API
  const result = await stockApi.batchImport({ items })
  
  if (result.failed > 0) {
    // 显示失败详情
    console.log('失败详情:', result.fail_details)
  }
}
```

## ✅ 测试清单

### 后端测试

- [ ] 数据库字段添加成功
- [ ] 单张卡出库（月包 + 单卡）
- [ ] 单张卡出库（月包 + 流量池卡）
- [ ] 单张卡出库（年包）
- [ ] 批量出库（多张卡）
- [ ] Excel批量出库（成功）
- [ ] Excel批量出库（部分失败）
- [ ] 下载Excel模板
- [ ] 验证卡片状态更新
- [ ] 验证日期字段保存

### 前端测试

- [ ] 出库表单显示正确
- [ ] 月包显示套餐周期选择器（3/6/12/24/36/50/60）
- [ ] 年包显示套餐周期选择器（1/2/3/5/6）
- [ ] 月包显示卡类型选择器
- [ ] 年包不显示卡类型选择器
- [ ] 日期选择器正常工作
- [ ] Excel模板下载成功
- [ ] Excel上传解析正确
- [ ] 批量出库成功提示
- [ ] 批量出库失败详情显示

## 🚀 部署步骤

### 1. 数据库迁移

**方式一：直接在终端执行 SQL 命令**（推荐）

```bash
# 进入 MySQL 命令行
mysql -u root -p

# 切换到数据库
use iot_card_platform;

# 添加 period_count 字段
ALTER TABLE iot_cards 
ADD COLUMN period_count INT DEFAULT 1 COMMENT '套餐周期数量: 月包=月数(3/6/12等), 年包=年数(1/2/3等)' 
AFTER period_type;

# 添加 stock_out_date 字段
ALTER TABLE iot_cards 
ADD COLUMN stock_out_date DATE NULL COMMENT '出库日期' 
AFTER stock_out_at;

# 验证字段添加成功
DESC iot_cards;

# 退出
exit;
```

**方式二：使用 SQL 文件**

```bash
# 执行迁移脚本
mysql -u root -p iot_card_platform < scripts/add_period_count_field.sql

# 验证字段添加
mysql -u root -p iot_card_platform -e "DESC iot_cards;"
```

### 2. 重启后端服务

```bash
# 停止现有服务
pkill -f "uvicorn app.main"

# 启动服务
cd /Users/huiren/Documents/goodman/iot_card_platform
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
```

### 3. 前端开发

- 更新出库表单组件
- 添加套餐周期选择器
- 添加卡类型选择器
- 实现Excel批量出库功能

## 📚 相关文档

- [FRONTEND_PRD.md](./FRONTEND_PRD.md) - 前端需求文档（已更新）
- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - API文档
- [scripts/add_period_count_field.sql](./scripts/add_period_count_field.sql) - 数据库迁移脚本

## 🎉 完成状态

### 后端开发
- ✅ 数据库模型更新
- ✅ Schema 更新
- ✅ CRUD 更新
- ✅ Service 更新
- ✅ API 更新
- ✅ Excel批量出库实现
- ✅ 数据库迁移脚本

### 待完成
- ⏳ 执行数据库迁移
- ⏳ 重启后端服务
- ⏳ 前端出库表单开发
- ⏳ 前端Excel批量出库开发
- ⏳ 功能测试

## 💡 注意事项

1. **年包有效期**：年包有效期是 360 天，不是 365 天
2. **卡类型**：仅月包套餐需要选择卡类型，年包默认为单卡
3. **日期格式**：所有日期字段使用 YYYY-MM-DD 格式
4. **Excel格式**：严格按照模板格式，避免格式错误
5. **批量出库**：建议每次不超过 1000 张卡片

## 🔗 下一步

1. 执行数据库迁移脚本
2. 重启后端服务并测试API
3. 开发前端出库表单
4. 实现Excel批量出库功能
5. 进行完整的功能测试

