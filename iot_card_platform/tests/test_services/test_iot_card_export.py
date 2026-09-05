from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.config import settings
from app.services.iot_card_service import IotCardService
from app.utils.exceptions import BusinessException


@pytest.mark.asyncio
async def test_export_cards_contains_full_card_and_related_account_fields(monkeypatch):
    card_data = {
        "id": 1,
        "iccid": "89860000000000000001",
        "imsi": "460001234567890",
        "msisdn": "1061234567890",
        "material_name": "塑料插拔卡",
        "card_type_name": "单卡",
        "carrier_name": "移动",
        "spec_name": "移动10G/月",
        "flow_size": 10240,
        "period_name": "月",
        "period_count": 12,
        "status_name": "已激活",
        "data_used": 128,
        "data_total": 10240,
        "data_remain": 10112,
        "data_usage_percent": 1.25,
        "activated_at": "26/7/1",
        "expired_at": "27/6/30",
        "remark": "测试卡",
        "user_id": 8,
        "sale_price": 99.8,
        "is_pool_member": True,
        "imei_separation_detected": False,
    }
    card = SimpleNamespace(to_dict=lambda: card_data.copy())
    service = IotCardService()
    service._get_accessible_user_ids = AsyncMock(return_value=None)

    async def hydrate(_db, rows, _current_user_id):
        rows[0].update({
            "related_user_id": 8,
            "related_user_name": "客户A",
            "related_user_account": "customer_a",
            "stock_out_no": "OUT20260713001",
        })

    service._hydrate_card_dicts = hydrate
    monkeypatch.setattr(
        "app.services.iot_card_service.iot_card_crud.get_by_ids",
        AsyncMock(return_value=[card]),
    )

    rows = await service.export_cards(
        db=AsyncMock(),
        current_user_id=1,
        user_level=1,
        card_ids=[1],
    )

    assert rows[0]["关联账户ID"] == 8
    assert rows[0]["关联账户名称"] == "客户A"
    assert rows[0]["关联登录账号"] == "customer_a"
    assert rows[0]["卡片类型"] == "单卡"
    assert rows[0]["本月已用流量(MB)"] == 0
    assert rows[0]["出库单号"] == "OUT20260713001"
    assert rows[0]["是否加入流量池"] == "是"
    assert rows[0]["套餐单价(元/周期)"] == 99.8


@pytest.mark.asyncio
async def test_export_cards_rejects_oversized_explicit_selection(monkeypatch):
    monkeypatch.setattr(settings, "max_export_size", 2)

    with pytest.raises(BusinessException, match="单次最多导出 2 张"):
        await IotCardService().export_cards(
            db=AsyncMock(),
            current_user_id=1,
            user_level=1,
            card_ids=[1, 2, 3],
        )


@pytest.mark.asyncio
async def test_history_export_uses_bounded_monthly_query(monkeypatch):
    service = IotCardService()
    service._get_accessible_user_ids = AsyncMock(return_value=None)
    card_data = {
        "iccid": "89860000000000000001",
        "msisdn": None,
        "imsi": None,
        "carrier_name": "移动",
        "spec_name": "移动10G/月",
        "status_name": "已激活",
        "data_total": 10240,
    }
    card = SimpleNamespace(id=1, to_dict=lambda: card_data.copy())
    get_history = AsyncMock(return_value=[])
    monkeypatch.setattr(
        "app.services.iot_card_service.iot_card_crud.get_by_ids",
        AsyncMock(return_value=[card]),
    )
    monkeypatch.setattr(
        "app.crud.iot_card_crud.card_usage_history_crud.get_cards_monthly_history",
        get_history,
    )
    monkeypatch.setattr(settings, "max_history_export_months", 3)

    rows = await service.export_cards_with_history(
        db=AsyncMock(),
        current_user_id=1,
        user_level=1,
        card_ids=[1],
        end_date="2026-09-05",
    )

    assert list(rows[0])[-3:] == ["2026-07用量(GB)", "2026-08用量(GB)", "2026-09用量(GB)"]
    assert get_history.await_count == 1
    assert get_history.await_args.args[1:] == (
        [1],
        date(2026, 7, 1),
        date(2026, 9, 5),
    )
