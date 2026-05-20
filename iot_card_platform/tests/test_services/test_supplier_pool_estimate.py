from calendar import monthrange
from datetime import datetime

from app.services.supplier_pool_service import SupplierTrafficPoolService


def test_month_estimate_uses_elapsed_days_and_month_days():
    now = datetime.now()
    sync_at = datetime(now.year, now.month, 10, 12, 0, 0)
    month_days = monthrange(sync_at.year, sync_at.month)[1]

    result = SupplierTrafficPoolService._month_estimate_fields(
        used_flow=100,
        total_flow=500,
        sync_at=sync_at,
        record_month=sync_at.strftime("%Y-%m"),
    )

    expected_used = 100 / 10 * month_days
    assert result["estimated_monthly_used_flow"] == expected_used
    assert result["estimated_month_end_remaining_flow"] == 500 - expected_used
    assert result["estimated_usage_percent"] == round(expected_used / 500 * 100, 2)
    assert result["estimate_used_days"] == 10
    assert result["estimate_month_days"] == month_days


def test_month_estimate_is_only_returned_for_current_month_history():
    result = SupplierTrafficPoolService._month_estimate_fields(
        used_flow=100,
        total_flow=500,
        sync_at=datetime(2026, 4, 10, 12, 0, 0),
        record_month="2000-01",
    )

    assert result["estimated_monthly_used_flow"] is None
    assert result["estimated_month_end_remaining_flow"] is None
    assert result["estimated_usage_percent"] is None
