# 库存模块 API 响应格式修复文档

## 修复日期
2026-02-10

## 问题概述

在完成入库功能的数据库表结构修复后，测试发现出库和库存管理页面出现多个 API 响应格式错误，导致页面无法正常显示数据。

## 错误现象

### 错误1：库存管理页面
```javascript
index.vue:287 获取销售套餐列表失败 TypeError: Cannot read properties of undefined (reading 'items')
    at fetchSalePackages (index.vue:285:35)

index.vue:353 获取套餐列表失败 TypeError: Cannot read properties of undefined (reading 'items')
    at fetchPackages (index.vue:351:31)

index.vue:26 Uncaught (in promise) TypeError: Cannot read properties of undefined (reading 'stock_cards')
    at index.vue:26:50
```

### 错误2：出库页面
```javascript
TypeError: Cannot read properties of undefined (reading 'items')
```

## 根本原因

### 响应拦截器自动解包

前端的响应拦截器会自动解包后端返回的数据：

```typescript
// frontend/src/utils/request.ts
request.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response
    
    // 如果响应数据有 code 字段，返回 data.data
    if (data && typeof data === 'object' && 'code' in data) {
      if (data.code === 200 || data.code === 0) {
        return data.data  // ✅ 自动解包，直接返回 data.data
      }
    }
    
    // 如果没有 code 字段，直接返回 data
    return data
  }
)
```

### 后端返回格式

后端统一返回格式：
```python
{
  "code": 200,
  "msg": "success",
  "data": {
    "list": [...],
    "total": 100
  }
}
```

### 前端错误用法

前端代码错误地使用了 `res.data.items` 或 `res.data.list`：

```typescript
// ❌ 错误：响应拦截器已经解包，res 就是 data.data
const res = await stockApi.getInventory(queryParams)
tableData.value = res.data.items  // ❌ 错误：res.data 是 undefined

// ✅ 正确：直接使用 res
tableData.value = res.list  // ✅ 正确
```

## 修复方案

### 统一响应格式处理规则

**规则**：响应拦截器已经自动解包，前端直接使用返回值

```typescript
// 后端返回
{
  code: 200,
  data: {
    list: [...],
    total: 100
  }
}

// 响应拦截器处理后
{
  list: [...],
  total: 100
}

// 前端使用
const res = await api.getList()
console.log(res.list)   // ✅ 正确
console.log(res.total)  // ✅ 正确
```

## 修复的文件

### 1. 库存管理页面

**文件**: `frontend/src/views/stock/inventory/index.vue`

#### 修复1：获取库存统计
```typescript
// ❌ 修复前
const fetchSummary = async () => {
  try {
    const res = await stockApi.getSummary()
    summary.value = res.data  // ❌ 错误
  } catch (error) {
    console.error('获取库存统计失败', error)
  }
}

// ✅ 修复后
const fetchSummary = async () => {
  try {
    const res = await stockApi.getSummary()
    summary.value = res  // ✅ 正确
  } catch (error) {
    console.error('获取库存统计失败', error)
  }
}
```

#### 修复2：获取库存列表
```typescript
// ❌ 修复前
const fetchInventory = async () => {
  loading.value = true
  try {
    const res = await stockApi.getInventory(queryParams)
    tableData.value = res.data.items  // ❌ 错误
    total.value = res.data.total      // ❌ 错误
  } catch (error) {
    ElMessage.error('获取库存列表失败')
  } finally {
    loading.value = false
  }
}

// ✅ 修复后
const fetchInventory = async () => {
  loading.value = true
  try {
    const res = await stockApi.getInventory(queryParams)
    tableData.value = res.list || []  // ✅ 正确
    total.value = res.total || 0      // ✅ 正确
  } catch (error) {
    ElMessage.error('获取库存列表失败')
  } finally {
    loading.value = false
  }
}
```

#### 修复3：获取套餐列表
```typescript
// ❌ 修复前
const fetchPackages = async () => {
  try {
    const res = await packageApi.getSupplierPackages({ page: 1, page_size: 100 })
    packages.value = res.data.items  // ❌ 错误
  } catch (error) {
    console.error('获取套餐列表失败', error)
  }
}

// ✅ 修复后
const fetchPackages = async () => {
  try {
    const res = await packageApi.getSupplierPackages({ page: 1, page_size: 100 })
    packages.value = res.list || []  // ✅ 正确
  } catch (error) {
    console.error('获取套餐列表失败', error)
  }
}
```

#### 修复4：批量查询
```typescript
// ❌ 修复前
const handleBatchQuery = async () => {
  // ...
  try {
    const res = await stockApi.batchQuery({ iccids })
    batchQueryResult.value = res.data.found || []      // ❌ 错误
    batchQueryNotFound.value = res.data.not_found || [] // ❌ 错误
  } catch (error: any) {
    ElMessage.error(error.message || '批量查询失败')
  }
}

// ✅ 修复后
const handleBatchQuery = async () => {
  // ...
  try {
    const res = await stockApi.batchQuery({ iccids })
    batchQueryResult.value = res.found || []      // ✅ 正确
    batchQueryNotFound.value = res.not_found || [] // ✅ 正确
  } catch (error: any) {
    ElMessage.error(error.message || '批量查询失败')
  }
}
```

#### 修复5：导出库存
```typescript
// ❌ 修复前
const handleExport = async () => {
  try {
    const res = await stockApi.exportInventory(queryParams)
    const ws = XLSX.utils.json_to_sheet(res.data)  // ❌ 错误
    // ...
  } catch (error: any) {
    ElMessage.error(error.message || '导出失败')
  }
}

// ✅ 修复后
const handleExport = async () => {
  try {
    const res = await stockApi.exportInventory(queryParams)
    const ws = XLSX.utils.json_to_sheet(res)  // ✅ 正确
    // ...
  } catch (error: any) {
    ElMessage.error(error.message || '导出失败')
  }
}
```

### 2. 出库页面

**文件**: `frontend/src/views/stock/out/index.vue`

#### 修复1：获取库存卡片
```typescript
// ❌ 修复前
const fetchInventory = async () => {
  loading.value = true
  try {
    const res = await stockApi.getInventory(queryParams)
    tableData.value = res.data.items  // ❌ 错误
    total.value = res.data.total      // ❌ 错误
  } catch (error) {
    ElMessage.error('获取库存卡片失败')
  } finally {
    loading.value = false
  }
}

// ✅ 修复后
const fetchInventory = async () => {
  loading.value = true
  try {
    const res = await stockApi.getInventory(queryParams)
    tableData.value = res.list || []  // ✅ 正确
    total.value = res.total || 0      // ✅ 正确
  } catch (error) {
    ElMessage.error('获取库存卡片失败')
  } finally {
    loading.value = false
  }
}
```

#### 修复2：获取销售套餐列表
```typescript
// ❌ 修复前
const fetchSalePackages = async () => {
  try {
    const res = await packageApi.getSalePackages({ page: 1, page_size: 100 })
    salePackages.value = res.data.items  // ❌ 错误
  } catch (error) {
    console.error('获取销售套餐列表失败', error)
  }
}

// ✅ 修复后
const fetchSalePackages = async () => {
  try {
    const res = await packageApi.getSalePackages({ page: 1, page_size: 100 })
    salePackages.value = res.list || []  // ✅ 正确
  } catch (error) {
    console.error('获取销售套餐列表失败', error)
  }
}
```

#### 修复3：提交出库
```typescript
// ❌ 修复前
const handleSubmit = async () => {
  submitting.value = true
  try {
    const res = await stockApi.stockOut({
      card_ids,
      to_user_id: outForm.to_user_id!,
      sale_package_id: outForm.sale_package_id!,
      remark: outForm.remark
    })
    
    ElMessage.success(`出库成功！成功 ${res.data.success} 张，失败 ${res.data.failed} 张`)  // ❌ 错误
  } catch (error: any) {
    ElMessage.error(error.message || '出库失败')
  } finally {
    submitting.value = false
  }
}

// ✅ 修复后
const handleSubmit = async () => {
  submitting.value = true
  try {
    const res = await stockApi.stockOut({
      card_ids,
      to_user_id: outForm.to_user_id!,
      sale_package_id: outForm.sale_package_id!,
      remark: outForm.remark
    })
    
    ElMessage.success(`出库成功！成功 ${res.success} 张，失败 ${res.failed} 张`)  // ✅ 正确
  } catch (error: any) {
    ElMessage.error(error.message || '出库失败')
  } finally {
    submitting.value = false
  }
}
```

### 3. 回收页面

**文件**: `frontend/src/views/stock/recycle/index.vue`

#### 修复1：搜索已出库卡片
```typescript
// ❌ 修复前
const handleSearch = async () => {
  loading.value = true
  try {
    const res = await stockApi.getInventory({
      ...searchParams,
      status: 'out'
    })
    outCards.value = res.data.items || []  // ❌ 错误
    total.value = res.data.total || 0      // ❌ 错误
  } catch (error: any) {
    ElMessage.error(error.message || '查询失败')
  } finally {
    loading.value = false
  }
}

// ✅ 修复后
const handleSearch = async () => {
  loading.value = true
  try {
    const res = await stockApi.getInventory({
      ...searchParams,
      status: 'out'
    })
    outCards.value = res.list || []  // ✅ 正确
    total.value = res.total || 0     // ✅ 正确
  } catch (error: any) {
    ElMessage.error(error.message || '查询失败')
  } finally {
    loading.value = false
  }
}
```

#### 修复2：确认回收
```typescript
// ❌ 修复前
const handleConfirmRecycle = async () => {
  // ...
  try {
    const res = await stockApi.recycleCards({
      card_ids,
      recycle_reason: recycleForm.recycle_reason,
      remark: recycleForm.remark
    })

    ElMessage.success(`回收成功！成功 ${res.data.success} 张，失败 ${res.data.failed} 张`)  // ❌ 错误
  } catch (error: any) {
    ElMessage.error(error.message || '回收失败')
  }
}

// ✅ 修复后
const handleConfirmRecycle = async () => {
  // ...
  try {
    const res = await stockApi.recycleCards({
      card_ids,
      recycle_reason: recycleForm.recycle_reason,
      remark: recycleForm.remark
    })

    ElMessage.success(`回收成功！成功 ${res.success} 张，失败 ${res.failed} 张`)  // ✅ 正确
  } catch (error: any) {
    ElMessage.error(error.message || '回收失败')
  }
}
```

#### 修复3：查询回收记录
```typescript
// ❌ 修复前
const handleQueryRecords = async () => {
  recordsLoading.value = true
  try {
    const params: any = { ...recordParams }
    if (recordDateRange.value && recordDateRange.value.length === 2) {
      params.start_date = recordDateRange.value[0]
      params.end_date = recordDateRange.value[1]
    }

    const res = await stockApi.getRecycleRecords(params)
    recycleRecords.value = res.data.items || []  // ❌ 错误
    recordTotal.value = res.data.total || 0      // ❌ 错误
  } catch (error: any) {
    ElMessage.error(error.message || '查询失败')
  } finally {
    recordsLoading.value = false
  }
}

// ✅ 修复后
const handleQueryRecords = async () => {
  recordsLoading.value = true
  try {
    const params: any = { ...recordParams }
    if (recordDateRange.value && recordDateRange.value.length === 2) {
      params.start_date = recordDateRange.value[0]
      params.end_date = recordDateRange.value[1]
    }

    const res = await stockApi.getRecycleRecords(params)
    recycleRecords.value = res.list || []  // ✅ 正确
    recordTotal.value = res.total || 0     // ✅ 正确
  } catch (error: any) {
    ElMessage.error(error.message || '查询失败')
  } finally {
    recordsLoading.value = false
  }
}
```

### 4. 批次管理页面

**文件**: `frontend/src/views/stock/batches/index.vue`

#### 修复1：获取批次列表
```typescript
// ❌ 修复前
const fetchBatches = async () => {
  loading.value = true
  try {
    const res = await stockApi.getBatches(queryParams)
    tableData.value = res.data.items  // ❌ 错误
    total.value = res.data.total      // ❌ 错误
  } catch (error) {
    ElMessage.error('获取批次列表失败')
  } finally {
    loading.value = false
  }
}

// ✅ 修复后
const fetchBatches = async () => {
  loading.value = true
  try {
    const res = await stockApi.getBatches(queryParams)
    tableData.value = res.list || []  // ✅ 正确
    total.value = res.total || 0      // ✅ 正确
  } catch (error) {
    ElMessage.error('获取批次列表失败')
  } finally {
    loading.value = false
  }
}
```

#### 修复2：获取底层套餐列表
```typescript
// ❌ 修复前
const fetchPackages = async () => {
  try {
    const res = await packageApi.getSupplierPackages({ page: 1, page_size: 100 })
    packages.value = res.data.items  // ❌ 错误
  } catch (error) {
    console.error('获取套餐列表失败', error)
  }
}

// ✅ 修复后
const fetchPackages = async () => {
  try {
    const res = await packageApi.getSupplierPackages({ page: 1, page_size: 100 })
    packages.value = res.list || []  // ✅ 正确
  } catch (error) {
    console.error('获取套餐列表失败', error)
  }
}
```

## 修复统计

### 修复的文件数量
- ✅ 4个 Vue 组件文件

### 修复的函数数量
- ✅ 库存管理页面：5个函数
- ✅ 出库页面：3个函数
- ✅ 回收页面：3个函数
- ✅ 批次管理页面：2个函数
- **总计：13个函数**

### 修复的错误类型
1. ✅ `res.data.items` → `res.list`
2. ✅ `res.data.total` → `res.total`
3. ✅ `res.data.found` → `res.found`
4. ✅ `res.data.not_found` → `res.not_found`
5. ✅ `res.data.success` → `res.success`
6. ✅ `res.data.failed` → `res.failed`
7. ✅ `res.data` → `res`（直接使用）

## 预防措施

### 1. 统一响应格式处理规范

**规则**：响应拦截器已自动解包，前端直接使用返回值

```typescript
// ✅ 正确的使用方式
const res = await api.getList()
console.log(res.list)    // 直接访问
console.log(res.total)   // 直接访问

// ❌ 错误的使用方式
const res = await api.getList()
console.log(res.data.list)   // 多余的 .data
console.log(res.data.total)  // 多余的 .data
```

### 2. 添加类型定义

为所有 API 响应添加明确的类型定义：

```typescript
// types/api.d.ts
export interface PaginationResponse<T> {
  list: T[]
  total: number
}

export interface BatchQueryResponse {
  found: Card[]
  not_found: string[]
}

export interface OperationResponse {
  success: number
  failed: number
}

// 使用
const res = await api.getList() as PaginationResponse<Card>
console.log(res.list)   // TypeScript 会提示正确的属性
```

### 3. 代码审查清单

在添加新的 API 调用时，检查：
- [ ] 是否直接使用 `res.xxx` 而不是 `res.data.xxx`
- [ ] 是否添加了类型定义
- [ ] 是否添加了空值保护（`|| []` 或 `|| 0`）
- [ ] 错误处理是否完善

### 4. 使用 ESLint 规则

可以添加自定义规则检测错误用法：

```javascript
// .eslintrc.js
rules: {
  'no-restricted-syntax': [
    'error',
    {
      selector: "MemberExpression[object.name='res'][property.name='data']",
      message: '响应拦截器已自动解包，请直接使用 res.xxx 而不是 res.data.xxx'
    }
  ]
}
```

### 5. 添加单元测试

为 API 调用添加单元测试，确保响应格式正确：

```typescript
// tests/api/stock.spec.ts
describe('Stock API', () => {
  it('should return correct format', async () => {
    const res = await stockApi.getInventory({ page: 1, page_size: 10 })
    
    expect(res).toHaveProperty('list')
    expect(res).toHaveProperty('total')
    expect(Array.isArray(res.list)).toBe(true)
    expect(typeof res.total).toBe('number')
  })
})
```

## 调试技巧

### 1. 查看响应拦截器处理结果

在响应拦截器中添加日志：

```typescript
request.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response
    
    if (import.meta.env.DEV) {
      console.log('响应拦截器处理:', {
        原始数据: data,
        处理后: data.data || data
      })
    }
    
    // ...
  }
)
```

### 2. 检查 API 返回格式

在浏览器 Console 中测试：

```javascript
// 测试 API 调用
const res = await stockApi.getInventory({ page: 1, page_size: 10 })
console.log('返回结果:', res)
console.log('是否有 list:', 'list' in res)
console.log('是否有 data:', 'data' in res)
```

### 3. 使用 TypeScript 类型检查

启用严格模式，TypeScript 会提示类型错误：

```typescript
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true
  }
}
```

### 4. 查看 Network 请求

在 Network 标签中查看实际的响应数据：

```json
// 后端返回
{
  "code": 200,
  "msg": "success",
  "data": {
    "list": [...],
    "total": 100
  }
}

// 响应拦截器处理后（前端收到）
{
  "list": [...],
  "total": 100
}
```

## 相关文件

- `frontend/src/utils/request.ts` - 响应拦截器配置
- `frontend/src/views/stock/inventory/index.vue` - 库存管理页面
- `frontend/src/views/stock/out/index.vue` - 出库页面
- `frontend/src/views/stock/recycle/index.vue` - 回收页面
- `frontend/src/views/stock/batches/index.vue` - 批次管理页面

## 测试验证

### 验证步骤

1. ✅ 访问库存管理页面，数据正常显示
2. ✅ 访问出库页面，卡片列表正常加载
3. ✅ 访问回收页面，已出库卡片正常显示
4. ✅ 访问批次管理页面，批次列表正常显示
5. ✅ 测试批量查询功能，结果正常显示
6. ✅ 测试导出功能，数据正常导出

### 验证结果

所有页面和功能都已正常工作，不再出现 `Cannot read properties of undefined` 错误。

## 总结

本次修复解决了库存模块中所有的 API 响应格式问题：

1. **问题根源**：响应拦截器自动解包，但前端代码仍使用 `res.data.xxx`
2. **修复方案**：统一改为直接使用 `res.xxx`
3. **修复范围**：4个文件，13个函数
4. **修复类型**：7种错误模式

所有修复都已完成并验证通过，库存模块现在可以正常使用。

---

**修复完成时间**: 2026-02-10 11:45
**修复状态**: ✅ 已完成
**测试状态**: ✅ 已通过





