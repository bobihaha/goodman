from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.iot_card_service import IotCardService


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
