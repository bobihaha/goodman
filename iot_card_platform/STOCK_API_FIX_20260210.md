# 2026-02-10 库存模块修复总结

## 修复1：数据库表缺少 is_deleted 字段

### 问题
```
sqlalchemy.exc.OperationalError: (1054, "Unknown column 'is_deleted' in 'field list'")
INSERT INTO stock_in_record_cards (record_id, card_id, iccid, is_deleted) VALUES (...)
```

### 原因
- 模型继承 BaseModel（包含 is_deleted）
- 数据库表缺少该字段

### 解决
```sql
ALTER TABLE stock_in_record_cards ADD COLUMN is_deleted TINYINT DEFAULT 0;
ALTER TABLE stock_out_record_cards ADD COLUMN is_deleted TINYINT DEFAULT 0;
ALTER TABLE stock_recycle_record_cards ADD COLUMN is_deleted TINYINT DEFAULT 0;
```

## 修复2：API响应格式错误

### 问题
```javascript
TypeError: Cannot read properties of undefined (reading 'items')
TypeError: Cannot read properties of undefined (reading 'stock_cards')
```

### 原因
响应拦截器自动解包，但代码仍使用 res.data.xxx

### 解决
修改4个文件，13个函数：

**库存管理** (inventory/index.vue):
- res.data → res
- res.data.items → res.list
- res.data.total → res.total
- res.data.found → res.found

**出库页面** (out/index.vue):
- res.data.items → res.list
- res.data.success → res.success

**回收页面** (recycle/index.vue):
- res.data.items → res.list
- res.data.success → res.success

**批次管理** (batches/index.vue):
- res.data.items → res.list

## 修复状态
✅ 数据库表结构已修复
✅ API响应格式已统一
✅ 所有页面功能正常

修复时间: 2026-02-10 11:45
