import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.iot_card_service import IotCardService


@pytest.mark.asyncio
async def test_update_remark_records_old_and_new_values_in_same_commit():
    service = IotCardService()
    card = SimpleNamespace(
        id=317,
        iccid="89860426102580310140",
        to_dict=lambda: {"id": 317, "iccid": "89860426102580310140"},
    )
    db = MagicMock()
    db.commit = AsyncMock()

    service._get_accessible_user_ids = AsyncMock(return_value=[12])
    service._get_user_name = AsyncMock(return_value="交规院")
    service._hydrate_card_dicts = AsyncMock()

    with patch(
        "app.services.iot_card_service.iot_card_crud.get_by_id_in_scope",
        AsyncMock(return_value=card),
    ), patch(
        "app.services.iot_card_service.iot_card_crud.get_user_remark_map",
        AsyncMock(return_value={317: "旧备注"}),
    ), patch(
        "app.services.iot_card_service.iot_card_crud.upsert_user_remark",
        AsyncMock(),
    ) as mock_upsert:
        await service.update_remark(
            db=db,
            card_id=317,
            remark="新备注",
            current_user_id=12,
            user_level=2,
        )

    mock_upsert.assert_awaited_once_with(db, 317, 12, "新备注")
    db.commit.assert_awaited_once()
    audit_logs = db.add_all.call_args.args[0]
    assert len(audit_logs) == 1

    audit_log = audit_logs[0]
    assert audit_log.user_id == 12
    assert audit_log.user_name == "交规院"
    assert audit_log.module == "card"
    assert audit_log.action == "update_remark"
    assert audit_log.target_id == 317
    assert audit_log.target_name == "89860426102580310140"
    assert json.loads(audit_log.detail) == {
        "source": "system",
        "old_remark": "旧备注",
        "new_remark": "新备注",
    }


@pytest.mark.asyncio
async def test_batch_update_remark_records_each_card_once():
    service = IotCardService()
    cards = [
        SimpleNamespace(id=1, iccid="8986000000000000001"),
        SimpleNamespace(id=2, iccid="8986000000000000002"),
    ]
    db = MagicMock()
    db.commit = AsyncMock()

    service._get_accessible_user_ids = AsyncMock(return_value=[12])
    service._get_user_name = AsyncMock(return_value="交规院")

    with patch(
        "app.services.iot_card_service.iot_card_crud.get_by_ids",
        AsyncMock(return_value=cards),
    ), patch(
        "app.services.iot_card_service.iot_card_crud.get_user_remark_map",
        AsyncMock(return_value={1: "备注A", 2: "备注B"}),
    ), patch(
        "app.services.iot_card_service.iot_card_crud.upsert_user_remark",
        AsyncMock(),
    ) as mock_upsert:
        result = await service.batch_update_remark(
            db=db,
            card_ids=[1, 2],
            remark="统一备注",
            current_user_id=12,
            user_level=2,
        )

    assert result == {"success": 2, "total": 2, "failed": 0}
    assert mock_upsert.await_count == 2
    db.commit.assert_awaited_once()
    audit_logs = db.add_all.call_args.args[0]
    assert [log.target_id for log in audit_logs] == [1, 2]
    assert [json.loads(log.detail)["old_remark"] for log in audit_logs] == ["备注A", "备注B"]


@pytest.mark.asyncio
async def test_batch_remark_by_iccids_audits_duplicate_card_once():
    service = IotCardService()
    card = SimpleNamespace(id=1, iccid="8986000000000000001", msisdn="13800000001")
    db = MagicMock()
    db.commit = AsyncMock()

    service._get_cards_by_iccids_in_scope = AsyncMock(return_value=[card])
    service._get_user_name = AsyncMock(return_value="交规院")

    with patch(
        "app.services.iot_card_service.iot_card_crud.get_user_remark_map",
        AsyncMock(return_value={1: "旧备注"}),
    ), patch(
        "app.services.iot_card_service.iot_card_crud.upsert_user_remark",
        AsyncMock(),
    ) as mock_upsert:
        result = await service.batch_remark_by_iccids(
            db=db,
            iccids=[card.iccid, card.iccid],
            remark="新备注",
            current_user_id=12,
            user_level=2,
        )

    assert result["success"] == 2
    assert mock_upsert.await_count == 2
    audit_logs = db.add_all.call_args.args[0]
    assert len(audit_logs) == 1
    assert audit_logs[0].target_id == 1


def test_remark_audit_source_can_identify_h5_updates():
    db = MagicMock()
    card = SimpleNamespace(id=9, iccid="8986000000000000009")

    IotCardService._add_remark_audit_logs(
        db=db,
        cards=[card],
        current_user_id=12,
        user_name="交规院",
        old_remark_map={9: None},
        new_remark="H5备注",
        source="h5",
    )

    audit_log = db.add_all.call_args.args[0][0]
    assert json.loads(audit_log.detail)["source"] == "h5"


@pytest.mark.asyncio
async def test_update_remark_records_original_super_login_operator():
    service = IotCardService()
    card = SimpleNamespace(
        id=317,
        iccid="89860426102580310140",
        to_dict=lambda: {"id": 317, "iccid": "89860426102580310140"},
    )
    db = MagicMock()
    db.commit = AsyncMock()

    service._get_accessible_user_ids = AsyncMock(return_value=[12])
    service._get_user_name = AsyncMock(return_value="超级管理员")
    service._hydrate_card_dicts = AsyncMock()

    with patch(
        "app.services.iot_card_service.iot_card_crud.get_by_id_in_scope",
        AsyncMock(return_value=card),
    ), patch(
        "app.services.iot_card_service.iot_card_crud.get_user_remark_map",
        AsyncMock(return_value={317: "旧备注"}),
    ), patch(
        "app.services.iot_card_service.iot_card_crud.upsert_user_remark",
        AsyncMock(),
    ):
        await service.update_remark(
            db=db,
            card_id=317,
            remark="新备注",
            current_user_id=12,
            user_level=2,
            original_user_id=1,
        )

    service._get_user_name.assert_awaited_once_with(db, 1)
    audit_log = db.add_all.call_args.args[0][0]
    assert audit_log.user_id == 12
    assert audit_log.user_name == "超级管理员"
    assert audit_log.original_user_id == 1
