from datetime import date, datetime

import pytest

from app.db.models.iot_card import CardStatus, SuspendType
from app.flow_packages import get_current_flow_cycle_month
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
        sale_package_id=1,
        stock_out_date=None,
        data_usage_month=None,
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
        self.data_usage_month = data_usage_month
        self.data_sync_at = None
        self.data_source_at = None
        self.addon_flow = 0
        self.addon_flow_month = None
        self.activated_at = None
        self.stock_out_date = stock_out_date
        self.test_expire_date = None
        self.silent_expire_date = None
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


def test_resolve_lifecycle_expired_at_repairs_supplier_longer_than_local_sale_period():
    card = DummyCard(
        expired_at=date(2026, 12, 26),
        period_type="monthly",
        period_count=6,
        carrier="cucc",
        sale_package_id=22,
        stock_out_date=date(2026, 1, 15),
    )
    card.activated_at = date(2026, 1, 15)

    resolved, preserved = SyncService._resolve_lifecycle_expired_at(card, date(2026, 12, 26))

    assert resolved == date(2026, 6, 26)
    assert preserved is True


def test_active_status_without_supplier_activation_date_still_repairs_expiry():
    card = DummyCard(
        expired_at=date(2026, 12, 26),
        period_type="monthly",
        period_count=6,
        carrier="cucc",
        sale_package_id=22,
        stock_out_date=date(2026, 1, 15),
    )
    card.status = CardStatus.activated

    filled = SyncService._ensure_activated_at_for_active_status(card)
    resolved, preserved = SyncService._resolve_lifecycle_expired_at(card, date(2026, 12, 26))

    assert filled is True
    assert card.activated_at == date(2026, 1, 15)
    assert resolved == date(2026, 6, 26)
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


def test_resolve_lifecycle_activated_at_uses_local_stock_out_date():
    card = DummyCard(stock_out_date=date(2026, 1, 15))

    resolved, ignored = SyncService._resolve_lifecycle_activated_at(card, date(2026, 1, 15))

    assert resolved == date(2026, 1, 15)
    assert ignored is True


def test_resolve_supplier_lifecycle_date_preserves_stock_out_local_date():
    card = DummyCard(stock_out_date=date(2026, 1, 15))
    card.test_expire_date = date(2026, 1, 20)

    resolved, preserved = SyncService._resolve_supplier_lifecycle_date(
        card,
        "test_expire_date",
        date(2025, 12, 27),
    )

    assert resolved == date(2026, 1, 20)
    assert preserved is True


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
@pytest.mark.parametrize("supplier_status", [CardStatus.expired, CardStatus.cancelled])
async def test_resolve_lifecycle_status_allows_supplier_terminal_status(supplier_status):
    service = SyncService()
    card = DummyCard()
    card.suspend_type = SuspendType.manual

    resolved = await service._resolve_lifecycle_status(None, card, supplier_status.value)

    assert resolved == supplier_status.value


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


def test_resolve_usage_data_total_monthly_ignores_supplier_yearly_total():
    card = DummyCard(period_type="monthly", data_total=24576, flow_size=10240)

    resolved, preserved = SyncService._resolve_usage_data_total(card, 24576)

    assert resolved == 10240
    assert preserved is False


def test_resolve_usage_data_total_monthly_uses_local_flow_when_supplier_total_missing():
    card = DummyCard(period_type="monthly", data_total=24576, flow_size=10240)

    resolved, preserved = SyncService._resolve_usage_data_total(card, None)

    assert resolved == 10240
    assert preserved is False


def test_resolve_usage_data_total_monthly_adds_current_local_topup():
    card = DummyCard(period_type="monthly", data_total=12288, flow_size=10240)
    card.addon_flow = 2048
    card.addon_flow_month = get_current_flow_cycle_month()

    resolved, preserved = SyncService._resolve_usage_data_total(card, 24576)

    assert resolved == 12288
    assert preserved is False


def test_resolve_usage_data_total_yearly_does_not_repeat_addon():
    card = DummyCard(period_type="yearly", data_total=12288, flow_size=10240)
    card.addon_flow = 2048
    card.addon_flow_month = get_current_flow_cycle_month()

    first, _ = SyncService._resolve_usage_data_total(card, 10240)
    card.data_total = first
    second, _ = SyncService._resolve_usage_data_total(card, 10240)

    assert first == 12288
    assert second == 12288


def test_resolve_usage_data_used_monthly_uses_supplier_value():
    card = DummyCard(period_type="monthly", data_used=50, data_used_month=50)

    resolved, month_used, reset = SyncService._resolve_usage_data_used(card, 60)

    assert resolved == 60
    assert month_used == 60
    assert reset is False


def test_resolve_usage_data_used_monthly_uses_month_value_for_supplier_year_cycle():
    card = DummyCard(period_type="monthly", data_used=3072, data_used_month=3072)

    resolved, month_used, reset = SyncService._resolve_usage_data_used(
        card,
        supplier_used=8192,
        supplier_used_month=512,
        supplier_usage_scope="cycle",
    )

    assert resolved == 512
    assert month_used == 512
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


def test_apply_usage_snapshot_rejects_previous_month_for_monthly_card():
    card = DummyCard(period_type="monthly", data_used=15040, data_total=10240, flow_size=10240)

    accepted, _, _, reason = SyncService._apply_usage_snapshot(card, {
        "data_used": 15040,
        "data_total": 10240,
        "sync_time": "2000-01-31 23:59:59",
    })

    assert accepted is False
    assert reason == "供应商仍返回 2000-01 用量"
    assert card.data_used == 0
    assert card.data_used_month == 0
    assert card.data_total == 10240
    assert card.data_usage_month is None
    assert card.data_source_at == datetime(2000, 1, 31, 23, 59, 59)


def test_yearly_month_usage_uses_explicit_source_month():
    card = DummyCard(
        period_type="yearly",
        data_used=136,
        data_used_month=36,
        data_usage_month="2026-08",
    )

    resolved, month_used, reset = SyncService._resolve_usage_data_used(
        card,
        6,
        supplier_usage_scope="month",
        supplier_usage_month="2026-09",
    )

    assert resolved == 142
    assert month_used == 6
    assert reset is True
