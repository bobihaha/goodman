"""
日期计算工具
用于计算套餐到期日期
"""
from datetime import date
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from typing import Optional


def _get_monthly_cycle_end(year: int, month: int, carrier: Optional[str]) -> date:
    """按运营商返回月包周期截止日。"""
    if carrier == "cucc":
        cycle_day = 26
    else:
        cycle_day = monthrange(year, month)[1]
    return date(year, month, cycle_day)


def calculate_expiry_date(
    start_date: date,
    period_type: str,
    period_months: Optional[int] = None,
    period_days: Optional[int] = None,
    carrier: Optional[str] = None
) -> date:
    """
    计算到期日期

    Args:
        start_date: 开始日期（激活日期）
        period_type: 周期类型 (monthly/yearly)
        period_months: 月数（月包和年包均使用，年包 1 年按 12 个月）
        period_days: 天数（年包旧数据兼容）
        carrier: 运营商编码，用于按运营商结算日计算

    Returns:
        到期日期

    Examples:
        >>> # 月包按自然月计算
        >>> calculate_expiry_date(date(2026, 4, 1), "monthly", period_months=1, carrier="cucc")
        date(2026, 4, 26)

        >>> calculate_expiry_date(date(2026, 4, 1), "monthly", period_months=1, carrier="cmcc")
        date(2026, 4, 30)

        >>> # 年包按 12 个计费月计算，首月不足 30 天也算一个月
        >>> calculate_expiry_date(date(2026, 4, 10), "yearly", period_months=12, carrier="cmcc")
        date(2027, 3, 31)
    """
    if period_type in ("monthly", "yearly"):
        if period_type == "yearly" and not period_months and period_days:
            period_months = max(1, int(period_days) // 30)
        if not period_months:
            raise ValueError("月包/年包必须提供 period_months")
        first_cycle_end = _get_monthly_cycle_end(start_date.year, start_date.month, carrier)
        if start_date > first_cycle_end:
            first_cycle_end = _get_monthly_cycle_end(
                (start_date + relativedelta(months=1)).year,
                (start_date + relativedelta(months=1)).month,
                carrier
            )

        if period_months == 1:
            return first_cycle_end

        target_month = first_cycle_end + relativedelta(months=period_months - 1)
        return _get_monthly_cycle_end(target_month.year, target_month.month, carrier)

    raise ValueError(f"不支持的周期类型: {period_type}")


def reduce_expiry_date(
    current_expiry: date,
    period_type: str,
    reduce_count: int,
    carrier: Optional[str] = None
) -> date:
    """
    按套餐周期回退到期日期。

    月包:
    - 按运营商结算日回退对应月数

    年包:
    - 按月包同口径每年回退 12 个计费月
    """
    if reduce_count <= 0:
        raise ValueError("减少周期必须大于 0")

    if period_type == "monthly":
        target_month = current_expiry + relativedelta(months=-reduce_count)
        return _get_monthly_cycle_end(target_month.year, target_month.month, carrier)

    if period_type == "yearly":
        target_month = current_expiry + relativedelta(months=-(reduce_count * 12))
        return _get_monthly_cycle_end(target_month.year, target_month.month, carrier)

    raise ValueError(f"不支持的周期类型: {period_type}")
