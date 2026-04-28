from datetime import date

from app.utils.date_utils import calculate_expiry_date, reduce_expiry_date


def test_calculate_expiry_date_yearly_uses_twelve_billing_months_cmcc():
    assert calculate_expiry_date(date(2026, 4, 10), "yearly", period_months=12, carrier="cmcc") == date(2027, 3, 31)


def test_calculate_expiry_date_yearly_uses_twelve_billing_months_cucc():
    assert calculate_expiry_date(date(2026, 4, 10), "yearly", period_months=12, carrier="cucc") == date(2027, 3, 26)


def test_reduce_expiry_date_monthly_cmcc():
    assert reduce_expiry_date(date(2026, 11, 30), "monthly", 1, "cmcc") == date(2026, 10, 31)


def test_reduce_expiry_date_monthly_cucc():
    assert reduce_expiry_date(date(2026, 11, 26), "monthly", 1, "cucc") == date(2026, 10, 26)


def test_reduce_expiry_date_yearly():
    assert reduce_expiry_date(date(2027, 3, 31), "yearly", 1, "cmcc") == date(2026, 3, 31)
