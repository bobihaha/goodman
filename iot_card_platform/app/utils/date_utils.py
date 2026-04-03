"""
日期计算工具
用于计算套餐到期日期
"""
from datetime import date, timedelta
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
        period_months: 月数（月包使用）
        period_days: 天数（年包使用）
        carrier: 运营商编码，月包用于按运营商结算日计算

    Returns:
        到期日期

    Examples:
        >>> # 月包按自然月计算
        >>> calculate_expiry_date(date(2026, 4, 1), "monthly", period_months=1, carrier="cucc")
        date(2026, 4, 26)

        >>> calculate_expiry_date(date(2026, 4, 1), "monthly", period_months=1, carrier="cmcc")
        date(2026, 4, 30)

        >>> # 年包按固定天数计算
        >>> calculate_expiry_date(date(2026, 1, 1), "yearly", period_days=360)
        date(2026, 12, 27)
    """
    if period_type == "monthly":
        if not period_months:
            raise ValueError("月包必须提供 period_months")
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
    elif period_type == "yearly":
        if not period_days:
            raise ValueError("年包必须提供 period_days")
        return start_date + timedelta(days=period_days)
    else:
        raise ValueError(f"不支持的周期类型: {period_type}")
