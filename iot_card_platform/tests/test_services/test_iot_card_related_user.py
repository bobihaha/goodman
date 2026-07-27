from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.crud.sys_user_crud_enhanced import SysUserCRUDEnhanced
from app.services.iot_card_service import IotCardService


def _user(user_id, name, account, user_level, parent_id=None):
    return SimpleNamespace(
        id=user_id,
        name=name,
        account=account,
        user_level=user_level,
        parent_id=parent_id,
    )


def _scalar_result(items):
    result = MagicMock()
    result.scalars.return_value.all.return_value = items
    return result


@pytest.mark.asyncio
async def test_super_admin_sees_level_two_parent_for_sub_user_card(monkeypatch):
    admin = _user(1, "超级管理员", "admin", 1)
    parent = _user(14, "上海翕禾传媒科技有限公司", "customer", 2, 1)
    child = _user(15, "浦东融媒体", "sub_user", 3, 14)
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _scalar_result([admin, child]),
        _scalar_result([parent]),
    ])
    service = IotCardService()
    service._get_stock_out_no_map = AsyncMock(return_value={})
    monkeypatch.setattr(
        "app.services.iot_card_service.iot_card_crud.get_user_remark_map",
        AsyncMock(return_value={}),
    )
    rows = [{"id": 660, "user_id": 15}]

    await service._hydrate_card_dicts(db, rows, current_user_id=1)

    assert rows[0]["user_id"] == 15
    assert rows[0]["related_user_id"] == 14
    assert rows[0]["related_user_name"] == "上海翕禾传媒科技有限公司"
    assert rows[0]["related_user_account"] == "customer"


@pytest.mark.asyncio
async def test_level_two_user_still_sees_actual_sub_user(monkeypatch):
    parent = _user(14, "上海翕禾传媒科技有限公司", "customer", 2, 1)
    child = _user(15, "浦东融媒体", "sub_user", 3, 14)
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_result([parent, child]))
    service = IotCardService()
    service._get_stock_out_no_map = AsyncMock(return_value={})
    monkeypatch.setattr(
        "app.services.iot_card_service.iot_card_crud.get_user_remark_map",
        AsyncMock(return_value={}),
    )
    rows = [{"id": 660, "user_id": 15}]

    await service._hydrate_card_dicts(db, rows, current_user_id=14)

    assert rows[0]["related_user_id"] == 15
    assert rows[0]["related_user_name"] == "浦东融媒体"
    assert rows[0]["related_user_account"] == "sub_user"
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_super_admin_customer_filter_includes_sub_users(monkeypatch):
    service = IotCardService()
    db = AsyncMock()
    service._get_accessible_user_ids = AsyncMock(return_value=None)
    service._hydrate_card_dicts = AsyncMock()
    monkeypatch.setattr(
        SysUserCRUDEnhanced,
        "get_children_ids",
        AsyncMock(return_value=[15]),
    )
    get_list = AsyncMock(return_value=([], 0))
    monkeypatch.setattr("app.services.iot_card_service.iot_card_crud.get_list", get_list)

    await service.get_cards(
        db=db,
        current_user_id=1,
        user_level=1,
        customer_id=14,
    )

    assert get_list.await_args.kwargs["user_ids"] == [14, 15]
    assert get_list.await_args.kwargs["customer_id"] is None
