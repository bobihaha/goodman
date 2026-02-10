# 前端导入错误修复记录

**时间**：2026年2月10日  
**问题**：Vue Router 报错 - supplierApi 导出不存在

---

## 🐛 问题描述

### 错误信息
```
[Vue Router warn]: uncaught error during route navigation:
SyntaxError: The requested module '/src/api/modules/supplier.ts' does not provide an export named 'supplierApi'
```

### 问题原因
`frontend/src/api/modules/supplier.ts` 文件只导出了单独的函数，没有导出 `supplierApi` 对象，导致使用命名导入的组件报错。

---

## ✅ 修复方案

### 修改文件：`frontend/src/api/modules/supplier.ts`

#### 1. 添加 `getEnabledSuppliers` 函数
```typescript
/**
 * 获取所有启用的供应商（用于下拉选择）
 */
export function getEnabledSuppliers() {
  return request.get<Supplier[]>('/suppliers/options')
}
```

#### 2. 添加 `supplierApi` 命名导出
```typescript
// 导出为 supplierApi 对象（保持与其他模块一致）
export const supplierApi = {
  getList: getSupplierList,
  getOptions: getSupplierOptions,
  getEnabled: getEnabledSuppliers,
  getDetail: getSupplierDetail,
  create: createSupplier,
  update: updateSupplier,
  delete: deleteSupplier,
  testConnection: testApiConnection
}
```

#### 3. 更新默认导出
```typescript
export default {
  getSupplierList,
  getSupplierOptions,
  getEnabledSuppliers,
  getSupplierDetail,
  createSupplier,
  updateSupplier,
  deleteSupplier,
  testApiConnection
}
```

---

## 📊 影响范围

### 使用命名导入的文件（已修复）
- ✅ `frontend/src/views/stock/records/index.vue`
- ✅ `frontend/src/views/stock/in/index.vue`
- ✅ `frontend/src/views/stock/out/index.vue`
- ✅ `frontend/src/views/stock/inventory/index.vue`
- ✅ `frontend/src/views/stock/batches/index.vue`

### 使用默认导入的文件（无需修改）
- ✅ `frontend/src/views/suppliers/index.vue`
- ✅ `frontend/src/views/suppliers/components/SupplierFormDialog.vue`

### 使用 package.ts 中 supplierApi 的文件（无需修改）
- ✅ `frontend/src/views/packages/supplier/index.vue`

---

## 🎯 导入方式说明

现在 `supplier.ts` 支持两种导入方式：

### 方式1：命名导入（推荐）
```typescript
import { supplierApi } from '@/api/modules/supplier'

// 使用
supplierApi.getList(params)
supplierApi.getEnabled()
```

### 方式2：默认导入
```typescript
import supplierApi from '@/api/modules/supplier'

// 使用
supplierApi.getSupplierList(params)
supplierApi.getEnabledSuppliers()
```

---

## 🔍 API 方法映射

| supplierApi 对象方法 | 原始函数名 | 说明 |
|---------------------|-----------|------|
| `getList()` | `getSupplierList()` | 获取供应商列表 |
| `getOptions()` | `getSupplierOptions()` | 获取供应商选项 |
| `getEnabled()` | `getEnabledSuppliers()` | 获取启用的供应商 |
| `getDetail()` | `getSupplierDetail()` | 获取供应商详情 |
| `create()` | `createSupplier()` | 创建供应商 |
| `update()` | `updateSupplier()` | 更新供应商 |
| `delete()` | `deleteSupplier()` | 删除供应商 |
| `testConnection()` | `testApiConnection()` | 测试API连接 |

---

## ✅ 验证结果

修复后，所有使用 `supplierApi` 的页面都能正常工作：
- ✅ 出入库记录页面可以正常加载
- ✅ 供应商管理页面可以正常使用
- ✅ 套餐管理页面可以正常使用
- ✅ 库存管理页面可以正常使用

---

## 💡 经验总结

### 问题根源
不同的开发人员使用了不同的导出方式，导致API模块不一致。

### 最佳实践
1. **统一导出格式**：所有API模块都应该同时提供命名导出和默认导出
2. **命名规范**：使用 `xxxApi` 作为对象名，方法名使用简洁的动词
3. **向后兼容**：保留原有的函数导出，避免破坏现有代码

### 推荐的API模块模板
```typescript
// 定义单独的函数
export function getList(params: any) {
  return request.get('/api/xxx', { params })
}

export function getDetail(id: number) {
  return request.get(`/api/xxx/${id}`)
}

// 导出为对象（命名导出）
export const xxxApi = {
  getList,
  getDetail,
  // ... 其他方法
}

// 默认导出（向后兼容）
export default {
  getList,
  getDetail,
  // ... 其他方法
}
```

---

**修复人**：后端开发团队  
**修复时间**：2026年2月10日 10:15

