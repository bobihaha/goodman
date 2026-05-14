from datetime import datetime
from types import SimpleNamespace

import pytest

from app.crud.stock_crud import StockSummaryCRUD
from app.services.stock_service import StockService, _storage_time_to_china_string


def test_stock_batch_query_normalizes_input_order_and_duplicates():
    normalized, duplicates = StockSummaryCRUD._parse_iccid_query([
        " 8986112520609490919 ",
        "",
        "8986112520609490920",
        "8986112520609490919",
    ])

    assert normalized == [
        "8986112520609490919",
        "8986112520609490920",
    ]
    assert duplicates == ["8986112520609490919"]


def test_stock_time_is_returned_as_china_time():
    assert _storage_time_to_china_string(datetime(2026, 5, 14, 9, 29, 38)) == "2026-05-14 17:29:38"


@pytest.mark.asyncio
async def test_enriched_stock_card_formats_stock_in_at_as_china_time():
    card = SimpleNamespace(
        to_dict=lambda: {
            "id": 1,
            "stock_in_at": "2026-05-14T09:29:38",
            "stock_out_at": None,
            "created_at": "2026-05-14T09:29:38",
            "updated_at": "2026-05-14T09:29:38",
        },
        stock_in_at=datetime(2026, 5, 14, 9, 29, 38),
        stock_out_at=None,
        created_at=datetime(2026, 5, 14, 9, 29, 38),
        updated_at=datetime(2026, 5, 14, 9, 29, 38),
        supplier_id=None,
        batch_id=None,
    )

    data = await StockService()._enrich_stock_card(db=None, item=card)

    assert data["stock_in_at"] == "2026-05-14 17:29:38"
