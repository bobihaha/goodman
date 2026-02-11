# 卡片列表功能完善 - 快速修复指南

## 错误原因
前端访问 `/api/v1/cards` 接口时返回500错误，原因是数据库缺少新添加的字段：
- `card_type` - 卡片类型
- `data_used_month` - 本月用量

## 修复步骤

### 1. 执行数据库迁移

打开MySQL客户端，执行以下SQL：

```sql
USE iot_card_platform;

-- 添加卡片类型字段
ALTER TABLE `iot_cards` 
ADD COLUMN `card_type` ENUM('single', 'pool') NOT NULL DEFAULT 'single' 
COMMENT '卡片类型: single=单卡(达量停机), pool=流量池卡' 
AFTER `period_type`;

-- 添加本月用量字段
ALTER TABLE `iot_cards` 
ADD COLUMN `data_used_month` BIGINT NOT NULL DEFAULT 0 
COMMENT '本月已用流量(MB)' 
AFTER `data_total`;

-- 为现有数据设置默认值
UPDATE `iot_cards` 
SET `card_type` = CASE 
    WHEN `is_pool_member` = 1 THEN 'pool' 
    ELSE 'single' 
END;

-- 初始化本月用量
UPDATE `iot_cards` 
SET `data_used_month` = `data_used`;
```

或者直接执行脚本文件：
```bash
mysql -u root -p iot_card_platform < scripts/MANUAL_ADD_FIELDS.sql
```

### 2. 重启后端服务

```bash
cd /Users/huiren/Documents/goodman/iot_card_platform
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 刷新前端页面

访问卡片列表页面，应该可以正常显示了。

## 新增功能说明

### 新增的列
1. **卡片类型** - 显示"单卡"或"流量池卡"
2. **本月用量** - 显示本月已用流量
3. **套餐总量** - 显示套餐总流量
4. **已用量** - 显示累计已用流量
5. **测试期** - 显示测试期到期日
6. **沉默期** - 显示沉默期到期日
7. **激活日期** - 显示激活日期
8. **出库日期** - 显示出库日期

### 批量操作增强
所有批量操作（划拨、备注、续费、停机、复机）都支持：
- ✅ 粘贴ICCID列表（每行一个或逗号分隔）
- ✅ 不需要勾选卡片
- ✅ 自动去重
- ✅ 显示成功/失败详情
- ✅ 复制失败的ICCID

## 验证

执行以下SQL验证字段是否添加成功：

```sql
DESCRIBE iot_cards;
```

应该能看到 `card_type` 和 `data_used_month` 字段。

