from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app import scheduler as scheduler_module
from app.db.models.iot_card import CardStatus, CardType, IotCardModel, SuspendType
from app.db.models.package import CarrierType, PeriodType
from app.db.models.suspend import SuspendActionType, SuspendPolicyModel
from app.services.suspend_service import SuspendActionService
from tests.conftest import TestSessionLocal


def test_start_scheduler_registers_non_overlapping_card_exceed_job():
    with patch.object(scheduler_module.scheduler, "add_job") as add_job, patch.object(
        scheduler_module.scheduler, "start"
    ) as start:
        scheduler_module.start_scheduler()

    jobs = {call.kwargs["id"]: call for call in add_job.call_args_list}
    card_exceed_job = jobs["card_exceed_auto_suspend"]
    assert card_exceed_job.args[0] is scheduler_module.check_card_exceed
    assert "minute='*/5'" in str(card_exceed_job.args[1])
    assert card_exceed_job.kwargs["replace_existing"] is True
    assert card_exceed_job.kwargs["max_instances"] == 1
    assert card_exceed_job.kwargs["coalesce"] is True
    assert card_exceed_job.kwargs["misfire_grace_time"] == 300
    start.assert_called_once_with()


@pytest.mark.asyncio
async def test_card_exceed_job_rolls_back_when_check_fails():
    db = MagicMock()
    db.rollback = AsyncMock()
    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=db)
    session_context.__aexit__ = AsyncMock(return_value=None)

    with patch.object(
        scheduler_module, "AsyncSessionLocal", return_value=session_context
    ), patch.object(
        SuspendActionService,
        "auto_suspend_card_exceed",
        AsyncMock(side_effect=RuntimeError("check failed")),
    ):
        await scheduler_module.check_card_exceed()

    db.rollback.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_supplier_reconcile_preserves_card_exceed_suspend_type():
    card = SimpleNamespace(
        id=1337,
        iccid="8986112521408934064",
        supplier_id=2,
        status=CardStatus.suspended,
        suspend_type=SuspendType.card_exceed,
        suspend_at=None,
        suspend_reason="单卡流量超限",
    )
    operation = SimpleNamespace(
        id=81,
        card_id=card.id,
        supplier_id=2,
        action=SuspendActionType.suspend,
        callback_status="pending",
        request_result='{"submitted": true}',
    )
    supplier = SimpleNamespace(
        id=2,
        api_url="",
        api_key="",
        api_secret="",
        code="upiot",
        api_config=None,
    )
    supplier_result = MagicMock()
    supplier_result.scalar_one_or_none.return_value = supplier
    db = MagicMock()
    db.get = AsyncMock(return_value=card)
    db.execute = AsyncMock(return_value=supplier_result)
    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=db)
    session_context.__aexit__ = AsyncMock(return_value=None)
    supplier_client = MagicMock()
    supplier_client.get_card_lifecycle = AsyncMock(return_value={"status": CardStatus.suspended.value})

    with patch("app.services.suspend_service.asyncio.sleep", AsyncMock()), patch(
        "app.services.suspend_service.AsyncSessionLocal", return_value=session_context
    ), patch(
        "app.services.suspend_service.SupplierSuspendOperationCRUD.get_by_callback_no",
        AsyncMock(return_value=operation),
    ), patch(
        "app.services.suspend_service.SupplierSuspendOperationCRUD.update_request_result",
        AsyncMock(),
    ), patch(
        "app.services.suspend_service.SupplierSuspendOperationCRUD.update_callback_result",
        AsyncMock(),
    ), patch(
        "app.services.suspend_service.get_supplier_client", return_value=supplier_client
    ), patch.object(
        SuspendActionService, "_safe_update_supplier_action_audit", AsyncMock()
    ):
        await SuspendActionService._run_pending_operation_reconcile("callback-81", 0)

    assert card.suspend_type == SuspendType.card_exceed


@pytest.mark.asyncio
async def test_card_exceed_prefers_user_policy_and_uses_its_stop_threshold(setup_database):
    async with TestSessionLocal() as db:
        card = IotCardModel(
            id=1337,
            iccid="8986112521408934064",
            user_id=33,
            supplier_id=2,
            carrier=CarrierType.ctcc,
            flow_size=10240,
            period_type=PeriodType.monthly,
            period_count=12,
            card_type=CardType.single,
            data_used=9728,
            data_used_month=9728,
            data_total=10240,
            status=CardStatus.activated,
            is_pool_member=0,
        )
        global_policy = SuspendPolicyModel(
            id=1,
            name="全局策略",
            policy_type="card_exceed",
            warning_threshold=80,
            critical_threshold=90,
            stop_threshold=100,
            auto_suspend=1,
            is_enabled=1,
        )
        user_policy = SuspendPolicyModel(
            id=2,
            name="客户策略",
            policy_type="card_exceed",
            user_id=33,
            warning_threshold=70,
            critical_threshold=80,
            stop_threshold=90,
            auto_suspend=1,
            is_enabled=1,
        )
        db.add_all([card, global_policy, user_policy])
        await db.commit()

        with patch.object(
            SuspendActionService,
            "_load_supplier_map",
            AsyncMock(return_value={2: MagicMock()}),
        ), patch.object(
            SuspendActionService,
            "_call_supplier_suspend",
            AsyncMock(return_value=(True, "callback-1", None)),
        ) as supplier_suspend, patch(
            "app.services.suspend_service.CardSuspendCRUD.suspend_card",
            AsyncMock(),
        ) as suspend_card, patch(
            "app.services.suspend_service.SuspendLogCRUD.create",
            AsyncMock(),
        ) as create_log, patch(
            "app.services.suspend_service.AlertLogCRUD.check_exists",
            AsyncMock(return_value=False),
        ), patch.object(
            SuspendActionService,
            "_create_alert_and_notify",
            AsyncMock(),
        ) as create_alert, patch(
            "app.services.suspend_service.NotificationService.send_pending_usage_alerts_for_user",
            AsyncMock(return_value=True),
        ):
            result = await SuspendActionService.auto_suspend_card_exceed(db)

    assert result == {"suspended_count": 1, "alerts_created": 1}
    supplier_suspend.assert_awaited_once()
    assert suspend_card.await_args.kwargs["card_id"] == 1337
    assert create_log.await_args.kwargs["policy_id"] == 2
    assert create_alert.await_args.kwargs["threshold"] == 90
