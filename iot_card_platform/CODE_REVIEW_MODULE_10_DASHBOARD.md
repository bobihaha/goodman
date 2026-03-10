# 模块10: Dashboard仪表盘模块 - 代码审查报告

**审查时间**: 2026-03-07
**优先级**: 🟡 MEDIUM
**审查状态**: ✅ 已完成

---

## 📋 审查范围

### 后端文件
- `app/api/v1/dashboard.py` - Dashboard API层
- `app/services/dashboard_service.py` - Dashboard服务层

---

## 🔴 CRITICAL 问题

### 1. API路由重复定义
**文件**: `app/api/v1/dashboard.py:129-323`
**问题**: 多个API端点重复定义4-5次
**风险**: 路由冲突，最后定义的会覆盖前面的

**受影响的端点**:
- `/account/balance` (4次重复: 129, 178, 227, 276)
- `/pools/usage-percent` (5次重复: 139, 188, 237, 286)
- `/cards/expiring` (5次重复: 152, 201, 250, 299)
- `/cards/over-usage` (5次重复: 165, 214, 263, 312)

**修复**: 删除重复定义，每个端点只保留一次

---

## 🟠 HIGH 问题

### 2. 服务层方法重复定义
**文件**: `app/services/dashboard_service.py:343-881`
**问题**: 多个方法重复定义4-5次
**风险**: 代码冗余，维护困难

**重复方法**:
- `get_account_balance` (5次: 343, 479, 614, 749)
- `get_pools_usage_percent` (5次: 359, 494, 629, 764)
- `get_expiring_cards` (5次: 391, 526, 661, 796)
- `get_over_usage_cards` (5次: 436, 571, 706, 841)

**修复**: 删除重复定义，每个方法只保留一次

---

### 3. 超量卡查询性能问题
**文件**: `app/services/dashboard_service.py:450-476`
**问题**: 查询所有激活卡片后在内存中过滤
**风险**: 数据量大时内存占用高，性能差

**建议**: 使用SQL过滤
```python
# 使用SQL计算使用率并过滤
from sqlalchemy import case

usage_percent_expr = case(
    (IotCardModel.data_total > 0, IotCardModel.data_used * 100.0 / IotCardModel.data_total),
    else_=0
)

result = await db.execute(
    select(IotCardModel)
    .where(
        *base_condition,
        usage_percent_expr > 100
    )
    .order_by((IotCardModel.data_used - IotCardModel.data_total).desc())
    .limit(50)
)
```

---

## 🟡 MEDIUM 问题

### 4. 流量趋势数据模拟
**文件**: `app/services/dashboard_service.py:232-274`
**问题**: 趋势数据是模拟的，不是真实历史数据
**建议**: 添加流量历史记录表

---

### 5. 账户余额返回模拟数据
**文件**: `app/services/dashboard_service.py:343-357`
**问题**: 返回硬编码的模拟数据
**建议**: 实现真实的账户余额表

---

## 🟢 LOW 问题

### 6. 用户名和套餐名为空
**文件**: `app/services/dashboard_service.py:430-432`
**问题**: 返回的卡片信息中用户名和套餐名为空字符串
**建议**: 通过JOIN查询关联数据

---

## ✅ 优点

1. ✅ 权限控制清晰（管理员vs普通用户）
2. ✅ 统计维度全面（卡片、用户、套餐、流量池、告警）
3. ✅ 分页和限制合理

---

## 📊 问题统计

| 级别 | 数量 |
|------|------|
| 🔴 CRITICAL | 1 |
| 🟠 HIGH | 2 |
| 🟡 MEDIUM | 2 |
| 🟢 LOW | 1 |
