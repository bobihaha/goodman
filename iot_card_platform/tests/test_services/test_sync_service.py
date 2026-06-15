from datetime import date

import pytest

from app.db.models.iot_card import CardStatus, SuspendType
from app.services.sync_service import SyncService


class DummyStatus:
    def __init__(self, value: str):
        self.value = value


class DummyCard:
    def __init__(
        self,
        expired_at=None,
        period_type="yearly",
        data_total=0,
        flow_size=0,
        data_used=0,
        data_used_month=0,
        period_count=1,
        carrier="cmcc",
        sale_package_id=1
    ):
        self.expired_at = expired_at
        self.status = DummyStatus("activated")
        self.period_type = DummyStatus(period_type)
        self.period_count = period_count
        self.carrier = DummyStatus(carrier)
        self.data_total = data_total
        self.flow_size = flow_size
        self.data_used = data_used
        self.data_used_month = data_used_month
        self.addon_flow = 0
        self.addon_flow_month = None
        self.activated_at = None
        self.sale_package_id = sale_package_id
        self.suspend_type = SuspendType.none
        self.suspend_at = None
        self.suspend_reason = None


def test_resolve_lifecycle_expired_at_prefers_supplier_when_longer():
    card = DummyCard(date(2027, 3, 31))

    resolved, preserved = SyncService._resolve_lifecycle_expired_at(card, date(2027, 8, 31))

    assert resolved == date(2027, 8, 31)
    assert preserved is False


def test_resolve_lifecycle_expired_at_preserves_local_when_supplier_is_shorter():
    card = DummyCard(date(2028, 1, 31))

    resolved, preserved = SyncService._resolve_lifecycle_expired_at(card, date(2027, 8, 31))

    assert resolved == date(2028, 1, 31)
    assert preserved is True


def test_protect_sales_period_expired_at_raises_supplier_short_cycle():
    card = DummyCard(
        expired_at=date(2026, 6, 30),
        period_type="monthly",
        period_count=3,
        carrier="ctcc",
        sale_package_id=29,
    )
    card.activated_at = date(2026, 6, 15)

    protected = SyncService._protect_sales_period_expired_at(card)

    assert protected is True
    assert card.expired_at == date(2026, 8, 31)


def test_protect_sales_period_expired_at_keeps_supplier_longer_cycle():
    card = DummyCard(
        expired_at=date(2026, 9, 30),
        period_type="monthly",
        period_count=3,
        carrier="ctcc",
        sale_package_id=29,
    )
    card.activated_at = date(2026, 6, 15)

    protected = SyncService._protect_sales_period_expired_at(card)

    assert protected is False
    assert card.expired_at == date(2026, 9, 30)


def test_protect_sales_period_expired_at_skips_cards_without_sale_package():
    card = DummyCard(
        expired_at=date(2026, 6, 30),
        period_type="monthly",
        period_count=3,
        carrier="ctcc",
        sale_package_id=None,
    )
    card.activated_at = date(2026, 6, 15)

    protected = SyncService._protect_sales_period_expired_at(card)

    assert protected is False
    assert card.expired_at == date(2026, 6, 30)


def test_resolve_lifecycle_activated_at_ignores_supplier_test_activation_date():
    card = DummyCard()
    card.activated_at = None

    resolved, ignored = SyncService._resolve_lifecycle_activated_at(card, date(2025, 11, 17))

    assert resolved is None
    assert ignored is True


def test_resolve_lifecycle_activated_at_preserves_local_platform_date():
    card = DummyCard()
    card.activated_at = date(2026, 5, 11)

    resolved, ignored = SyncService._resolve_lifecycle_activated_at(card, date(2025, 11, 17))

    assert resolved == date(2026, 5, 11)
    assert ignored is True


def test_apply_resolved_lifecycle_status_clears_stale_supplier_suspend_state():
    card = DummyCard()
    card.status = CardStatus.suspended
    card.suspend_type = SuspendType.none
    card.suspend_at = date(2026, 4, 27)
    card.suspend_reason = "供应商状态同步为停机"

    SyncService._apply_resolved_lifecycle_status(card, CardStatus.activated.value)

    assert card.status == CardStatus.activated
    assert card.suspend_type == SuspendType.none
    assert card.suspend_at is None
    assert card.suspend_reason is None


def test_extract_lifecycle_from_usage_reuses_supplier_snapshot():
    usage_data = {
        "iccid": "8986",
        "data_used": 10,
        "status": CardStatus.activated.value,
        "activated_at": "2026-05-01",
        "expired_at": "2027-05-01",
    }

    lifecycle = SyncService._extract_lifecycle_from_usage(usage_data, "fallback")

    assert lifecycle == {
        "iccid": "8986",
        "activated_at": "2026-05-01",
        "expired_at": "2027-05-01",
        "status": CardStatus.activated.value,
    }


@pytest.mark.asyncio
async def test_resolve_lifecycle_status_preserves_business_suspend():
    service = SyncService()
    card = DummyCard()
    card.suspend_type = SuspendType.manual

    resolved = await service._resolve_lifecycle_status(None, card, CardStatus.activated.value)

    assert resolved == CardStatus.suspended.value


@pytest.mark.asyncio
async def test_resolve_lifecycle_status_ignores_unknown_supplier_status():
    service = SyncService()
    card = DummyCard()
    card.status = CardStatus.activated

    resolved = await service._resolve_lifecycle_status(None, card, "unknown")

    assert resolved == CardStatus.activated.value


def test_resolve_usage_data_total_preserves_yearly_local_renew_total():
    card = DummyCard(period_type="yearly", data_total=2048, flow_size=1024)

    resolved, preserved = SyncService._resolve_usage_data_total(card, 1024)

    assert resolved == 2048
    assert preserved is True


def test_resolve_usage_data_total_accepts_supplier_when_yearly_total_is_higher():
    card = DummyCard(period_type="yearly", data_total=1024, flow_size=1024)

    resolved, preserved = SyncService._resolve_usage_data_total(card, 2048)

    assert resolved == 2048
    assert preserved is False


def test_resolve_usage_data_total_monthly_keeps_at_least_package_flow():
    card = DummyCard(period_type="monthly", data_total=512, flow_size=1024)

    resolved, preserved = SyncService._resolve_usage_data_total(card, 512)

    assert resolved == 1024
    assert preserved is False


def test_resolve_usage_data_used_monthly_uses_supplier_value():
    card = DummyCard(period_type="monthly", data_used=50, data_used_month=50)

    resolved, month_used, reset = SyncService._resolve_usage_data_used(card, 60)

    assert resolved == 60
    assert month_used == 60
    assert reset is False


def test_resolve_usage_data_used_yearly_accumulates_month_delta():
    card = DummyCard(period_type="yearly", data_used=30, data_used_month=24)

    resolved, month_used, reset = SyncService._resolve_usage_data_used(card, 36, supplier_usage_scope="month")

    assert resolved == 42
    assert month_used == 36
    assert reset is False


def test_resolve_usage_data_used_yearly_accumulates_after_month_reset():
    card = DummyCard(period_type="yearly", data_used=36, data_used_month=30)

    resolved, month_used, reset = SyncService._resolve_usage_data_used(card, 6, supplier_usage_scope="month")

    assert resolved == 42
    assert month_used == 6
    assert reset is True


def test_resolve_usage_data_used_yearly_initializes_month_baseline_without_double_count():
    card = DummyCard(period_type="yearly", data_used=36, data_used_month=0)

    resolved, month_used, reset = SyncService._resolve_usage_data_used(card, 12, supplier_usage_scope="month")

    assert resolved == 36
    assert month_used == 12
    assert reset is False


def test_resolve_usage_data_used_yearly_accepts_cycle_usage():
    card = DummyCard(period_type="yearly", data_used=16, data_used_month=0)

    resolved, month_used, reset = SyncService._resolve_usage_data_used(
        card,
        35.926,
        supplier_used_month=15.532,
        supplier_usage_scope="cycle"
    )

    assert resolved == 36
    assert month_used == 16
    assert reset is False
