from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.models.iot_card import CardStatus
from app.db.models.sys_user import UserLevel, UserStatus
from app.schemas.suspend import ManualSuspend
from app.services.iot_card_service import IotCardService
from app.services.suspend_service import SuspendActionService


@pytest.mark.asyncio
async def test_manual_suspend_adds_user_visible_operation_log():
    card = SimpleNamespace(
        id=317,
        iccid="89860426102580310140",
        status=CardStatus.activated,
        supplier_id=1,
    )
    db = MagicMock()

    with patch(
        "app.services.suspend_service.CardSuspendCRUD.get_cards_by_ids",
        AsyncMock(return_value=[card]),
    ), patch.object(
        SuspendActionService,
        "_load_supplier_map",
        AsyncMock(return_value={}),
    ), patch.object(
        SuspendActionService,
        "_call_supplier_suspend",
        AsyncMock(return_value=(True, "callback-1", None)),
    ), patch(
        "app.services.suspend_service.CardSuspendCRUD.suspend_card",
        AsyncMock(),
    ), patch(
        "app.services.suspend_service.SuspendLogCRUD.create",
        AsyncMock(),
    ):
        result = await SuspendActionService.manual_suspend(
            db=db,
            data=ManualSuspend(card_ids=[317], reason="客户手动停机"),
            operator_id=12,
            user_id=12,
            user_ids=[12],
            operator_name="交规院",
            original_user_id=1,
        )

    assert result.success_count == 1
    operation_log = db.add.call_args.args[0]
    assert operation_log.user_id == 12
    assert operation_log.user_name == "交规院"
    assert operation_log.original_user_id == 1
    assert operation_log.action == "suspend"
    assert operation_log.target_id == 317


@pytest.mark.asyncio
async def test_transfer_to_child_adds_card_operation_log():
    service = IotCardService()
    target_user = SimpleNamespace(
        id=13,
        name="子账户",
        parent_id=12,
        status=UserStatus.enable,
    )
    target_result = MagicMock()
    target_result.scalar_one_or_none.return_value = target_user
    db = MagicMock()
    db.execute = AsyncMock(return_value=target_result)
    card = SimpleNamespace(
        id=317,
        iccid="89860426102580310140",
        to_dict=lambda: {"id": 317, "iccid": "89860426102580310140"},
    )

    service._get_user_name = AsyncMock(return_value="交规院")
    with patch(
        "app.services.iot_card_service.iot_card_crud.transfer",
        AsyncMock(return_value=card),
    ), patch(
        "app.services.iot_card_service.SysOperationLogCRUD.create",
        AsyncMock(),
    ) as mock_log_create:
        await service.transfer_card(
            db=db,
            card_id=317,
            to_user_id=13,
            current_user_id=12,
            user_level=UserLevel.USER.value,
            remark="项目卡",
            original_user_id=1,
        )

    service._get_user_name.assert_awaited_once_with(db, 1)
    assert mock_log_create.await_args.kwargs["action"] == "transfer"
    assert mock_log_create.await_args.kwargs["target_id"] == 317
    assert mock_log_create.await_args.kwargs["original_user_id"] == 1


@pytest.mark.asyncio
async def test_batch_suspend_by_iccids_keeps_original_operator():
    service = IotCardService()
    card = SimpleNamespace(id=317, iccid="89860426102580310140", msisdn="13800138000")
    db = MagicMock()
    service._get_cards_by_iccids_in_scope = AsyncMock(return_value=[card])
    service._get_accessible_user_ids = AsyncMock(return_value=[12, 13])
    service._get_user_name = AsyncMock(return_value="平台管理员")
    suspend_result = SimpleNamespace(success_cards=[card.iccid], fail_cards=[])

    with patch.object(
        SuspendActionService,
        "manual_suspend",
        AsyncMock(return_value=suspend_result),
    ) as mock_suspend:
        result = await service.batch_suspend_by_iccids(
            db=db,
            iccids=[card.iccid],
            reason="客户要求停机",
            current_user_id=12,
            user_level=UserLevel.USER.value,
            original_user_id=1,
        )

    assert result["success"] == 1
    service._get_user_name.assert_awaited_once_with(db, 1)
    assert mock_suspend.await_args.kwargs["operator_name"] == "平台管理员"
    assert mock_suspend.await_args.kwargs["original_user_id"] == 1
