import asyncio
import json
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import Integer, MetaData, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app import scheduler
from app.crud.suspend_crud import CardSuspendCRUD
from app.db.models.iot_card import CardStatus, CardType, IotCardModel, SuspendType
from app.db.models.package import CarrierType, PeriodType
from app.db.models.supplier import SupplierModel
from app.db.models.suspend import SuspendActionType, SuspendLogModel, SuspendPolicyModel, SupplierSuspendOperationModel
from app.services import expired_suspend_service as expiry
from app.services.suspend_service import SupplierCallbackService, SuspendActionService
from app.utils.timezone import beijing_now


@pytest_asyncio.fixture
async def env(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    metadata = MetaData()
    for model in (IotCardModel, SupplierModel, SuspendPolicyModel, SuspendLogModel, SupplierSuspendOperationModel):
        table = model.__table__.to_metadata(metadata)
        # SQLite 仅 INTEGER PRIMARY KEY 支持自动编号，不改变生产模型。
        table.c.id.type = Integer()
    async with engine.begin() as connection:
        await connection.run_sync(metadata.create_all)
    sessions = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    monkeypatch.setattr("app.services.suspend_service.AsyncSessionLocal", sessions)
    monkeypatch.setattr(SuspendActionService, "schedule_pending_operation_reconcile", MagicMock())
    refresh_pool = AsyncMock()
    monkeypatch.setattr(SuspendActionService, "_safe_refresh_pool_stats", refresh_pool)
    client = SimpleNamespace(
        get_card_lifecycle=AsyncMock(return_value={"status": "activated"}),
        suspend_card=AsyncMock(return_value=True), resume_card=AsyncMock(return_value=True),
        last_sor_result=None,
    )
    monkeypatch.setattr(expiry, "get_supplier_client", lambda **kw: client)
    monkeypatch.setattr("app.services.suspend_service.get_supplier_client", lambda **kw: client)
    async with sessions() as db:
        supplier = SupplierModel(id=1, name="测试供应商", code="001")
        card = IotCardModel(
            id=871, iccid="8986112520609498004", user_id=10, supplier_id=1, pool_id=16,
            carrier=CarrierType.ctcc, period_type=PeriodType.monthly, card_type=CardType.pool,
            flow_size=71680, data_total=71680, status=CardStatus.activated,
            expired_at=beijing_now().date() - timedelta(days=1),
        )
        db.add_all([supplier, card])
        await db.commit()
        yield SimpleNamespace(db=db, card=card, supplier=supplier, client=client, refresh_pool=refresh_pool, sessions=sessions)
    await engine.dispose()


async def operations(env):
    return list((await env.db.execute(select(SupplierSuspendOperationModel).order_by(SupplierSuspendOperationModel.id))).scalars())


@pytest.mark.asyncio
@pytest.mark.parametrize("legacy", [False, True])
async def test_expired_and_legacy_local_stops_reach_supplier_once(env, legacy):
    if legacy:
        env.card.status = CardStatus.suspended
        env.card.suspend_type = SuspendType.expired
        await env.db.commit()
    first = await SuspendActionService.auto_suspend_expired(env.db)
    second = await SuspendActionService.auto_suspend_expired(env.db)
    env.client.suspend_card.assert_awaited_once()
    assert first["submitted_count"] == 1 and first["suspended_count"] == 0
    assert second["skipped_count"] == 1
    operation, = await operations(env)
    assert operation.callback_status == "pending"
    assert expiry.operation_context(operation)["suspend_type"] == "expired"
    assert "等待供应商确认" in env.card.suspend_reason
    env.refresh_pool.assert_any_await(env.db, {16})


@pytest.mark.asyncio
async def test_candidate_query_keeps_only_expiry_scope_and_includes_renewed_legacy(env):
    expected = []
    for index, (status, kind, days, deleted) in enumerate([
        ("activated", "none", -1, 0), ("suspended", "expired", -1, 0),
        ("suspended", "expired", 5, 0), ("activated", "none", 0, 0),
        ("activated", "none", 5, 0), ("suspended", "manual", -1, 0),
        ("suspended", "pool_exceed", -1, 0), ("cancelled", "expired", -1, 0),
        ("activated", "none", -1, 1), ("testing", "none", -1, 0),
        ("suspended", "device_separation", -1, 0), ("suspended", "card_exceed", -1, 0),
    ]):
        card = IotCardModel(
            id=1000+index, iccid=str(1000+index), carrier=CarrierType.ctcc,
            flow_size=100, data_total=100, period_type=PeriodType.monthly,
            status=CardStatus(status), suspend_type=SuspendType(kind), is_deleted=deleted,
            expired_at=beijing_now().date()+timedelta(days=days),
        )
        env.db.add(card)
        if index < 3:
            expected.append(card.id)
    await env.db.commit()
    rows = await CardSuspendCRUD.get_expired_cards(env.db)
    assert {c.id for c in rows} == {871, *expected}


@pytest.mark.asyncio
@pytest.mark.parametrize("days", [0, 1])
async def test_today_and_renewed_cards_are_never_stopped(env, days):
    env.card.expired_at = beijing_now().date() + timedelta(days=days)
    await env.db.commit()
    result = await SuspendActionService.auto_suspend_expired(env.db)
    env.client.suspend_card.assert_not_awaited()
    assert result["suspended_count"] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("lookup", ["unknown", RuntimeError("supplier offline")])
async def test_unknown_or_failed_lookup_never_claims_success(env, lookup):
    if isinstance(lookup, Exception):
        env.client.get_card_lifecycle.side_effect = lookup
    else:
        env.client.get_card_lifecycle.return_value = {"status": lookup}
    result = await SuspendActionService.auto_suspend_expired(env.db)
    assert result["failed_count"] == 1
    env.client.suspend_card.assert_not_awaited()
    assert await operations(env) == []


@pytest.mark.asyncio
@pytest.mark.parametrize("supplier_status", ["expired", "cancelled"])
async def test_supplier_terminal_cards_are_skipped_without_failure_or_new_commands(env, supplier_status):
    env.client.get_card_lifecycle.return_value = {"status": supplier_status, "network_status": "unknown"}
    result = await SuspendActionService.auto_suspend_expired(env.db)
    assert result["skipped_count"] == 1 and result["failed_count"] == 0
    env.client.suspend_card.assert_not_awaited()
    env.client.resume_card.assert_not_awaited()


@pytest.mark.asyncio
async def test_rejected_submission_is_retryable_and_not_confirmed(env):
    env.client.suspend_card.return_value = False
    result = await SuspendActionService.auto_suspend_expired(env.db)
    assert result["failed_count"] == 1 and result["suspended_count"] == 0
    first, = await operations(env)
    assert first.callback_status == "failed"
    assert env.card.status == CardStatus.activated
    env.client.suspend_card.return_value = True
    assert (await SuspendActionService.auto_suspend_expired(env.db))["submitted_count"] == 1
    assert env.client.suspend_card.await_count == 2


@pytest.mark.asyncio
async def test_querying_one_bad_card_does_not_abort_remaining_cards(env):
    other = IotCardModel(
        id=872, iccid="second", user_id=10, supplier_id=1, carrier=CarrierType.ctcc,
        flow_size=100, data_total=100, period_type=PeriodType.monthly,
        status=CardStatus.activated, expired_at=env.card.expired_at,
    )
    env.db.add(other)
    await env.db.commit()
    env.client.get_card_lifecycle.side_effect = [RuntimeError("timeout"), {"status": "activated"}]
    result = await SuspendActionService.auto_suspend_expired(env.db)
    assert result["failed_count"] == result["submitted_count"] == 1


@pytest.mark.asyncio
async def test_already_off_is_confirmed_without_repeated_commands_or_logs(env):
    env.client.get_card_lifecycle.return_value = {"status": "suspended"}
    assert (await SuspendActionService.auto_suspend_expired(env.db))["suspended_count"] == 1
    assert (await SuspendActionService.auto_suspend_expired(env.db))["suspended_count"] == 0
    env.client.suspend_card.assert_not_awaited()
    logs = (await env.db.execute(select(SuspendLogModel))).scalars().all()
    assert len(logs) == 1 and logs[0].api_called == 1
    assert env.card.suspend_reason == expiry.CONFIRMED_REASON


@pytest.mark.asyncio
async def test_simboss_accepted_but_network_unconfirmed_is_pending(env):
    env.supplier.code = "002"
    await env.db.commit()
    env.client.get_card_lifecycle.return_value = {"status": "suspended", "network_status": "activated"}
    env.client.suspend_card.return_value = False
    env.client.last_sor_result = {"submitted": True, "verification_pending": True}
    result = await SuspendActionService.auto_suspend_expired(env.db)
    assert result["submitted_count"] == 1 and result["suspended_count"] == 0
    env.client.suspend_card.assert_awaited_once()


@pytest.mark.asyncio
async def test_simboss_missing_network_status_is_not_confirmation(env):
    env.supplier.code = "002"
    await env.db.commit()
    env.client.get_card_lifecycle.return_value = {"status": "suspended"}
    assert (await SuspendActionService.auto_suspend_expired(env.db))["failed_count"] == 1
    env.client.suspend_card.assert_not_awaited()


@pytest.mark.asyncio
async def test_immediate_confirmation_closes_operation(env):
    env.client.last_sor_result = {"submitted": True, "reconciled_status": "suspended"}
    assert (await SuspendActionService.auto_suspend_expired(env.db))["suspended_count"] == 1
    op, = await operations(env)
    assert op.callback_status == "success"


@pytest.mark.asyncio
async def test_user_policy_overrides_global_and_unrelated_pool_policy(env):
    env.db.add_all([
        SuspendPolicyModel(id=1, name="全局", policy_type="expired", auto_suspend=1),
        SuspendPolicyModel(id=2, name="客户暂停", policy_type="expired", user_id=10, auto_suspend=0),
        SuspendPolicyModel(id=3, name="其他池", policy_type="expired", user_id=10, pool_id=99, auto_suspend=1),
    ])
    await env.db.commit()
    assert (await SuspendActionService.auto_suspend_expired(env.db))["skipped_count"] == 1
    env.client.suspend_card.assert_not_awaited()


@pytest.mark.asyncio
async def test_pool_policy_does_not_apply_to_nonmember(env):
    env.card.pool_id = None
    env.db.add(SuspendPolicyModel(id=1, name="其他池关闭自动停机", policy_type="expired", pool_id=99, auto_suspend=0))
    await env.db.commit()
    assert (await SuspendActionService.auto_suspend_expired(env.db))["submitted_count"] == 1


@pytest.mark.asyncio
async def test_renewal_during_lookup_cancels_stop(env):
    async def lookup(_):
        async with env.sessions() as another:
            card = await another.get(IotCardModel, 871)
            card.expired_at = beijing_now().date() + timedelta(days=30)
            await another.commit()
        return {"status": "activated"}
    env.client.get_card_lifecycle.side_effect = lookup
    assert (await SuspendActionService.auto_suspend_expired(env.db))["skipped_count"] == 1
    env.client.suspend_card.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("action", [SuspendActionType.resume, SuspendActionType.suspend])
async def test_existing_pending_stop_or_resume_blocks_new_stop(env, action):
    env.db.add(SupplierSuspendOperationModel(
        card_id=871, iccid=env.card.iccid, supplier_id=1, action=action, callback_no="existing",
        created_at=beijing_now(), updated_at=beijing_now(),
    ))
    await env.db.commit()
    assert (await SuspendActionService.auto_suspend_expired(env.db))["skipped_count"] == 1
    env.client.suspend_card.assert_not_awaited()


@pytest.mark.asyncio
async def test_callback_confirms_expired_type_and_is_idempotent(env):
    await SuspendActionService.auto_suspend_expired(env.db)
    op, = await operations(env)
    payload = {"callback_no": op.callback_no, "code": "200", "account_status": "02"}
    await SupplierCallbackService.handle_upiot_sor_callback(env.db, payload)
    await SupplierCallbackService.handle_upiot_sor_callback(env.db, payload)
    assert op.callback_status == "success"
    assert env.card.suspend_type == SuspendType.expired
    assert env.card.suspend_reason == expiry.CONFIRMED_REASON
    logs = (await env.db.execute(select(SuspendLogModel))).scalars().all()
    assert len(logs) == 2  # 一次受理，一次确认


@pytest.mark.asyncio
async def test_restart_recovers_pending_operation_from_request_payload(env):
    env.db.add(SupplierSuspendOperationModel(
        card_id=871, iccid=env.card.iccid, supplier_id=1, action=SuspendActionType.suspend,
        callback_no="interrupted", request_payload=json.dumps({"operation_source": "expired"}),
        created_at=beijing_now()-timedelta(minutes=10), updated_at=beijing_now()-timedelta(minutes=10),
    ))
    await env.db.commit()
    env.client.get_card_lifecycle.return_value = {"status": "suspended"}
    await SuspendActionService.auto_suspend_expired(env.db)
    op, = await operations(env)
    await env.db.refresh(op)
    assert op.callback_status == "success"
    assert env.card.suspend_type == SuspendType.expired
    env.client.suspend_card.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("via_callback", [True, False])
async def test_renewal_after_submission_resumes_after_stop_confirmation(env, via_callback):
    await SuspendActionService.auto_suspend_expired(env.db)
    op, = await operations(env)
    env.card.expired_at = beijing_now().date()+timedelta(days=30)
    # 模拟续费提交日期后，复机调用尚未执行或失败。
    await env.db.commit()
    env.client.get_card_lifecycle.return_value = {"status": "suspended"}
    if via_callback:
        await SupplierCallbackService.handle_upiot_sor_callback(
            env.db, {"callback_no": op.callback_no, "code": "200", "account_status": "02"}
        )
    else:
        await SuspendActionService._run_pending_operation_reconcile(op.callback_no, 0)
    await env.db.refresh(env.card)
    env.client.resume_card.assert_awaited_once()
    assert env.card.status == CardStatus.activated
    assert env.card.suspend_type == SuspendType.none


@pytest.mark.asyncio
async def test_stale_expiry_confirmation_cannot_override_newer_resume(env):
    await SuspendActionService.auto_suspend_expired(env.db)
    op, = await operations(env)
    env.db.add(SupplierSuspendOperationModel(
        card_id=871, iccid=env.card.iccid, supplier_id=1, action=SuspendActionType.resume,
        callback_no="newer", callback_status="success",
    ))
    env.card.expired_at = beijing_now().date()+timedelta(days=30)
    env.card.status = CardStatus.activated
    env.card.suspend_type = SuspendType.none
    await env.db.commit()
    env.client.get_card_lifecycle.return_value = {"status": "suspended"}
    await SuspendActionService._run_pending_operation_reconcile(op.callback_no, 0)
    await env.db.refresh(env.card)
    await env.db.refresh(op)
    assert env.card.status == CardStatus.activated
    assert op.callback_code == "SUPERSEDED"
    env.client.resume_card.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("mutation", ["manual_stop", "disable_policy", "pending_resume"])
async def test_changes_during_lookup_cancel_stop(env, mutation):
    async def lookup(_):
        async with env.sessions() as another:
            if mutation == "manual_stop":
                card = await another.get(IotCardModel, 871)
                card.status = CardStatus.suspended
                card.suspend_type = SuspendType.manual
            elif mutation == "disable_policy":
                another.add(SuspendPolicyModel(name="关闭自动关停", policy_type="expired", user_id=10, auto_suspend=0))
            else:
                another.add(SupplierSuspendOperationModel(
                    card_id=871, supplier_id=1, iccid="8986112520609498004",
                    action=SuspendActionType.resume, callback_no="concurrent-resume",
                ))
            await another.commit()
        return {"status": "activated"}
    env.client.get_card_lifecycle.side_effect = lookup
    assert (await SuspendActionService.auto_suspend_expired(env.db))["skipped_count"] == 1
    env.client.suspend_card.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("submission_response", [True, False])
async def test_fast_callback_is_not_overwritten_by_pending_state(env, submission_response):
    async def submit(iccid, reason, callback_no):
        async with env.sessions() as another:
            await SupplierCallbackService.handle_upiot_sor_callback(
                another, {"callback_no": callback_no, "code": "200", "account_status": "02"}
            )
        return submission_response
    env.client.suspend_card.side_effect = submit
    result = await SuspendActionService.auto_suspend_expired(env.db)
    assert result["suspended_count"] == 1 and result["submitted_count"] == 0
    assert env.card.suspend_reason == expiry.CONFIRMED_REASON
    op, = await operations(env)
    assert op.callback_status == "success"


@pytest.mark.asyncio
async def test_renewed_legacy_stop_is_repaired_without_new_stop(env):
    env.card.status = CardStatus.suspended
    env.card.suspend_type = SuspendType.expired
    env.card.expired_at = beijing_now().date()+timedelta(days=30)
    await env.db.commit()
    result = await SuspendActionService.auto_suspend_expired(env.db)
    assert result["resumed_count"] == 1
    assert env.card.status == CardStatus.activated
    env.client.suspend_card.assert_not_awaited()
    env.client.resume_card.assert_not_awaited()  # 供应商本来就可用，只修复本地。


@pytest.mark.asyncio
async def test_timed_out_stop_can_retry_in_later_scan(env):
    await SuspendActionService.auto_suspend_expired(env.db)
    op, = await operations(env)
    meta = expiry.operation_context(op)
    meta["auto_reconcile_attempts"] = 4
    op.request_result = json.dumps(meta)
    await env.db.commit()
    await SuspendActionService._run_pending_operation_reconcile(op.callback_no, 0)
    await env.db.refresh(op)
    assert op.callback_status == "failed"
    assert (await SuspendActionService.auto_suspend_expired(env.db))["submitted_count"] == 1
    assert env.client.suspend_card.await_count == 2


@pytest.mark.asyncio
async def test_concurrent_manual_and_scheduled_runs_submit_once(env):
    async with env.sessions() as other_db:
        await asyncio.gather(
            SuspendActionService.auto_suspend_expired(env.db),
            SuspendActionService.auto_suspend_expired(other_db),
        )
    env.client.suspend_card.assert_awaited_once()


def test_scheduler_registers_expired_job_in_beijing_without_overlap():
    with patch.object(scheduler.scheduler, "add_job") as add_job, patch.object(scheduler.scheduler, "start"):
        scheduler.start_scheduler()
    job = next(c for c in add_job.call_args_list if c.kwargs["id"] == "card_expired_auto_suspend")
    assert job.args[0] == scheduler.check_card_expired
    assert "minute='*/5'" in str(job.args[1])
    assert job.args[1].timezone.utcoffset(None) == timedelta(hours=8)
    assert job.kwargs["max_instances"] == 1 and job.kwargs["coalesce"] is True


@pytest.mark.asyncio
async def test_scheduler_rolls_back_and_logs_failure():
    db = SimpleNamespace(rollback=AsyncMock())
    ctx = MagicMock(__aenter__=AsyncMock(return_value=db), __aexit__=AsyncMock(return_value=None))
    with patch.object(scheduler, "AsyncSessionLocal", return_value=ctx), patch.object(
        SuspendActionService, "auto_suspend_expired", AsyncMock(side_effect=RuntimeError("failure"))
    ), patch.object(scheduler.logger, "exception") as log:
        await scheduler.check_card_expired()
    db.rollback.assert_awaited_once()
    log.assert_called_once()
