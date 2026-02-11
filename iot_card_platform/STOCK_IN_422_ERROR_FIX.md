# 入库流程422错误修复记录

**时间**：2026年2月10日  
**问题**：点击确认入库时报422错误（Unprocessable Entity）

---

## 🐛 问题描述

### 错误信息
```
POST http://localhost:3000/api/v1/stock/in 422 (Unprocessable Entity)
```

### 问题原因
前端直接发送入库请求时，传递的参数不符合后端API的要求：

**前端发送的数据**：
```javascript
{
  supplier_id: 1,
  package_id: 1,
  test_expire_date: "2024-12-31",
  silent_expire_date: "2025-06-30",
  cards: [...],
  remark: "备注"
}
```

**后端期望的数据**：
```javascript
{
  batch_id: 123,  // 必须先创建批次，获取批次ID
  cards: [...],
  remark: "备注"
}
```

### 根本原因
后端的入库流程分为两步：
1. **创建采购批次**（`POST /stock/batches`）- 记录供应商、套餐、生命周期等信息
2. **批量入库卡片**（`POST /stock/in`）- 关联批次ID，导入卡片数据

但前端直接调用入库接口，跳过了创建批次的步骤。

---

## ✅ 修复方案

### 1. 前端逻辑修改

**文件**：`frontend/src/views/stock/in/index.vue`

#### 修改前（错误）
```javascript
const handleSubmit = async () => {
  submitting.value = true
  try {
    // ❌ 直接入库，缺少batch_id
    const res = await stockApi.stockIn({
      supplier_id: formData.supplier_id!,
      package_id: formData.package_id!,
      test_expire_date: formData.test_expire_date || undefined,
      silent_expire_date: formData.silent_expire_date,
      cards: cardList.value,
      remark: formData.remark
    })
    
    ElMessage.success(`入库成功！`)
  } catch (error: any) {
    ElMessage.error(error.message || '入库失败')
  } finally {
    submitting.value = false
  }
}
```

#### 修改后（正确）
```javascript
const handleSubmit = async () => {
  submitting.value = true
  try {
    // ✅ 步骤1：先创建批次
    const batchRes = await stockApi.createBatch({
      supplier_id: formData.supplier_id!,
      package_id: formData.package_id!,
      test_expire_date: formData.test_expire_date || undefined,
      silent_expire_date: formData.silent_expire_date,
      purchase_date: new Date().toISOString().split('T')[0], // 当前日期
      remark: formData.remark
    })
    
    const batchId = batchRes.data.id
    
    // ✅ 步骤2：使用批次ID进行入库
    const res = await stockApi.stockIn({
      batch_id: batchId,
      cards: cardList.value,
      remark: formData.remark
    })
    
    ElMessage.success(`入库成功！成功 ${res.data.success} 张，失败 ${res.data.failed} 张`)
    
    // 重置表单...
  } catch (error: any) {
    ElMessage.error(error.message || '入库失败')
  } finally {
    submitting.value = false
  }
}
```

### 2. API方法添加

**文件**：`frontend/src/api/modules/stock.ts`

添加 `createBatch` 方法：

```typescript
export const stockApi = {
  // ============ 批次管理 ============
  
  /**
   * 创建采购批次
   */
  createBatch(data: any) {
    return request.post('/stock/batches', data)
  },

  // ============ 入库 ============
  
  /**
   * 批量入库
   */
  stockIn(data: any) {
    return request.post('/stock/in', data)
  },
  
  // ... 其他方法
}
```

---

## 📋 入库流程说明

### 完整流程

```
用户操作
  ↓
1. 填写入库信息
   - 选择供应商
   - 选择底层套餐
   - 设置测试期/沉默期
   - 导入卡片数据
  ↓
2. 点击"确认入库"
  ↓
3. 前端：创建采购批次
   POST /stock/batches
   {
     supplier_id: 1,
     package_id: 1,
     test_expire_date: "2024-12-31",
     silent_expire_date: "2025-06-30",
     purchase_date: "2024-01-15",
     remark: "备注"
   }
   ← 返回 { id: 123, batch_no: "B20240115ABCD" }
  ↓
4. 前端：批量入库卡片
   POST /stock/in
   {
     batch_id: 123,
     cards: [
       { iccid: "...", imsi: "...", msisdn: "..." },
       ...
     ],
     remark: "备注"
   }
   ← 返回 { success: 100, failed: 0 }
  ↓
5. 显示入库结果
```

### 为什么需要两步？

#### 1. 批次管理的意义
- **追溯性**：每批卡片都有明确的来源（供应商、套餐、采购日期）
- **生命周期管理**：批次统一管理测试期和沉默期
- **库存统计**：按批次统计入库、出库、剩余数量
- **财务对账**：批次关联采购成本

#### 2. 数据库设计
```
purchase_batches (采购批次表)
  ├─ id: 批次ID
  ├─ supplier_id: 供应商
  ├─ package_id: 套餐
  ├─ test_expire_date: 测试期截止
  ├─ silent_expire_date: 沉默期截止
  └─ card_count: 卡片数量

iot_cards (物联网卡表)
  ├─ id: 卡片ID
  ├─ batch_id: 关联批次 ← 必须字段
  ├─ iccid: ICCID
  ├─ imsi: IMSI
  └─ msisdn: 号码
```

---

## 🔍 后端API详解

### API 1: 创建采购批次

**接口**：`POST /api/v1/stock/batches`

**请求参数**：
```typescript
{
  supplier_id: number        // 供应商ID（必填）
  package_id: number         // 底层套餐ID（必填）
  test_expire_date?: string  // 测试期截止日期（可选，格式：YYYY-MM-DD）
  silent_expire_date: string // 沉默期截止日期（必填，格式：YYYY-MM-DD）
  purchase_date: string      // 采购日期（必填，格式：YYYY-MM-DD）
  remark?: string           // 备注（可选）
}
```

**响应数据**：
```typescript
{
  code: 200,
  msg: "批次创建成功",
  data: {
    id: 123,
    batch_no: "B20240115ABCD",
    supplier_id: 1,
    package_id: 1,
    // ... 其他字段
  }
}
```

### API 2: 批量入库卡片

**接口**：`POST /api/v1/stock/in`

**请求参数**：
```typescript
{
  batch_id: number           // 批次ID（必填）
  cards: [                   // 卡片列表（必填，至少1张）
    {
      iccid: string,         // ICCID（必填，19-30位）
      imsi?: string,         // IMSI（可选）
      msisdn?: string        // 号码（可选）
    }
  ],
  remark?: string           // 备注（可选）
}
```

**响应数据**：
```typescript
{
  code: 200,
  msg: "成功入库 100 张卡片",
  data: {
    record_no: "IN20240115EFGH",
    total: 100,
    success: 100,
    failed: 0,
    fail_details: []
  }
}
```

---

## ✅ 测试验证

### 测试用例1：正常入库流程

**步骤**：
1. 选择供应商：中国移动
2. 选择套餐：移动1G月包
3. 设置沉默期：2025-06-30
4. 导入3张卡片
5. 点击确认入库

**预期结果**：
```
✅ 创建批次成功（batch_id: 123）
✅ 入库成功（成功3张，失败0张）
✅ 显示成功提示
✅ 表单重置
```

### 测试用例2：批次创建失败

**场景**：供应商ID不存在

**预期结果**：
```
❌ 提示"供应商不存在"
❌ 不执行入库操作
```

### 测试用例3：入库部分失败

**场景**：导入的卡片中有重复的ICCID

**预期结果**：
```
✅ 批次创建成功
⚠️  入库部分成功（成功2张，失败1张）
✅ 显示详细的失败原因
```

---

## 📊 修改总结

### 前端修改
- ✅ `frontend/src/views/stock/in/index.vue`
  - 修改 `handleSubmit` 函数，添加两步流程
  - 先创建批次，再入库卡片

- ✅ `frontend/src/api/modules/stock.ts`
  - 添加 `createBatch` API方法

### 后端修改
- ✅ 无需修改（API已正确实现）

### 影响范围
- ✅ 仅影响卡片入库功能
- ✅ 其他功能不受影响

---

## 💡 最佳实践

### 1. 错误处理
```javascript
try {
  // 创建批次
  const batchRes = await stockApi.createBatch(...)
  
  // 入库卡片
  const res = await stockApi.stockIn(...)
  
  ElMessage.success('入库成功')
} catch (error: any) {
  // 区分错误类型
  if (error.message.includes('批次')) {
    ElMessage.error('批次创建失败：' + error.message)
  } else {
    ElMessage.error('入库失败：' + error.message)
  }
}
```

### 2. 用户体验优化
```javascript
// 显示进度提示
ElMessage.info('正在创建批次...')
const batchRes = await stockApi.createBatch(...)

ElMessage.info('正在导入卡片...')
const res = await stockApi.stockIn(...)

ElMessage.success('入库完成！')
```

### 3. 数据验证
```javascript
// 前端验证
if (!formData.supplier_id) {
  ElMessage.warning('请选择供应商')
  return
}

if (!formData.silent_expire_date) {
  ElMessage.warning('请设置沉默期截止日期')
  return
}

if (cardList.value.length === 0) {
  ElMessage.warning('请至少添加一张卡片')
  return
}
```

---

## 🔄 后续建议

### 短期
- ✅ 已完成：修复入库流程
- 📋 添加批次创建的进度提示
- 📋 优化错误提示信息

### 中期
- 📋 支持批次复用（同一批次多次入库）
- 📋 添加批次管理页面
- 📋 支持批次信息编辑

### 长期
- 📋 批次自动归档
- 📋 批次成本分析
- 📋 批次生命周期报表

---

**修复人**：后端开发团队  
**修复时间**：2026年2月10日 11:00  
**验证状态**：✅ 待测试验证


