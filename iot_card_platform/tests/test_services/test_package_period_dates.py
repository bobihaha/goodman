from datetime import date

import pytest

from app.services.package_period_service import PackagePeriodService
from app.utils.date_utils import calculate_expiry_date, reduce_expiry_date


class DummyValue:
    def __init__(self, value: str):
        self.value = value


class DummyCard:
    def __init__(self, period_type="monthly", period_count=12, carrier="ctcc"):
        self.period_type = DummyValue(period_type)
        self.period_count = period_count
        self.carrier = DummyValue(carrier)


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


def test_force_activate_expiry_uses_platform_activation_date_not_supplier_date():
    card = DummyCard(period_type="monthly", period_count=12, carrier="ctcc")

    assert PackagePeriodService._resolve_force_activate_expired_at(card, date(2026, 5, 11)) == date(2027, 4, 30)


class DummyForceCard:
    iccid = "8986112520609551679"
    msisdn = None


class RetryForceClient:
    def __init__(self):
        self.calls = 0
        self.last_force_activate_result = None

    async def force_activate_card(self, iccid, card_no=None):
        self.calls += 1
        if self.calls == 1:
            self.last_force_activate_result = {
                "submitted": False,
                "supplier_msg": "访问频率限制"
            }
            return False
        self.last_force_activate_result = {"submitted": True}
        return True


@pytest.mark.asyncio
async def test_force_activate_supplier_retries_rate_limit(monkeypatch):
    client = RetryForceClient()
    sleeps = []

    async def fake_sleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr("app.services.package_period_service.asyncio.sleep", fake_sleep)

    success, meta = await PackagePeriodService._call_force_activate_supplier(client, DummyForceCard())

    assert success is True
    assert client.calls == 2
    assert sleeps == [3]
    assert meta["attempts"] == 2


def test_supplier_error_text_falls_back_to_error_field():
    assert PackagePeriodService._supplier_error_text({"error": "访问频率限制"}) == "访问频率限制"
