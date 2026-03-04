-- 套餐周期字段迁移脚本
-- 将 effective_days 迁移到 period_months/period_days

-- 1. 添加新字段到 supplier_packages 表
ALTER TABLE supplier_packages
ADD COLUMN period_months INT NULL COMMENT '套餐周期(月) - 月包使用' AFTER period_type,
ADD COLUMN period_days INT NULL COMMENT '套餐周期(天) - 年包使用' AFTER period_months;

-- 2. 添加新字段到 sale_packages 表
ALTER TABLE sale_packages
ADD COLUMN period_months INT NULL COMMENT '套餐周期(月) - 月包使用' AFTER period_type,
ADD COLUMN period_days INT NULL COMMENT '套餐周期(天) - 年包使用' AFTER period_months;

-- 3. 迁移 supplier_packages 数据
-- 月包：将天数转换为月数（向上取整）
UPDATE supplier_packages
SET period_months = CEIL(effective_days / 30.0),
    period_days = NULL
WHERE period_type = 'monthly' AND effective_days IS NOT NULL;

-- 年包：直接使用天数
UPDATE supplier_packages
SET period_days = effective_days,
    period_months = NULL
WHERE period_type = 'yearly' AND effective_days IS NOT NULL;

-- 4. 迁移 sale_packages 数据
-- 月包
UPDATE sale_packages
SET period_months = CEIL(effective_days / 30.0),
    period_days = NULL
WHERE period_type = 'monthly' AND effective_days IS NOT NULL;

-- 年包
UPDATE sale_packages
SET period_days = effective_days,
    period_months = NULL
WHERE period_type = 'yearly' AND effective_days IS NOT NULL;

-- 5. 修改 effective_days 字段为可空（保留用于兼容）
ALTER TABLE supplier_packages
MODIFY COLUMN effective_days INT NULL COMMENT '[已废弃]激活后有效天数';

ALTER TABLE sale_packages
MODIFY COLUMN effective_days INT NULL COMMENT '[已废弃]激活后有效天数';

-- 6. 验证迁移结果
SELECT
    period_type,
    COUNT(*) as count,
    COUNT(period_months) as has_months,
    COUNT(period_days) as has_days
FROM supplier_packages
WHERE is_deleted = 0
GROUP BY period_type;

SELECT
    period_type,
    COUNT(*) as count,
    COUNT(period_months) as has_months,
    COUNT(period_days) as has_days
FROM sale_packages
WHERE is_deleted = 0
GROUP BY period_type;
