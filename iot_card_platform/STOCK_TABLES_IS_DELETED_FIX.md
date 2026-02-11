# 库存记录表 is_deleted 字段缺失问题修复

## 问题描述

**错误信息：**
```
sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError) (1054, "Unknown column 'is_deleted' in 'field list'")
[SQL: INSERT INTO stock_in_record_cards (record_id, card_id, iccid, is_deleted) VALUES (%s, %s, %s, %s)]
```

**发生时间：** 2026-02-10 11:27:55

**触发操作：** 执行入库操作时，尝试向 `stock_in_record_cards` 表插入数据

## 根本原因

1. **模型定义问题：**
   - `StockInRecordCardModel`、`StockOutRecordCardModel`、`StockRecycleRecordCardModel` 都继承自 `BaseModel`
   - `BaseModel` 包含 `is_deleted` 字段定义
   
2. **数据库表结构问题：**
   - 数据库中的三个关联表缺少 `is_deleted` 字段：
     - `stock_in_record_cards`
     - `stock_out_record_cards`
     - `stock_recycle_record_cards`

3. **不一致原因：**
   - 可能是创建表时使用了原始SQL而非ORM迁移
   - 或者创建表后修改了 `BaseModel` 但未同步数据库

## 解决方案

### 方案1：修改数据库表结构（已采用）

为三个表添加缺失的 `is_deleted` 字段：

```sql
-- 1. stock_in_record_cards
ALTER TABLE stock_in_record_cards 
ADD COLUMN is_deleted TINYINT DEFAULT 0 COMMENT '删除标记：0=未删除，1=已删除';

-- 2. stock_out_record_cards
ALTER TABLE stock_out_record_cards 
ADD COLUMN is_deleted TINYINT DEFAULT 0 COMMENT '删除标记：0=未删除，1=已删除';

-- 3. stock_recycle_record_cards
ALTER TABLE stock_recycle_record_cards 
ADD COLUMN is_deleted TINYINT DEFAULT 0 COMMENT '删除标记：0=未删除，1=已删除';
```

### 执行步骤

1. **创建修复脚本：** `fix_tables.py`
   ```python
   import asyncio
   from sqlalchemy import text
   from app.db.database import AsyncSessionLocal

   async def fix_tables():
       sqls = [
           "ALTER TABLE stock_in_record_cards ADD COLUMN is_deleted TINYINT DEFAULT 0 COMMENT '删除标记：0=未删除，1=已删除'",
           "ALTER TABLE stock_out_record_cards ADD COLUMN is_deleted TINYINT DEFAULT 0 COMMENT '删除标记：0=未删除，1=已删除'",
           "ALTER TABLE stock_recycle_record_cards ADD COLUMN is_deleted TINYINT DEFAULT 0 COMMENT '删除标记：0=未删除，1=已删除'"
       ]
       
       async with AsyncSessionLocal() as db:
           for sql in sqls:
               await db.execute(text(sql))
               await db.commit()
   
   if __name__ == "__main__":
       asyncio.run(fix_tables())
   ```

2. **执行修复：**
   ```bash
   cd /Users/huiren/Documents/goodman/iot_card_platform
   source venv/bin/activate
   python fix_tables.py
   ```

3. **执行结果：**
   ```
   ✓ 执行成功: ALTER TABLE stock_in_record_cards ADD COL...
   ✓ 执行成功: ALTER TABLE stock_out_record_cards ADD CO...
   ✓ 执行成功: ALTER TABLE stock_recycle_record_cards AD...
   
   修复完成！
   ```

## 验证

修复后的表结构：

```sql
-- stock_in_record_cards
+------------+------------+------+-----+---------+----------------+
| Field      | Type       | Null | Key | Default | Extra          |
+------------+------------+------+-----+---------+----------------+
| id         | bigint     | NO   | PRI | NULL    | auto_increment |
| record_id  | bigint     | NO   | MUL | NULL    |                |
| card_id    | bigint     | NO   | MUL | NULL    |                |
| iccid      | varchar(30)| NO   |     | NULL    |                |
| created_at | datetime   | YES  |     | NULL    |                |
| updated_at | datetime   | YES  |     | NULL    |                |
| is_deleted | tinyint    | YES  |     | 0       |                |
+------------+------------+------+-----+---------+----------------+
```

## 影响范围

- **受影响的表：** 3个
  - `stock_in_record_cards`
  - `stock_out_record_cards`
  - `stock_recycle_record_cards`

- **受影响的功能：**
  - ✅ 入库操作（创建入库记录和卡片关联）
  - ✅ 出库操作（创建出库记录和卡片关联）
  - ✅ 回收操作（创建回收记录和卡片关联）

## 预防措施

1. **使用ORM迁移工具：**
   - 建议使用 Alembic 进行数据库迁移
   - 确保模型定义和数据库结构同步

2. **代码审查：**
   - 创建新模型时，检查是否正确继承 `BaseModel`
   - 创建数据库表时，确保包含所有基类字段

3. **测试覆盖：**
   - 添加集成测试，验证数据库操作
   - 测试应覆盖所有CRUD操作

## 相关文件

- **模型定义：** `app/db/models/stock.py`
- **基础模型：** `app/db/models/base.py`
- **CRUD操作：** `app/crud/stock_crud.py`
- **修复脚本：** `fix_tables.py`
- **SQL脚本：** `fix_stock_record_cards_tables.sql`

## 总结

此问题是由于数据库表结构与ORM模型定义不一致导致的。通过为三个关联表添加 `is_deleted` 字段，使其与 `BaseModel` 的定义保持一致，成功解决了入库操作失败的问题。

**修复时间：** 2026-02-10 11:39:09
**修复状态：** ✅ 已完成


