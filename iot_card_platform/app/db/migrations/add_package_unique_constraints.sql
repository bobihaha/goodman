-- 套餐管理 - 规格三要素唯一约束
-- 修复日期: 2026-03-07

-- 1. 供应商套餐: 同一供应商下，运营商+流量+周期类型 必须唯一
ALTER TABLE supplier_packages
ADD CONSTRAINT uq_supplier_spec UNIQUE (supplier_id, carrier, flow_size, period_type);

-- 2. 销售套餐: 同一用户下，运营商+流量+周期类型 必须唯一
ALTER TABLE sale_packages
ADD CONSTRAINT uq_sale_spec UNIQUE (user_id, carrier, flow_size, period_type);
