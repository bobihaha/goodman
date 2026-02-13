-- 流量池阈值字段更新
-- 将原来的2个阈值字段改为3个阈值字段

-- 1. 添加新的3个阈值字段
ALTER TABLE traffic_pools 
ADD COLUMN alert_threshold_1 INT NULL COMMENT '告警阈值1百分比',
ADD COLUMN alert_threshold_2 INT NULL COMMENT '告警阈值2百分比',
ADD COLUMN alert_threshold_3 INT NULL COMMENT '告警阈值3百分比';

-- 2. 迁移旧数据（如果存在）
-- 将 alert_threshold 的值迁移到 alert_threshold_1
-- 将 stop_threshold 的值迁移到 alert_threshold_3
UPDATE traffic_pools 
SET 
    alert_threshold_1 = alert_threshold,
    alert_threshold_3 = stop_threshold
WHERE alert_threshold IS NOT NULL OR stop_threshold IS NOT NULL;

-- 3. 删除旧字段
ALTER TABLE traffic_pools 
DROP COLUMN alert_threshold,
DROP COLUMN stop_threshold;


-- 将原来的2个阈值字段改为3个阈值字段

-- 1. 添加新的3个阈值字段
ALTER TABLE traffic_pools 
ADD COLUMN alert_threshold_1 INT NULL COMMENT '告警阈值1百分比',
ADD COLUMN alert_threshold_2 INT NULL COMMENT '告警阈值2百分比',
ADD COLUMN alert_threshold_3 INT NULL COMMENT '告警阈值3百分比';

-- 2. 迁移旧数据（如果存在）
-- 将 alert_threshold 的值迁移到 alert_threshold_1
-- 将 stop_threshold 的值迁移到 alert_threshold_3
UPDATE traffic_pools 
SET 
    alert_threshold_1 = alert_threshold,
    alert_threshold_3 = stop_threshold
WHERE alert_threshold IS NOT NULL OR stop_threshold IS NOT NULL;

-- 3. 删除旧字段
ALTER TABLE traffic_pools 
DROP COLUMN alert_threshold,
DROP COLUMN stop_threshold;


-- 将原来的2个阈值字段改为3个阈值字段

-- 1. 添加新的3个阈值字段
ALTER TABLE traffic_pools 
ADD COLUMN alert_threshold_1 INT NULL COMMENT '告警阈值1百分比',
ADD COLUMN alert_threshold_2 INT NULL COMMENT '告警阈值2百分比',
ADD COLUMN alert_threshold_3 INT NULL COMMENT '告警阈值3百分比';

-- 2. 迁移旧数据（如果存在）
-- 将 alert_threshold 的值迁移到 alert_threshold_1
-- 将 stop_threshold 的值迁移到 alert_threshold_3
UPDATE traffic_pools 
SET 
    alert_threshold_1 = alert_threshold,
    alert_threshold_3 = stop_threshold
WHERE alert_threshold IS NOT NULL OR stop_threshold IS NOT NULL;

-- 3. 删除旧字段
ALTER TABLE traffic_pools 
DROP COLUMN alert_threshold,
DROP COLUMN stop_threshold;


-- 将原来的2个阈值字段改为3个阈值字段

-- 1. 添加新的3个阈值字段
ALTER TABLE traffic_pools 
ADD COLUMN alert_threshold_1 INT NULL COMMENT '告警阈值1百分比',
ADD COLUMN alert_threshold_2 INT NULL COMMENT '告警阈值2百分比',
ADD COLUMN alert_threshold_3 INT NULL COMMENT '告警阈值3百分比';

-- 2. 迁移旧数据（如果存在）
-- 将 alert_threshold 的值迁移到 alert_threshold_1
-- 将 stop_threshold 的值迁移到 alert_threshold_3
UPDATE traffic_pools 
SET 
    alert_threshold_1 = alert_threshold,
    alert_threshold_3 = stop_threshold
WHERE alert_threshold IS NOT NULL OR stop_threshold IS NOT NULL;

-- 3. 删除旧字段
ALTER TABLE traffic_pools 
DROP COLUMN alert_threshold,
DROP COLUMN stop_threshold;



