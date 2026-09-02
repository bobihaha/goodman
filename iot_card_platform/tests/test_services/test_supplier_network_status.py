import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.config import settings
from app.crud.pool_crud import pool_crud
from app.db.models.iot_card import CardStatus, CardType, IotCardModel, SuspendType
from app.db.models.suspend import SuspendActionType, SuspendLogModel
from app.services.suspend_service import SuspendActionService


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (CardStatus.activated, "open"),
        (CardStatus.suspended, "closed"),
        (CardStatus.silent, "unknown"),
    ],
)
def test_card_network_status_does_not_default_unknown_to_closed(status, expected):
    card = IotCardModel(status=status)

    assert card.get_network_status() == expected
    assert card.to_dict()["network_status"] == expected


@pytest.mark.asyncio
async def test_delayed_simboss_resume_is_scheduled_for_reconcile():
    card = SimpleNamespace(
        id=11,
        iccid="8986000000000000011",
        msisdn=None,
        supplier_id=2,
        card_type=CardType.pool,
    )
    supplier = SimpleNamespace(
        id=2,
        code="002",
        api_url="https://api.simboss.com",
        api_key="key",
        api_secret="secret",
        api_config={},
    )
    operation = SimpleNamespace(id=21)
    client = SimpleNamespace(
        resume_card=AsyncMock(return_value=False),
        last_sor_result={"submitted": True, "verification_pending": True},
    )
    db = SimpleNamespace()

    with patch.object(
        SuspendActionService,
        "_create_supplier_operation",
        new=AsyncMock(return_value=operation),
    ), patch(
        "app.services.suspend_service.get_supplier_client",
        return_value=client,
    ), patch(
        "app.services.suspend_service.SupplierSuspendOperationCRUD.update_request_result",
        new=AsyncMock(),
    ), patch.object(
        SuspendActionService,
        "_safe_update_supplier_action_audit",
        new=AsyncMock(),
    ), patch.object(
        SuspendActionService,
        "schedule_pending_operation_reconcile",
        new=Mock(),
    ) as schedule_reconcile:
        success, callback_no, reconciled_status = await SuspendActionService._call_supplier_resume(
            db=db,
            card=card,
            supplier=supplier,
            operator_id=1,
        )

    assert success is False
    assert callback_no
    assert reconciled_status is None
    schedule_reconcile.assert_called_once_with(
        callback_no,
        delay_seconds=settings.supplier_callback_reconcile_seconds,
    )


@pytest.mark.asyncio
async def test_h5_supplier_request_uses_fast_reconcile_interval():
    card = SimpleNamespace(
        id=11,
        iccid="8986000000000000011",
        msisdn=None,
        supplier_id=1,
        card_type=CardType.pool,
    )
    supplier = SimpleNamespace(
        id=1,
        code="001",
        api_url="https://api.example.com",
        api_key="key",
        api_secret="secret",
        api_config={},
    )
    operation = SimpleNamespace(id=21)
    client = SimpleNamespace(
        suspend_card=AsyncMock(return_value=True),
        last_sor_result={"submitted": True},
    )

    with patch.object(
        SuspendActionService,
        "_create_supplier_operation",
        new=AsyncMock(return_value=operation),
    ), patch(
        "app.services.suspend_service.get_supplier_client",
        return_value=client,
    ), patch(
        "app.services.suspend_service.SupplierSuspendOperationCRUD.update_request_result",
        new=AsyncMock(),
    ), patch.object(
        SuspendActionService,
        "_safe_update_supplier_action_audit",
        new=AsyncMock(),
    ), patch.object(
        SuspendActionService,
        "schedule_pending_operation_reconcile",
        new=Mock(),
    ) as schedule_reconcile:
        success, callback_no, reconciled_status = await SuspendActionService._call_supplier_suspend(
            db=SimpleNamespace(),
            card=card,
            supplier=supplier,
            reason="H5停机",
            operator_id=1,
            request_context={"audit_source": "h5"},
        )

    assert success is True
    assert callback_no
    assert reconciled_status is None
    schedule_reconcile.assert_called_once_with(
        callback_no,
        delay_seconds=settings.refresh_status_poll_interval_seconds,
    )


def test_h5_reconcile_retries_remain_fast():
    assert (
        SuspendActionService._operation_reconcile_delay({"audit_source": "h5"})
        == settings.refresh_status_poll_interval_seconds
    )
    assert (
        SuspendActionService._operation_reconcile_delay({
            "audit_source": "h5",
            "auto_reconcile_attempts": 2,
        })
        == settings.refresh_status_poll_interval_seconds
    )
    assert (
        SuspendActionService._operation_reconcile_delay({
            "audit_source": "h5",
            "auto_reconcile_attempts": 3,
        })
        == settings.supplier_callback_reconcile_seconds
    )
    assert (
        SuspendActionService._operation_reconcile_delay({})
        == settings.supplier_callback_reconcile_seconds
    )


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _ScalarsResult:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return self

    def all(self):
        return self.values


@pytest.mark.asyncio
async def test_pool_exceed_suspend_uses_supplier_operation_service_and_records_api_call():
    pool = SimpleNamespace(id=46, user_id=40, name="测试池", get_usage_percent=lambda: 108.4)
    card = SimpleNamespace(
        id=1516,
        iccid="8986032341202056067",
        msisdn="1064983508065",
        supplier_id=2,
        card_type=CardType.pool,
        status=CardStatus.activated,
        suspend_type=SuspendType.none,
        suspend_at=None,
        suspend_reason=None,
    )
    supplier = SimpleNamespace(id=2, code="002")
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[
            _ScalarResult({"pool_stop_threshold": 100}),
            _ScalarsResult([card]),
            _ScalarsResult([]),
            _ScalarsResult([supplier]),
        ]),
        add=Mock(),
        commit=AsyncMock(),
    )

    with patch.object(
        SuspendActionService,
        "_call_supplier_suspend",
        new=AsyncMock(return_value=(True, "sus-callback", "suspended")),
    ) as supplier_suspend:
        await pool_crud._check_pool_stop_threshold(db, pool)

    supplier_suspend.assert_awaited_once()
    request_context = supplier_suspend.await_args.kwargs["request_context"]
    assert request_context["operation_source"] == "pool_exceed"
    assert request_context["pool_id"] == 46
    assert card.status == CardStatus.suspended
    log = db.add.call_args.args[0]
    assert log.api_called == 1
    assert json.loads(log.api_result)["callback_no"] == "sus-callback"
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_pool_exceed_does_not_resubmit_while_supplier_operation_is_pending():
    pool = SimpleNamespace(id=46, user_id=40, name="测试池", get_usage_percent=lambda: 108.4)
    card = SimpleNamespace(
        id=1516,
        iccid="8986032341202056067",
        supplier_id=2,
        status=CardStatus.activated,
    )
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[
            _ScalarResult({"pool_stop_threshold": 100}),
            _ScalarsResult([card]),
            _ScalarsResult([card.id]),
            _ScalarsResult([]),
        ]),
        add=Mock(),
        commit=AsyncMock(),
    )

    with patch.object(
        SuspendActionService,
        "_call_supplier_suspend",
        new=AsyncMock(),
    ) as supplier_suspend:
        await pool_crud._check_pool_stop_threshold(db, pool)

    supplier_suspend.assert_not_awaited()
    db.add.assert_not_called()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_pool_exceed_reconcile_preserves_reason_and_creates_suspend_log():
    card = SimpleNamespace(
        id=1516,
        iccid="8986032341202056067",
        supplier_id=2,
        pool_id=46,
        status=CardStatus.activated,
        suspend_type=SuspendType.none,
        suspend_at=None,
        suspend_reason=None,
    )
    operation = SimpleNamespace(
        id=81,
        card_id=card.id,
        supplier_id=2,
        action=SuspendActionType.suspend,
        callback_status="pending",
        operator_id=None,
        request_result=json.dumps({
            "submitted": True,
            "operation_source": "pool_exceed",
            "pool_id": 46,
            "suspend_type": SuspendType.pool_exceed.value,
            "reason": "流量池用量超限停卡",
        }),
    )
    supplier = SimpleNamespace(
        id=2,
        api_url="",
        api_key="",
        api_secret="",
        code="002",
        api_config=None,
    )
    supplier_result = MagicMock()
    supplier_result.scalar_one_or_none.return_value = supplier
    db = MagicMock()
    db.get = AsyncMock(return_value=card)
    db.execute = AsyncMock(return_value=supplier_result)
    db.commit = AsyncMock()
    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=db)
    session_context.__aexit__ = AsyncMock(return_value=None)
    supplier_client = MagicMock()
    supplier_client.get_card_lifecycle = AsyncMock(
        return_value={"status": CardStatus.suspended.value}
    )

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
    ), patch.object(
        SuspendActionService, "_safe_refresh_pool_stats", AsyncMock()
    ):
        await SuspendActionService._run_pending_operation_reconcile("callback-81", 0)

    assert card.status == CardStatus.suspended
    assert card.suspend_type == SuspendType.pool_exceed
    assert card.suspend_reason == "流量池用量超限停卡"
    log = next(call.args[0] for call in db.add.call_args_list if isinstance(call.args[0], SuspendLogModel))
    assert log.pool_id == 46
    assert log.api_called == 1
