from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.iot_card_service import IotCardService


def test_parse_supplier_expired_at_accepts_iso_date():
    assert IotCardService._parse_supplier_expired_at("2026-11-30") == date(2026, 11, 30)


def test_parse_supplier_expired_at_rejects_invalid_value():
    assert IotCardService._parse_supplier_expired_at("2026/11/30") is None


@pytest.mark.asyncio
async def test_batch_renew_by_iccids_allows_parent_scope_cards(monkeypatch):
    service = IotCardService()
    card = SimpleNamespace(
        id=101,
        iccid="89860862102590436070",
        msisdn="13800000000",
        expired_at=date(2026, 4, 30),
        sale_package_id=88,
        carrier=SimpleNamespace(value="cmcc"),
    )
    package = SimpleNamespace(
        period_type=SimpleNamespace(value="monthly"),
        period_months=1,
        period_days=None,
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
        renew_months=1,
        current_user_id=2001,
        user_level=2,
    )

    assert result["success"] == 1
    assert result["failed"] == 0
    assert card.expired_at == date(2026, 5, 31)
    db.commit.assert_awaited_once()
    service._get_cards_by_iccids_in_scope.assert_awaited_once()


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
        user_level=2,
    )

    assert result["success"] == 1
    assert card.expired_at == date(2027, 4, 30)
    assert card.data_total == 2048
