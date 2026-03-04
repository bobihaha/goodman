"""
日期计算工具
用于计算套餐到期日期
"""
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional


def calculate_expiry_date(
    start_date: date,
    period_type: str,
    period_months: Optional[int] = None,
    period_days: Optional[int] = None
) -> date:
    """
    计算到期日期

    Args:
        start_date: 开始日期（激活日期）
        period_type: 周期类型 (monthly/yearly)
        period_months: 月数（月包使用）
        period_days: 天数（年包使用）

    Returns:
        到期日期

    Examples:
        >>> # 月包按自然月计算
        >>> calculate_expiry_date(date(2026, 1, 31), "monthly", period_months=1)
        date(2026, 2, 28)

        >>> calculate_expiry_date(date(2026, 3, 1), "monthly", period_months=1)
        date(2026, 4, 1)

        >>> # 年包按固定天数计算
        >>> calculate_expiry_date(date(2026, 1, 1), "yearly", period_days=360)
        date(2026, 12, 27)
    """
    if period_type == "monthly":
        if not period_months:
            raise ValueError("月包必须提供 period_months")
        return start_date + relativedelta(months=period_months)
    elif period_type == "yearly":
        if not period_days:
            raise ValueError("年包必须提供 period_days")
        return start_date + timedelta(days=period_days)
    else:
        raise ValueError(f"不支持的周期类型: {period_type}")
