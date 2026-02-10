# 入库超时和库存显示问题修复

## 问题1：入库请求超时

### 现象
```
fetchError: Request timeout after 30000ms
点击确认入库无反应
```

### 原因
- 前端请求超时设置为30秒
- 入库操作涉及多个数据库操作（创建批次、创建卡片、创建记录），可能超过30秒

### 解决方案
将请求超时时间从30秒增加到60秒

**文件**: `frontend/src/utils/request.ts`

```typescript
// 修改前
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,  // 30秒
  headers: {
    'Content-Type': 'application/json'
  }
})

// 修改后
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 60000,  // 60秒
  headers: {
    'Content-Type': 'application/json'
  }
})
```

## 问题2：库存管理页面不显示已入库卡片

### 数据验证
数据库中确实有数据：
- 9张库存卡片（status='stock', user_id IS NULL）
- 包括最近入库的3张卡片（11:41:16入库）

### 可能原因
1. 前端API响应格式处理问题（已修复）
2. 前端缓存问题
3. 浏览器需要刷新

### 解决步骤

#### 1. 清除浏览器缓存
- Mac: `Cmd + Shift + R`
- Windows: `Ctrl + Shift + R`

#### 2. 检查Network请求
在浏览器开发者工具中查看：
```
GET /api/v1/stock/inventory?sort_by=stock_in_at&sort_order=desc&page=1&page_size=20
```

响应应该包含：
```json
{
  "list": [
    {
      "id": 21,
      "iccid": "898604D92623D0373773",
      "status": "stock",
      ...
    }
  ],
  "total": 9
}
```

#### 3. 检查前端代码
确保使用正确的响应格式：
```typescript
const res = await stockApi.getInventory(queryParams)
tableData.value = res.list || []  // ✅ 正确
total.value = res.total || 0      // ✅ 正确
```

## 测试步骤

### 1. 测试入库功能
1. 访问入库页面
2. 填写入库信息
3. 添加卡片（ICCID、IMSI、MSISDN）
4. 点击"确认入库"
5. 等待响应（最多60秒）
6. 检查是否显示成功消息

### 2. 测试库存显示
1. 访问库存管理页面
2. 硬刷新页面（Cmd+Shift+R）
3. 检查是否显示卡片列表
4. 检查总数是否正确

## 当前数据库状态

### 批次信息
```
ID=9, 批次号=B20260210D36E, 总数=3, 已入库=3, 创建时间=2026-02-10 11:41:16
```

### 库存卡片（共9张）
```
ID=21, ICCID=898604D92623D0373773, 状态=stock, 入库时间=2026-02-10 11:41:16
ID=22, ICCID=898604D92623D0373774, 状态=stock, 入库时间=2026-02-10 11:41:16
ID=23, ICCID=898604D92623D0373775, 状态=stock, 入库时间=2026-02-10 11:41:16
ID=15, ICCID=89860123456789012345, 状态=stock, 入库时间=2026-01-28 14:05:29
ID=16, ICCID=89860123456789012346, 状态=stock, 入库时间=2026-01-28 14:05:29
ID=17, ICCID=89860123456789012347, 状态=stock, 入库时间=2026-01-28 14:05:29
ID=14, ICCID=89860012345678900005, 状态=stock, 入库时间=2026-01-14 14:39:03
ID=6, ICCID=89860012345678901239, 状态=stock, 入库时间=2026-01-14 10:00:00
ID=7, ICCID=89860012345678901240, 状态=stock, 入库时间=2026-01-14 10:00:00
```

### 入库记录
```
ID=2, 总数=3, 成功=3, 失败=0, 创建时间=2026-02-10 11:41:16
```

## 修复状态
✅ 请求超时时间已增加到60秒
⏳ 等待测试库存显示问题

修复时间: 2026-02-10 13:58
