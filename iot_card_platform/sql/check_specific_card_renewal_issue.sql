-- 续费成功但套餐周期未延长：三张指定卡核查 SQL
-- 使用前请先确认当前连接的是正确生产库 / 预发库

USE iot_card_platform;

-- 1) 卡片当前核心状态
SELECT
    id,
    iccid,
    user_id,
    status,
    supplier_id,
    sale_package_id,
    sale_price,
    period_type,
    period_count,
    activated_at,
    expired_at,
    updated_at
FROM iot_cards
WHERE iccid IN (
    '89860862102590436070',
    '89860862102590436071',
    '89860862102590436072'
)
ORDER BY iccid;

-- 2) 对应销售套餐基线
SELECT
    sp.id,
    sp.name,
    sp.period_type,
    sp.period_months,
    sp.period_days,
    sp.price_sale
FROM sale_packages sp
INNER JOIN iot_cards c ON c.sale_package_id = sp.id
WHERE c.iccid IN (
    '89860862102590436070',
    '89860862102590436071',
    '89860862102590436072'
)
ORDER BY sp.id;

-- 3) 最近续费相关操作日志
SELECT
    id,
    module,
    action,
    user_id,
    target_id,
    target_name,
    detail,
    created_at
FROM sys_operation_logs
WHERE target_name IN (
    '89860862102590436070',
    '89860862102590436071',
    '89860862102590436072'
)
AND action IN ('renew', 'card_renew_purchase')
ORDER BY id DESC
LIMIT 100;

-- 4) 最近余额扣减日志（判断是否发生过单卡购买续费）
SELECT
    id,
    module,
    action,
    user_id,
    target_id,
    target_name,
    detail,
    created_at
FROM sys_operation_logs
WHERE module = 'balance'
AND action = 'consume'
AND target_name IN (
    '89860862102590436070',
    '89860862102590436071',
    '89860862102590436072'
)
ORDER BY id DESC
LIMIT 100;

-- 5) 若怀疑“父账号续下级卡被误判 0 成功”，检查这三张卡归属用户
SELECT
    c.iccid,
    c.user_id,
    u.account,
    u.name,
    u.parent_id,
    u.user_level
FROM iot_cards c
LEFT JOIN sys_users u ON u.id = c.user_id
WHERE c.iccid IN (
    '89860862102590436070',
    '89860862102590436071',
    '89860862102590436072'
)
ORDER BY c.iccid;

-- 6) 如果日志里显示“续费成功”但 iot_cards.expired_at 未变化，
--    先不要直接手改数据，优先重新发起一次续费请求验证修复是否生效。
--    如确需手工修复，请先备份并结合实际旧到期日、新周期人工确认。
