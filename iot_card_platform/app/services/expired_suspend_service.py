"""本地套餐到期与供应商关停对账，复用现有停复机操作和回调。"""
import asyncio
import json
import logging
from datetime import timedelta
from weakref import WeakKeyDictionary

from sqlalchemy import or_, select

from app.config import settings
from app.crud.suspend_crud import CardSuspendCRUD, SuspendLogCRUD, SuspendPolicyCRUD, SupplierSuspendOperationCRUD
from app.db.models.iot_card import CardStatus, IotCardModel, SuspendType
from app.db.models.suspend import SupplierSuspendOperationModel, SuspendActionType
from app.clients.supplier_api import get_supplier_client
from app.services.suspend_service import SuspendActionService
from app.utils.timezone import beijing_now

logger = logging.getLogger(__name__)
# 当前生产为单 worker；同时串行化管理员手动触发与定时任务。
_task_locks = WeakKeyDictionary()
CONFIRMED_REASON = "套餐到期，供应商已确认停机"


def operation_context(operation):
    """请求前持久化的上下文用于恢复进程中断时遗留的操作。"""
    context = {}
    for value in (getattr(operation, "request_payload", None), getattr(operation, "request_result", None)):
        try:
            data = json.loads(value or "{}")
            if isinstance(data, dict):
                context.update(data)
        except (TypeError, ValueError):
            pass
    return context


def needs_expiry_check(card):
    return bool(
        card and not card.is_deleted and card.expired_at
        and (
            (card.status == CardStatus.activated and card.expired_at < beijing_now().date())
            or (card.status == CardStatus.suspended and card.suspend_type == SuspendType.expired)
        )
    )


async def _policy_allows_stop(db, card):
    policies = await SuspendPolicyCRUD.get_active_policies(
        db, "expired", user_id=card.user_id, pool_id=card.pool_id
    )
    # CRUD 在未传 pool_id 时不限制池；这里必须排除其他池的策略。
    policies = [p for p in policies if p.pool_id is None or p.pool_id == card.pool_id]
    policy = max(policies, key=lambda p: (p.user_id is not None, p.pool_id is not None, -p.id), default=None)
    return policy is None or policy.auto_suspend == 1


async def _pending_operation(db, card_id):
    return (await db.execute(
        select(SupplierSuspendOperationModel).where(
            SupplierSuspendOperationModel.card_id == card_id,
            SupplierSuspendOperationModel.is_deleted == 0,
            SupplierSuspendOperationModel.callback_status == "pending",
        ).order_by(SupplierSuspendOperationModel.id.desc()).limit(1)
    )).scalar_one_or_none()


async def _confirm_local_stop(db, card, callback_no=None):
    changed = card.status != CardStatus.suspended or card.suspend_reason != CONFIRMED_REASON
    SuspendActionService.normalize_card_suspend_state(
        card, "suspended", suspend_type=SuspendType.expired, reason=CONFIRMED_REASON
    )
    if changed:
        await SuspendLogCRUD.create(
            db, card_id=card.id, iccid=card.iccid, action=SuspendActionType.suspend,
            suspend_type="expired", pool_id=card.pool_id, reason=CONFIRMED_REASON,
            api_called=True,
            api_result=json.dumps({"callback_no": callback_no, "status": "confirmed"}, ensure_ascii=False),
        )
    return changed


async def confirm_expired_operation(db, card, operation):
    """供应商确认后收敛本地状态；停机期间续费则恢复网络。"""
    await db.commit()
    await db.refresh(card)
    latest_id = await SupplierSuspendOperationCRUD.get_latest_id_for_card(db, card.id)
    if (latest_id != operation.id or card.is_deleted or card.supplier_id != operation.supplier_id
            or card.status in {CardStatus.expired, CardStatus.cancelled}):
        return
    if card.suspend_type not in {None, SuspendType.none, SuspendType.expired}:
        return
    await _confirm_local_stop(db, card, operation.callback_no)
    if card.expired_at and card.expired_at >= beijing_now().date():
        await SuspendActionService.auto_resume_cards_after_flow_adjustment(
            db, [card], reason="到期停机确认期间已续费，自动复机"
        )


async def _recover_pending(db):
    cutoff = beijing_now() - timedelta(seconds=max(90, settings.supplier_callback_reconcile_seconds))
    # 与卡片当前到期日无关，确保续费或重启不会丢失在途停机的核验。
    rows = (await db.execute(
        select(SupplierSuspendOperationModel).where(
            SupplierSuspendOperationModel.is_deleted == 0,
            SupplierSuspendOperationModel.callback_status == "pending",
            SupplierSuspendOperationModel.updated_at <= cutoff,
            or_(
                SupplierSuspendOperationModel.request_payload.contains('"operation_source": "expired"'),
                SupplierSuspendOperationModel.request_result.contains('"operation_source": "expired"'),
            ),
        ).order_by(SupplierSuspendOperationModel.id).limit(100)
    )).scalars().all()
    callback_nos = [row.callback_no for row in rows]
    await db.commit()
    confirmed_count = 0
    for callback_no in callback_nos:
        await SuspendActionService._run_pending_operation_reconcile(callback_no, 0)
        operation = await SupplierSuspendOperationCRUD.get_by_callback_no(db, callback_no)
        if operation:
            await db.refresh(operation)
            confirmed_count += operation.callback_status == "success"
        await db.commit()
    return confirmed_count


async def _check_card(db, card_id):
    card = await db.get(IotCardModel, card_id, populate_existing=True)
    if not needs_expiry_check(card):
        return "skipped_count", None
    pending = await _pending_operation(db, card.id)
    if pending:
        # 也恢复续费复机等在途请求；仍在处理的操作不重复下发。
        if pending.updated_at <= beijing_now() - timedelta(seconds=max(90, settings.supplier_callback_reconcile_seconds)):
            await db.commit()
            await SuspendActionService._run_pending_operation_reconcile(pending.callback_no, 0)
        return "skipped_count", None
    if card.expired_at < beijing_now().date() and not await _policy_allows_stop(db, card):
        return "skipped_count", None

    suppliers = await SuspendActionService._load_supplier_map(db, [card])
    supplier = suppliers.get(card.supplier_id)
    if not SuspendActionService._supplier_supports_network_switch(card, supplier):
        logger.warning("到期停机供应商未配置或不支持: card_id=%s", card_id)
        return "failed_count", None
    client = get_supplier_client(
        supplier_id=supplier.id, api_url=supplier.api_url or "", api_key=supplier.api_key or "",
        api_secret=supplier.api_secret or "", supplier_code=supplier.code, api_config=supplier.api_config,
    )
    lifecycle = await client.get_card_lifecycle(card.iccid)
    observed = lifecycle.get("network_status", "unknown") if supplier.code == "002" else lifecycle.get("status")

    # MySQL 默认可重复读，必须结束旧事务再读，才能看见查询期间发生的续费。
    await db.commit()
    await db.refresh(card)
    if not needs_expiry_check(card) or card.supplier_id != supplier.id or await _pending_operation(db, card.id):
        return "skipped_count", None
    if lifecycle.get("status") in {"expired", "cancelled"}:
        return "skipped_count", None
    if observed not in {"activated", "testing", "silent", "suspended"}:
        logger.warning("到期停机未获得供应商确定状态，稍后重试: card_id=%s status=%s", card_id, observed)
        return "failed_count", None
    if card.expired_at >= beijing_now().date():
        if observed != "suspended":
            await SuspendActionService._resume_card_with_logging(
                db, card, reason="已续费且供应商可用，修复本地到期停机状态", api_called=True,
                api_result=json.dumps({"status": observed, "source": "expiry_reconcile"}),
            )
            return "resumed_count", card.pool_id
        result = await SuspendActionService.auto_resume_cards_after_flow_adjustment(
            db, [card], reason="已续费卡到期停机状态核对复机"
        )
        return ("resumed_count" if result["resumed_count"] else "failed_count"), card.pool_id
    if not await _policy_allows_stop(db, card):
        return "skipped_count", None
    if observed == "suspended":
        changed = await _confirm_local_stop(db, card)
        return ("suspended_count" if changed else "skipped_count"), card.pool_id if changed else None
    success, callback_no, confirmed = await SuspendActionService._call_supplier_suspend(
        db, card, supplier, reason="套餐到期自动停卡",
        request_context={"operation_source": "expired", "suspend_type": "expired", "reason": CONFIRMED_REASON},
    )
    operation = await SupplierSuspendOperationCRUD.get_by_callback_no(db, callback_no) if callback_no else None
    meta = operation_context(operation) if operation else {}
    await db.commit()
    await db.refresh(card)
    if operation:
        await db.refresh(operation)
        # 供应商可能在提交接口返回前完成回调，不能把已确认状态覆盖成待确认。
        if operation.callback_status != "pending":
            if operation.callback_status == "failed":
                return "failed_count", None
            return "suspended_count", card.pool_id
        if await SupplierSuspendOperationCRUD.get_latest_id_for_card(db, card.id) != operation.id:
            return "submitted_count", None
    if not success and not meta.get("submitted"):
        if operation and operation.callback_status == "pending":
            await SupplierSuspendOperationCRUD.update_callback_result(
                db, operation, "{}", "SUBMIT_FAILED", "供应商停机提交失败，下轮重试", None, "failed"
            )
        return "failed_count", None

    # 已续费或有其他停机原因时交由回调/对账处理，不用旧快照覆盖。
    if needs_expiry_check(card) and card.expired_at < beijing_now().date():
        if confirmed == "suspended":
            if operation:
                await SupplierSuspendOperationCRUD.update_callback_result(
                    db, operation, "{}", "IMMEDIATE_CONFIRM", "供应商已确认停机", "suspended", "success"
                )
            await _confirm_local_stop(db, card, callback_no)
            return "suspended_count", card.pool_id
        SuspendActionService.normalize_card_suspend_state(
            card, "suspended", suspend_type=SuspendType.expired,
            reason="套餐到期停机已提交，等待供应商确认",
        )
        await SuspendLogCRUD.create(
            db, card_id=card.id, iccid=card.iccid, action=SuspendActionType.suspend,
            suspend_type="expired", pool_id=card.pool_id, reason=card.suspend_reason, api_called=True,
            api_result=json.dumps({"callback_no": callback_no, "status": "pending"}),
        )
        return "submitted_count", card.pool_id
    return "submitted_count", None


async def reconcile_expired_cards(db):
    # Python 3.9 的锁须在运行中的事件循环内创建。
    lock = _task_locks.setdefault(asyncio.get_running_loop(), asyncio.Lock())
    async with lock:
        counts = dict.fromkeys(("suspended_count", "submitted_count", "failed_count", "skipped_count", "resumed_count"), 0)
        counts["suspended_count"] += await _recover_pending(db)
        cards = await CardSuspendCRUD.get_expired_cards(db)
        card_ids = [card.id for card in cards]
        await db.commit()
        pool_ids = set()
        for card_id in card_ids:
            try:
                outcome, pool_id = await _check_card(db, card_id)
                counts[outcome] += 1
                if pool_id:
                    pool_ids.add(pool_id)
                await db.commit()
            except Exception:
                await db.rollback()
                counts["failed_count"] += 1
                logger.exception("到期停机核对失败，下轮重试: card_id=%s", card_id)
        await SuspendActionService._safe_refresh_pool_stats(db, pool_ids)
        return counts
