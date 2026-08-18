from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.db.models.iot_card import CardStatus, CardType, SuspendType
from app.schemas.package_period import BatchForceActivateRequest
from app.services.package_period_service import PackagePeriodService
from app.utils.date_utils import calculate_expiry_date, reduce_expiry_date
from app.utils.exceptions import BusinessException


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


def _build_simboss_silent_pool_card():
    return SimpleNamespace(
        id=101,
        iccid="8986032341202053098",
        msisdn="1064983512508",
        status=CardStatus.silent,
        supplier_id=2,
        activated_at=None,
        expired_at=None,
        period_type=DummyValue("monthly"),
        period_count=12,
        carrier=DummyValue("ctcc"),
        sale_package_id=88,
        card_type=CardType.pool,
        pool_id=None,
        is_pool_member=0,
        user_id=50,
        suspend_type=SuspendType.none,
        suspend_at=None,
        suspend_reason=None,
    )


@pytest.mark.asyncio
async def test_simboss_manual_pool_join_does_not_commit_early():
    card = _build_simboss_silent_pool_card()
    sale_package = SimpleNamespace(id=88)
    pool = SimpleNamespace(id=46)
    package_result = SimpleNamespace(scalar_one_or_none=lambda: sale_package)
    db = SimpleNamespace(
        execute=AsyncMock(return_value=package_result),
        add=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
    )

    with patch.object(
        PackagePeriodService,
        "_find_or_create_change_pool",
        new=AsyncMock(return_value=pool),
    ), patch(
        "app.services.package_period_service.pool_crud.update_stats",
        new=AsyncMock(return_value=pool),
    ) as update_stats:
        await PackagePeriodService._join_manual_force_activated_card_to_pool(
            db=db,
            card=card,
            operator_id=1,
        )

    assert card.pool_id == 46
    assert card.is_pool_member == 1
    db.flush.assert_awaited_once()
    db.commit.assert_not_awaited()
    update_stats.assert_awaited_once_with(
        db,
        46,
        commit=False,
        run_checks=False,
    )


@pytest.mark.asyncio
async def test_simboss_existing_pool_refreshes_stats_after_activation():
    card = _build_simboss_silent_pool_card()
    card.pool_id = 46
    db = SimpleNamespace(flush=AsyncMock(), commit=AsyncMock())
    pool = SimpleNamespace(id=46)

    with patch(
        "app.services.package_period_service.pool_crud.update_stats",
        new=AsyncMock(return_value=pool),
    ) as update_stats:
        await PackagePeriodService._join_manual_force_activated_card_to_pool(
            db=db,
            card=card,
            operator_id=1,
        )

    assert card.pool_id == 46
    assert card.is_pool_member == 1
    db.flush.assert_awaited_once()
    db.commit.assert_not_awaited()
    update_stats.assert_awaited_once_with(
        db,
        46,
        commit=False,
        run_checks=False,
    )


@pytest.mark.asyncio
async def test_simboss_existing_pool_requires_customer():
    card = _build_simboss_silent_pool_card()
    card.pool_id = 46
    card.user_id = None
    db = SimpleNamespace(flush=AsyncMock())

    with patch(
        "app.services.package_period_service.pool_crud.update_stats",
        new=AsyncMock(),
    ) as update_stats:
        with pytest.raises(BusinessException, match="SIMBOSS 流量池卡未关联客户"):
            await PackagePeriodService._join_manual_force_activated_card_to_pool(
                db=db,
                card=card,
                operator_id=1,
            )

    db.flush.assert_not_awaited()
    update_stats.assert_not_awaited()


@pytest.mark.asyncio
async def test_simboss_force_activate_only_updates_local_state_and_joins_pool():
    card = _build_simboss_silent_pool_card()
    supplier = SimpleNamespace(code="002")
    db = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock(), refresh=AsyncMock())

    async def join_pool(db, card, operator_id):
        card.pool_id = 46
        card.is_pool_member = 1

    with patch.object(
        PackagePeriodService, "_load_cards_by_iccids", new=AsyncMock(return_value=[card])
    ), patch.object(
        PackagePeriodService, "_load_supplier_map", new=AsyncMock(return_value={2: supplier})
    ), patch.object(
        PackagePeriodService, "_add_operation_log", new=Mock()
    ) as add_log, patch(
        "app.services.package_period_service.get_supplier_client"
    ) as get_supplier_client, patch.object(
        PackagePeriodService, "_join_manual_force_activated_card_to_pool",
        new=AsyncMock(side_effect=join_pool),
    ) as auto_join_pool:
        result = await PackagePeriodService.batch_force_activate(
            db=db,
            data=BatchForceActivateRequest(iccids=[card.iccid], reason="供应商已人工激活"),
            operator_id=1,
            operator_name="管理员",
        )

    assert result["success"] == 1
    assert result["failed"] == 0
    assert result["success_list"][0]["pool_id"] == 46
    assert result["success_list"][0]["supplier_result"]["manual_supplier_activation"] is True
    assert card.status == CardStatus.activated
    assert card.activated_at == date.today()
    assert card.pool_id == 46
    get_supplier_client.assert_not_called()
    auto_join_pool.assert_awaited_once_with(db=db, card=card, operator_id=1)
    assert "manual_supplier_confirmed" in add_log.call_args.kwargs["detail"]
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_simboss_force_activate_rolls_back_when_pool_join_fails():
    card = _build_simboss_silent_pool_card()
    supplier = SimpleNamespace(code="002")
    db = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock(), refresh=AsyncMock())

    with patch.object(
        PackagePeriodService, "_load_cards_by_iccids", new=AsyncMock(return_value=[card])
    ), patch.object(
        PackagePeriodService, "_load_supplier_map", new=AsyncMock(return_value={2: supplier})
    ), patch(
        "app.services.package_period_service.get_supplier_client"
    ) as get_supplier_client, patch.object(
        PackagePeriodService, "_join_manual_force_activated_card_to_pool",
        new=AsyncMock(side_effect=BusinessException(code=400, msg="SIMBOSS 卡本地激活后自动加入流量池失败")),
    ):
        result = await PackagePeriodService.batch_force_activate(
            db=db,
            data=BatchForceActivateRequest(iccids=[card.iccid]),
            operator_id=1,
            operator_name="管理员",
        )

    assert result["success"] == 0
    assert result["failed"] == 1
    assert result["failed_list"][0]["error"] == "SIMBOSS 卡本地激活后自动加入流量池失败"
    get_supplier_client.assert_not_called()
    db.commit.assert_not_awaited()
    db.rollback.assert_awaited_once()
