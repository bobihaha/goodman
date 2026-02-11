# 出入库管理模块 - 后端API开发清单

## 📋 概述

本文档列出了出入库管理模块前端已完成但后端需要补充开发的API接口清单。

**前端开发状态**: ✅ 已完成
**后端开发状态**: 🔄 部分完成（基础接口已实现，需补充11个接口）

---

## ✅ 后端已实现的接口

| 接口 | 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|------|
| 创建采购批次 | POST | `/api/v1/stock/batches` | 创建采购批次 | ✅ 已实现 |
| 获取批次详情 | GET | `/api/v1/stock/batches/{batch_id}` | 获取批次详情 | ✅ 已实现 |
| 批量入库 | POST | `/api/v1/stock/in` | 批量导入卡片入库 | ✅ 已实现 |
| 批量出库 | POST | `/api/v1/stock/out` | 批量卡片出库 | ✅ 已实现 |
| 库存统计 | GET | `/api/v1/stock/summary` | 获取库存统计数据 | ✅ 已实现 |
| 库存列表 | GET | `/api/v1/stock/inventory` | 获取库存卡片列表 | ✅ 已实现 |

---

## ❌ 需要补充开发的接口（共11个）

### 优先级 P0 - 核心功能（3个）

#### 1. 获取入库记录列表
```
GET /api/v1/stock/in/records
```

**功能描述**：
- 分页查询入库记录列表
- 支持按供应商、时间范围筛选
- 返回入库记录摘要信息

**请求参数**：
```json
{
  "supplier_id": 1,           // 可选，供应商ID
  "start_date": "2026-01-01", // 可选，开始日期
  "end_date": "2026-02-09",   // 可选，结束日期
  "page": 1,                  // 必填，页码
  "page_size": 20             // 必填，每页数量
}
```

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "supplier_id": 1,
        "supplier_name": "供应商A",
        "package_id": 1,
        "package_name": "移动1G/月",
        "card_count": 100,
        "success_count": 98,
        "failed_count": 2,
        "test_expire_date": "2026-01-31",
        "silent_expire_date": "2026-04-30",
        "operator_id": 1,
        "operator_name": "管理员",
        "remark": "第一批入库",
        "created_at": "2026-02-09 10:00:00"
      }
    ]
  }
}
```

**数据库表**: `stock_in_records`

---

#### 2. 获取出库记录列表
```
GET /api/v1/stock/out/records
```

**功能描述**：
- 分页查询出库记录列表
- 支持按目标用户、时间范围筛选
- 返回出库记录摘要信息

**请求参数**：
```json
{
  "user_id": 2,               // 可选，目标用户ID
  "start_date": "2026-01-01", // 可选，开始日期
  "end_date": "2026-02-09",   // 可选，结束日期
  "page": 1,                  // 必填，页码
  "page_size": 20             // 必填，每页数量
}
```

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 50,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "user_id": 2,
        "user_name": "代理商A",
        "sale_package_id": 1,
        "sale_package_name": "移动1G/月-销售版",
        "card_count": 50,
        "success_count": 50,
        "failed_count": 0,
        "unit_price": 15.00,
        "total_amount": 750.00,
        "operator_id": 1,
        "operator_name": "管理员",
        "remark": "首次出库",
        "created_at": "2026-02-09 11:00:00"
      }
    ]
  }
}
```

**数据库表**: `stock_out_records`

---

#### 3. 批量查询卡片
```
POST /api/v1/stock/inventory/batch-query
```

**功能描述**：
- 根据多个ICCID批量查询卡片信息
- 返回找到的卡片列表和未找到的ICCID列表
- 最多支持10000个ICCID

**请求参数**：
```json
{
  "iccids": [
    "89860123456789012345",
    "89860123456789012346",
    "89860123456789012347"
  ]
}
```

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "found": [
      {
        "id": 1,
        "iccid": "89860123456789012345",
        "imsi": "460012345678901",
        "msisdn": "13800138000",
        "carrier": "cmcc",
        "carrier_name": "中国移动",
        "supplier_id": 1,
        "supplier_name": "供应商A",
        "status": "stock",
        "status_name": "库存",
        "stock_in_at": "2026-02-09 10:00:00"
      }
    ],
    "not_found": [
      "89860123456789012346",
      "89860123456789012347"
    ]
  }
}
```

**验证规则**：
- ICCID数组不能为空
- 最多10000个ICCID
- 每个ICCID必须是19-20位数字

---

### 优先级 P1 - 重要功能（4个）

#### 4. 获取入库记录详情
```
GET /api/v1/stock/in/records/{id}
```

**功能描述**：
- 获取指定入库记录的详细信息
- 包含入库的卡片列表

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "supplier_id": 1,
    "supplier_name": "供应商A",
    "package_id": 1,
    "package_name": "移动1G/月",
    "card_count": 100,
    "success_count": 98,
    "failed_count": 2,
    "test_expire_date": "2026-01-31",
    "silent_expire_date": "2026-04-30",
    "operator_id": 1,
    "operator_name": "管理员",
    "remark": "第一批入库",
    "created_at": "2026-02-09 10:00:00",
    "cards": [
      {
        "id": 1,
        "iccid": "89860123456789012345",
        "imsi": "460012345678901",
        "msisdn": "13800138000",
        "status": "stock",
        "status_name": "库存"
      }
    ]
  }
}
```

---

#### 5. 获取出库记录详情
```
GET /api/v1/stock/out/records/{id}
```

**功能描述**：
- 获取指定出库记录的详细信息
- 包含出库的卡片列表

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "user_id": 2,
    "user_name": "代理商A",
    "sale_package_id": 1,
    "sale_package_name": "移动1G/月-销售版",
    "card_count": 50,
    "success_count": 50,
    "failed_count": 0,
    "unit_price": 15.00,
    "total_amount": 750.00,
    "operator_id": 1,
    "operator_name": "管理员",
    "remark": "首次出库",
    "created_at": "2026-02-09 11:00:00",
    "cards": [
      {
        "id": 1,
        "iccid": "89860123456789012345",
        "imsi": "460012345678901",
        "msisdn": "13800138000",
        "status": "testing",
        "status_name": "测试期"
      }
    ]
  }
}
```

---

#### 6. 卡片回收
```
POST /api/v1/stock/recycle
```

**功能描述**：
- 将已出库的卡片回收到库存
- 回收后卡片状态恢复为"库存"
- 记录回收原因和操作人

**请求参数**：
```json
{
  "card_ids": [1, 2, 3],
  "recycle_reason": "客户退货",
  "remark": "批量回收"
}
```

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": 3,
    "failed": 0,
    "record_id": 1
  }
}
```

**业务逻辑**：
1. 验证卡片是否存在
2. 验证卡片是否已出库（只能回收已出库的卡片）
3. 更新卡片状态为"stock"
4. 清空卡片的user_id
5. 记录回收时间
6. 创建回收记录
7. 记录操作日志

**数据库表**: `stock_recycle_records`

---

#### 7. 获取回收记录列表
```
GET /api/v1/stock/recycle/records
```

**功能描述**：
- 分页查询回收记录列表
- 支持按时间范围筛选

**请求参数**：
```json
{
  "start_date": "2026-01-01", // 可选，开始日期
  "end_date": "2026-02-09",   // 可选，结束日期
  "page": 1,                  // 必填，页码
  "page_size": 20             // 必填，每页数量
}
```

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 10,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "card_count": 3,
        "success_count": 3,
        "failed_count": 0,
        "recycle_reason": "客户退货",
        "operator_id": 1,
        "operator_name": "管理员",
        "remark": "批量回收",
        "created_at": "2026-02-09 15:00:00"
      }
    ]
  }
}
```

---

### 优先级 P2 - 辅助功能（4个）

#### 8. 导出入库记录
```
POST /api/v1/stock/in/records/export
```

**功能描述**：
- 导出入库记录为Excel文件
- 支持按筛选条件导出

**请求参数**：
```json
{
  "supplier_id": 1,           // 可选，供应商ID
  "start_date": "2026-01-01", // 可选，开始日期
  "end_date": "2026-02-09"    // 可选，结束日期
}
```

**响应**：
- 返回Excel文件数据或JSON格式数据（前端使用xlsx库生成Excel）

**建议实现方式**：
- 方式1：后端直接返回Excel文件（推荐）
- 方式2：后端返回JSON数据，前端使用xlsx库生成Excel

---

#### 9. 导出出库记录
```
POST /api/v1/stock/out/records/export
```

**功能描述**：
- 导出出库记录为Excel文件
- 支持按筛选条件导出

**请求参数**：
```json
{
  "user_id": 2,               // 可选，目标用户ID
  "start_date": "2026-01-01", // 可选，开始日期
  "end_date": "2026-02-09"    // 可选，结束日期
}
```

---

#### 10. 导出库存数据
```
POST /api/v1/stock/inventory/export
```

**功能描述**：
- 导出库存卡片数据为Excel文件
- 支持按筛选条件导出

**请求参数**：
```json
{
  "supplier_id": 1,    // 可选，供应商ID
  "carrier": "cmcc",   // 可选，运营商
  "package_id": 1,     // 可选，套餐ID
  "sort_by": "stock_in_at",  // 可选，排序字段
  "sort_order": "desc" // 可选，排序方式
}
```

---

#### 11. 下载Excel导入模板
```
GET /api/v1/stock/import-template
```

**功能描述**：
- 下载标准的Excel导入模板
- 模板包含3列：ICCID、IMSI、电话号码

**响应**：
- 返回Excel文件

**模板格式**：
```
| ICCID                | IMSI            | 电话号码    |
|---------------------|-----------------|------------|
| 89860123456789012345| 460012345678901 | 13800138000|
| 89860123456789012346| 460012345678902 | 13800138001|
```

**实现建议**：
- 使用openpyxl或xlsxwriter库生成Excel文件
- 设置表头样式（加粗、背景色）
- 添加示例数据行
- 设置列宽自适应

---

## 📊 数据库表结构

### 1. 入库记录表 (stock_in_records)

```sql
CREATE TABLE `stock_in_records` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `supplier_id` BIGINT UNSIGNED NOT NULL COMMENT '供应商ID',
    `package_id` BIGINT UNSIGNED NOT NULL COMMENT '底层套餐ID',
    
    -- 生命周期配置
    `test_expire_date` DATE DEFAULT NULL COMMENT '测试期到期日',
    `silent_expire_date` DATE NOT NULL COMMENT '沉默期到期日',
    
    `card_count` INT NOT NULL DEFAULT 0 COMMENT '卡片数量',
    `success_count` INT NOT NULL DEFAULT 0 COMMENT '成功数量',
    `failed_count` INT NOT NULL DEFAULT 0 COMMENT '失败数量',
    `remark` VARCHAR(500) DEFAULT NULL,
    `operator_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '操作人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,
    
    PRIMARY KEY (`id`),
    KEY `idx_supplier_id` (`supplier_id`),
    KEY `idx_created_at` (`created_at`)
) COMMENT='入库记录表';
```

### 2. 出库记录表 (stock_out_records)

```sql
CREATE TABLE `stock_out_records` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT UNSIGNED NOT NULL COMMENT '目标用户ID',
    `sale_package_id` BIGINT UNSIGNED NOT NULL COMMENT '销售套餐ID',
    
    `card_count` INT NOT NULL DEFAULT 0 COMMENT '卡片数量',
    `success_count` INT NOT NULL DEFAULT 0 COMMENT '成功数量',
    `failed_count` INT NOT NULL DEFAULT 0 COMMENT '失败数量',
    `unit_price` DECIMAL(10,2) NOT NULL COMMENT '单价',
    `total_amount` DECIMAL(10,2) NOT NULL COMMENT '总金额',
    `remark` VARCHAR(500) DEFAULT NULL,
    `operator_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '操作人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,
    
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_created_at` (`created_at`)
) COMMENT='出库记录表';
```

### 3. 回收记录表 (stock_recycle_records)

```sql
CREATE TABLE `stock_recycle_records` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `card_count` INT NOT NULL DEFAULT 0 COMMENT '回收数量',
    `success_count` INT NOT NULL DEFAULT 0 COMMENT '成功数量',
    `failed_count` INT NOT NULL DEFAULT 0 COMMENT '失败数量',
    `recycle_reason` VARCHAR(500) NOT NULL COMMENT '回收原因',
    `remark` VARCHAR(500) DEFAULT NULL,
    `operator_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '操作人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` TINYINT DEFAULT 0,
    
    PRIMARY KEY (`id`),
    KEY `idx_created_at` (`created_at`)
) COMMENT='回收记录表';
```

---

## 🔄 现有接口需要调整

### 1. POST /api/v1/stock/in - 批量入库

**需要调整**：
- 入库成功后，需要创建入库记录到 `stock_in_records` 表
- 返回入库记录ID

**调整后响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": 98,
    "failed": 2,
    "record_id": 1,  // 新增：入库记录ID
    "errors": [
      {
        "iccid": "89860123456789012345",
        "reason": "ICCID已存在"
      }
    ]
  }
}
```

### 2. POST /api/v1/stock/out - 批量出库

**需要调整**：
- 出库成功后，需要创建出库记录到 `stock_out_records` 表
- 返回出库记录ID

**调整后响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": 50,
    "failed": 0,
    "record_id": 1,  // 新增：出库记录ID
    "total_amount": 750.00  // 新增：总金额
  }
}
```

---

## 📝 开发建议

### 1. 开发顺序

**第一阶段（核心功能）**：
1. 创建数据库表（stock_in_records, stock_out_records, stock_recycle_records）
2. 调整现有入库/出库接口，创建记录
3. 实现入库记录列表接口
4. 实现出库记录列表接口
5. 实现批量查询接口

**第二阶段（重要功能）**：
6. 实现入库记录详情接口
7. 实现出库记录详情接口
8. 实现卡片回收接口
9. 实现回收记录列表接口

**第三阶段（辅助功能）**：
10. 实现导出入库记录接口
11. 实现导出出库记录接口
12. 实现导出库存接口
13. 实现下载模板接口

### 2. 技术要点

**分页查询**：
- 使用SQLAlchemy的分页功能
- 返回总数、当前页、每页数量

**关联查询**：
- 入库/出库记录需要关联供应商、套餐、用户等信息
- 使用JOIN或分步查询

**批量查询优化**：
- 使用 `IN` 查询
- 注意SQL性能（最多10000个ICCID）
- 考虑使用缓存

**Excel导出**：
- 推荐使用 `openpyxl` 或 `xlsxwriter`
- 设置合适的响应头
- 考虑大数据量的流式导出

**事务处理**：
- 入库/出库/回收操作需要使用事务
- 确保数据一致性

### 3. 错误处理

**常见错误**：
- 卡片不存在
- 卡片状态不符合要求
- 权限不足
- 参数验证失败
- 数据库操作失败

**错误响应格式**：
```json
{
  "code": 400,
  "message": "操作失败",
  "data": {
    "errors": [
      {
        "field": "card_ids",
        "message": "卡片ID不能为空"
      }
    ]
  }
}
```

### 4. 权限控制

**接口权限**：
- 所有接口需要登录认证
- 入库/出库/回收操作需要管理员权限
- 记录查询需要相应的查看权限

---

## ✅ 验收标准

### 功能验收
- [ ] 所有11个接口都已实现
- [ ] 接口响应格式符合规范
- [ ] 分页功能正常
- [ ] 筛选功能正常
- [ ] 导出功能正常
- [ ] 批量查询功能正常

### 数据验收
- [ ] 入库记录正确创建
- [ ] 出库记录正确创建
- [ ] 回收记录正确创建
- [ ] 卡片状态正确更新
- [ ] 关联数据正确查询

### 性能验收
- [ ] 列表查询响应时间 < 1秒
- [ ] 批量查询10000个ICCID响应时间 < 3秒
- [ ] 导出1000条记录响应时间 < 5秒

### 安全验收
- [ ] 所有接口都有权限验证
- [ ] 参数都有验证
- [ ] SQL注入防护
- [ ] XSS防护

---

## 📚 参考文档

- [前端PRD文档](./FRONTEND_PRD.md) - 第5节：出入库管理模块
- [模块开发总结](./STOCK_MODULE_SUMMARY.md) - 前端实现详情
- [模块规划文档](./MODULE_PLAN.md) - 整体规划

---

## 📞 联系方式

如有疑问，请参考以上文档或联系前端开发团队。

**开发时间估算**: 3-5天
**优先级**: P0（高优先级）

---

**最后更新**: 2026-02-09
**文档版本**: v1.0




