from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.v1.iot_card import router as iot_card_router
from app.db.models.sys_user import UserLevel
from app.services.iot_card_service import IotCardService
from app.utils.auth import require_super_admin
from app.utils.exceptions import BusinessException


def test_parse_supplier_expired_at_accepts_iso_date():
    assert IotCardService._parse_supplier_expired_at("2026-11-30") == date(2026, 11, 30)


def test_parse_supplier_expired_at_rejects_invalid_value():
    assert IotCardService._parse_supplier_expired_at("2026/11/30") is None


def test_all_renew_routes_require_super_admin():
    renew_paths = {
        "/cards/batch/renew-by-iccids",
        "/cards/batch/renew-price-query",
        "/cards/{card_id}/renew/quote",
        "/cards/{card_id}/renew",
    }
    matched_paths = set()

    for route in iot_card_router.routes:
        if route.path not in renew_paths:
            continue
        matched_paths.add(route.path)
        dependency_calls = [dependency.call for dependency in route.dependant.dependencies]
        assert require_super_admin in dependency_calls

    assert matched_paths == renew_paths


@pytest.mark.asyncio
async def test_batch_renew_by_iccids_rejects_level_two_before_mutation():
    service = IotCardService()
    card = SimpleNamespace(
        id=101,
        iccid="89860862102590436070",
        msisdn="13800000000",
        expired_at=date(2026, 4, 30),
        sale_package_id=88,
        carrier=SimpleNamespace(value="cmcc"),
    )
    db = SimpleNamespace(commit=AsyncMock())

    service._get_cards_by_iccids_in_scope = AsyncMock(return_value=[card])

    with pytest.raises(BusinessException) as exc_info:
        await service.batch_renew_by_iccids(
            db=db,
            iccids=[card.iccid],
            renew_months=1,
            current_user_id=2001,
            user_level=UserLevel.USER.value,
        )

    assert exc_info.value.code == 403
    assert card.expired_at == date(2026, 4, 30)
    db.commit.assert_not_awaited()
    service._get_cards_by_iccids_in_scope.assert_not_awaited()


@pytest.mark.asyncio
async def test_query_renew_price_rejects_level_two_before_card_query():
    service = IotCardService()
    service._get_cards_by_iccids_in_scope = AsyncMock()

    with pytest.raises(BusinessException) as exc_info:
        await service.query_renew_price(
            db=SimpleNamespace(),
            iccids=["89860862102590436070"],
            current_user_id=2001,
            user_level=UserLevel.USER.value,
        )

    assert exc_info.value.code == 403
    service._get_cards_by_iccids_in_scope.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["quote_card_renew", "purchase_card_renew"])
async def test_single_card_renew_rejects_level_two_before_card_query(method_name):
    service = IotCardService()
    db = SimpleNamespace(execute=AsyncMock(), flush=AsyncMock())

    with pytest.raises(BusinessException) as exc_info:
        await getattr(service, method_name)(
            db=db,
            card_id=101,
            renew_months=1,
            current_user_id=2001,
            user_level=UserLevel.USER.value,
        )

    assert exc_info.value.code == 403
    db.execute.assert_not_awaited()
    db.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_yearly_card_exceed_renew_starts_from_suspend_month(monkeypatch):
    service = IotCardService()
    card = SimpleNamespace(
        id=102,
        iccid="89860862102590436071",
        msisdn="13800000001",
        expired_at=date(2027, 3, 31),
        sale_package_id=89,
        carrier=SimpleNamespace(value="cmcc"),
        period_type=SimpleNamespace(value="yearly"),
        suspend_type=SimpleNamespace(value="card_exceed"),
        suspend_at=SimpleNamespace(date=lambda: date(2026, 5, 20)),
        data_total=1024,
    )
    package = SimpleNamespace(
        period_type=SimpleNamespace(value="yearly"),
        period_months=None,
        period_days=360,
        flow_size=1024,
    )
    db = SimpleNamespace(commit=AsyncMock())

    service._get_cards_by_iccids_in_scope = AsyncMock(return_value=[card])
    monkeypatch.setattr(
        "app.services.iot_card_service.sale_package_crud.get_by_id",
        AsyncMock(return_value=package),
    )
    monkeypatch.setattr(
        "app.services.iot_card_service.SysOperationLogCRUD.create",
        AsyncMock(return_value=None),
    )

    result = await service.batch_renew_by_iccids(
        db=db,
        iccids=[card.iccid],
        renew_months=12,
        current_user_id=2001,
        user_level=UserLevel.SUPER_ADMIN.value,
    )

    assert result["success"] == 1
    assert card.expired_at == date(2027, 4, 30)
    assert card.data_total == 2048
