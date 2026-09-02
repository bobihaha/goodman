import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.models.iot_card import CardStatus, SuspendType
from app.db.models.suspend import SuspendActionType, SuspendLogModel
from app.services.h5_service import H5Service
from app.services.suspend_service import SuspendActionService


@pytest.mark.asyncio
async def test_h5_suspend_links_operation_log_to_supplier_request():
    service = H5Service()
    user = SimpleNamespace(id=2, name="客户", h5_allow_suspend=1)
    card = SimpleNamespace(
        id=24,
        iccid="898604F21023C0012037",
        status=CardStatus.activated,
        supplier_id=1,
    )
    audit_log = SimpleNamespace(id=88)
    db = MagicMock()

    service._get_h5_user = AsyncMock(return_value=user)
    service._get_card_in_scope = AsyncMock(return_value=card)
    service._get_pending_action = AsyncMock(return_value=None)
    service._create_action_audit_log = AsyncMock(return_value=audit_log)

    with patch.object(
        SuspendActionService,
        "_load_supplier_map",
        AsyncMock(return_value={1: SimpleNamespace(id=1)}),
    ), patch.object(
        SuspendActionService,
        "_call_supplier_suspend",
        AsyncMock(return_value=(True, "sus-callback", None)),
    ) as mock_suspend:
        result = await service.suspend_card(db, "slug", card.id, "客户申请")

    assert result["status"] == "processing"
    context = mock_suspend.await_args.kwargs["request_context"]
    assert context == {
        "audit_source": "h5",
        "audit_log_id": 88,
        "audit_action": "suspend",
        "audit_phase": "suspend",
        "audit_reason": "客户申请",
    }


@pytest.mark.asyncio
async def test_h5_suspend_applies_immediately_reconciled_status():
    service = H5Service()
    user = SimpleNamespace(id=2, name="客户", h5_allow_suspend=1)
    card = SimpleNamespace(
        id=24,
        iccid="898604F21023C0012037",
        status=CardStatus.activated,
        suspend_type=SuspendType.none,
        suspend_at=None,
        suspend_reason=None,
        supplier_id=1,
        pool_id=88,
    )
    db = MagicMock(commit=AsyncMock(), refresh=AsyncMock())

    service._get_h5_user = AsyncMock(return_value=user)
    service._get_card_in_scope = AsyncMock(return_value=card)
    service._get_pending_action = AsyncMock(return_value=None)
    service._create_action_audit_log = AsyncMock(return_value=SimpleNamespace(id=88))

    with patch.object(
        SuspendActionService,
        "_load_supplier_map",
        AsyncMock(return_value={1: SimpleNamespace(id=1)}),
    ), patch.object(
        SuspendActionService,
        "_call_supplier_suspend",
        AsyncMock(return_value=(True, "sus-callback", CardStatus.suspended.value)),
    ), patch.object(
        SuspendActionService,
        "_safe_refresh_pool_stats",
        AsyncMock(),
    ) as refresh_pool_stats:
        result = await service.suspend_card(db, "slug", card.id, "客户申请")

    assert result["status"] == "success"
    assert result["message"] == "停机成功"
    assert card.status == CardStatus.suspended
    assert card.suspend_type == SuspendType.manual
    assert card.suspend_reason == "客户申请"
    db.commit.assert_awaited_once()
    refresh_pool_stats.assert_awaited_once_with(db, {88})


@pytest.mark.asyncio
async def test_h5_resume_applies_immediately_reconciled_status():
    service = H5Service()
    user = SimpleNamespace(id=2, name="客户", h5_allow_resume=1)
    card = SimpleNamespace(
        id=24,
        iccid="898604F21023C0012037",
        status=CardStatus.suspended,
        suspend_type=SuspendType.manual,
        suspend_at=None,
        suspend_reason="客户申请",
        supplier_id=1,
        pool_id=None,
    )
    db = MagicMock(commit=AsyncMock(), refresh=AsyncMock())

    service._get_h5_user = AsyncMock(return_value=user)
    service._get_card_in_scope = AsyncMock(return_value=card)
    service._get_pending_action = AsyncMock(return_value=None)
    service._create_action_audit_log = AsyncMock(return_value=SimpleNamespace(id=89))

    with patch.object(
        SuspendActionService,
        "_check_resume_eligibility",
        AsyncMock(return_value=(True, None)),
    ), patch.object(
        SuspendActionService,
        "_load_supplier_map",
        AsyncMock(return_value={1: SimpleNamespace(id=1)}),
    ), patch.object(
        SuspendActionService,
        "_call_supplier_resume",
        AsyncMock(return_value=(True, "res-callback", CardStatus.activated.value)),
    ):
        result = await service.resume_card(db, "slug", card.id)

    assert result["status"] == "success"
    assert result["message"] == "复机成功"
    assert card.status == CardStatus.activated
    assert card.suspend_type == SuspendType.none
    assert card.suspend_reason is None
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_h5_resume_reuses_pending_restart_resume_request():
    service = H5Service()
    user = SimpleNamespace(id=2, name="客户", h5_allow_resume=1)
    card = SimpleNamespace(
        id=24,
        iccid="898604F21023C0012037",
        status=CardStatus.suspended,
    )
    pending_operation = SimpleNamespace(
        action=SuspendActionType.resume,
        callback_no="res-existing",
        request_result=json.dumps({
            "audit_source": "h5",
            "audit_action": "restart",
            "audit_phase": "resume",
        }),
    )
    db = MagicMock()

    service._get_h5_user = AsyncMock(return_value=user)
    service._get_card_in_scope = AsyncMock(return_value=card)
    service._get_pending_action = AsyncMock(return_value=pending_operation)

    with patch.object(
        SuspendActionService,
        "_call_supplier_resume",
        AsyncMock(),
    ) as mock_resume:
        result = await service.resume_card(db, "slug", card.id)

    assert result["status"] == "processing"
    assert result["callback_no"] == "res-existing"
    assert "请勿重复提交" in result["message"]
    mock_resume.assert_not_awaited()


@pytest.mark.asyncio
async def test_h5_supplier_success_finalizes_operation_and_suspend_log():
    detail = {
        "source": "h5",
        "status": "processing",
        "reason": "客户申请",
        "phases": {},
    }
    operation_log = SimpleNamespace(
        action="suspend",
        detail=json.dumps(detail, ensure_ascii=False),
        is_success=1,
        error_msg=None,
    )
    operation = SimpleNamespace(
        card_id=24,
        iccid="898604F21023C0012037",
        action=SuspendActionType.suspend,
        callback_no="sus-callback",
        operator_id=2,
        request_result=None,
    )
    request_meta = {
        "audit_source": "h5",
        "audit_log_id": 88,
        "audit_action": "suspend",
        "audit_phase": "suspend",
        "audit_reason": "客户申请",
    }
    db = MagicMock()
    db.get = AsyncMock(return_value=operation_log)
    db.commit = AsyncMock()

    await SuspendActionService._update_supplier_action_audit(
        db=db,
        request_meta=request_meta,
        status="success",
        callback_no="sus-callback",
        supplier_status="suspended",
        operation=operation,
    )

    updated_detail = json.loads(operation_log.detail)
    assert updated_detail["status"] == "success"
    assert updated_detail["phases"]["suspend"]["supplier_status"] == "suspended"
    assert request_meta["audit_suspend_finalized"] is True
    added_objects = [call.args[0] for call in db.add.call_args_list]
    suspend_log = next(item for item in added_objects if isinstance(item, SuspendLogModel))
    assert suspend_log.action == SuspendActionType.suspend
    assert suspend_log.operator_id == 2


@pytest.mark.asyncio
async def test_restart_suspend_phase_keeps_log_processing():
    operation_log = SimpleNamespace(
        action="restart",
        detail=json.dumps({"source": "h5", "status": "processing", "phases": {}}),
        is_success=1,
        error_msg=None,
    )
    operation = SimpleNamespace(
        card_id=24,
        iccid="898604F21023C0012037",
        action=SuspendActionType.suspend,
        callback_no="sus-restart",
        operator_id=2,
        request_result=None,
    )
    request_meta = {
        "audit_source": "h5",
        "audit_log_id": 89,
        "audit_action": "restart",
        "audit_phase": "suspend",
        "audit_reason": "H5重启",
    }
    db = MagicMock()
    db.get = AsyncMock(return_value=operation_log)
    db.commit = AsyncMock()

    await SuspendActionService._update_supplier_action_audit(
        db=db,
        request_meta=request_meta,
        status="success",
        callback_no="sus-restart",
        supplier_status="suspended",
        operation=operation,
    )

    updated_detail = json.loads(operation_log.detail)
    assert updated_detail["status"] == "processing"
    assert updated_detail["current_phase"] == "resume_pending"


@pytest.mark.asyncio
async def test_duplicate_supplier_success_does_not_duplicate_suspend_log():
    operation_log = SimpleNamespace(
        action="resume",
        detail=json.dumps({"source": "h5", "status": "processing", "phases": {}}),
        is_success=1,
        error_msg=None,
    )
    db = MagicMock()
    db.get = AsyncMock(return_value=operation_log)
    db.commit = AsyncMock()

    for callback_no in ("res-first", "res-retry"):
        operation = SimpleNamespace(
            card_id=24,
            iccid="898604F21023C0012037",
            action=SuspendActionType.resume,
            callback_no=callback_no,
            operator_id=2,
            request_result=None,
        )
        request_meta = {
            "audit_source": "h5",
            "audit_log_id": 90,
            "audit_action": "resume",
            "audit_phase": "resume",
            "audit_reason": "H5手动复机",
        }
        await SuspendActionService._update_supplier_action_audit(
            db=db,
            request_meta=request_meta,
            status="success",
            callback_no=callback_no,
            supplier_status="activated",
            operation=operation,
        )

    added_objects = [call.args[0] for call in db.add.call_args_list]
    suspend_logs = [item for item in added_objects if isinstance(item, SuspendLogModel)]
    assert len(suspend_logs) == 1


@pytest.mark.asyncio
async def test_audit_failure_isolated_from_supplier_action_result():
    db = MagicMock()
    db.rollback = AsyncMock()

    with patch.object(
        SuspendActionService,
        "_update_supplier_action_audit",
        AsyncMock(side_effect=RuntimeError("audit unavailable")),
    ):
        await SuspendActionService._safe_update_supplier_action_audit(
            db=db,
            request_meta={"audit_source": "h5", "audit_log_id": 91},
            status="processing",
        )

    db.rollback.assert_awaited_once()
