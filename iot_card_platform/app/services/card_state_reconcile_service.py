"""供应商状态对账，发现强制锁定卡已开网时重新停机。"""
import json
import logging
from datetime import date, datetime, timedelta

from sqlalchemy import select, and_, or_
from app.clients import get_supplier_client
from app.db.database import AsyncSessionLocal
from app.db.models.iot_card import IotCardModel, CardStatus, SuspendType
from app.db.models.supplier import SupplierModel
from app.db.models.suspend import (
    SupplierSuspendOperationModel, SuspendLogModel, SuspendActionType,
    AlertLogModel, AlertLevel, AlertTargetType,
)

logger = logging.getLogger(__name__)
CONFLICT_PREFIX = "手动停机冲突：供应商已激活 "


def decision(card, upstream, supplier_code, operation, allow_manual=False, *, manual_refresh=False):
    if getattr(card, "admin_stop_token", None):
        return "skip"
    if card.status != CardStatus.suspended or card.is_deleted:
        return "skip"
    if card.suspend_type not in (None, SuspendType.none, SuspendType.manual):
        return "skip"
    if card.expired_at and card.expired_at < date.today():
        return "skip"
    if upstream.get("status") != "activated":
        return "skip"
    if supplier_code == "002" and upstream.get("network_status") != "activated":
        return "skip"
    if operation:
        if operation.created_at >= datetime.now() - timedelta(minutes=10) and not (
            manual_refresh and operation.action == SuspendActionType.resume and operation.callback_status == "failed"
        ):
            return "skip"
        try:
            submitted = json.loads(operation.request_result or "{}").get("submitted", True)
        except (ValueError, AttributeError):
            submitted = True
        if operation.callback_status == "pending" and submitted:
            return "skip"
    if card.suspend_type == SuspendType.manual and not allow_manual:
        if not (
            operation and operation.action == SuspendActionType.resume
            and operation.callback_status == "failed" and card.suspend_at
            and operation.created_at > card.suspend_at
            and operation.supplier_id == card.supplier_id
        ):
            return "alert"
    return "repair"


async def latest_operation(db, card_id):
    return (await db.execute(select(SupplierSuspendOperationModel).where(
        SupplierSuspendOperationModel.card_id == card_id,
        SupplierSuspendOperationModel.is_deleted == 0,
    ).order_by(SupplierSuspendOperationModel.id.desc()).limit(1))).scalar_one_or_none()


async def reconcile_supplier(supplier_id, authorized_iccids=()):
    """授权列表只供本次人工修复调用；定时调用永远为空。"""
    counts = {"repair": 0, "alert": 0, "skip": 0, "failed": 0}
    async with AsyncSessionLocal() as db:
        supplier = await db.get(SupplierModel, supplier_id)
        if not supplier or supplier.is_deleted:
            return counts
        client = get_supplier_client(
            supplier_id=supplier.id, api_url=supplier.api_url or "",
            api_key=supplier.api_key or "", api_secret=supplier.api_secret or "",
            supplier_code=supplier.code, api_config=supplier.api_config,
        )
        code = supplier.code
        query = select(IotCardModel.id, IotCardModel.iccid).where(
            IotCardModel.supplier_id == supplier_id, IotCardModel.is_deleted == 0,
            or_(IotCardModel.admin_stop_token.is_not(None), and_(
                IotCardModel.status == CardStatus.suspended,
                IotCardModel.suspend_type.in_([SuspendType.none, SuspendType.manual]),
            )),
        )
        if authorized_iccids:
            query = query.where(IotCardModel.iccid.in_(authorized_iccids))
        targets = (await db.execute(query)).all()
        await db.rollback()
        for card_id, iccid in targets:
            try:
                before = await latest_operation(db, card_id)
                before_id = before.id if before else None
                await db.rollback()
                upstream = await client.get_card_lifecycle(iccid)
                # 不在外部请求期间持锁。返回后重读，避免覆盖新操作/续费/卡归属变化。
                card = (await db.execute(select(IotCardModel).where(
                    IotCardModel.id == card_id
                ).with_for_update().execution_options(populate_existing=True))).scalar_one()
                operation = await latest_operation(db, card_id)
                if (card.is_deleted or card.iccid != iccid or card.supplier_id != supplier_id
                        or (operation.id if operation else None) != before_id):
                    await db.rollback()
                    counts["skip"] += 1
                    continue
                if card.admin_stop_token:
                    from app.services.suspend_service import SuspendActionService
                    current_supplier = await db.get(SupplierModel, supplier_id)
                    await SuspendActionService.enforce_admin_stop(db, card, current_supplier, upstream, operation)
                    await db.commit()
                    continue
                action = decision(card, upstream, code, operation, iccid in authorized_iccids)
                if action == "skip":
                    await db.rollback()
                    counts[action] += 1
                    continue
                name = CONFLICT_PREFIX + iccid
                alerts = (await db.execute(select(AlertLogModel).where(
                    AlertLogModel.target_type == AlertTargetType.card,
                    AlertLogModel.target_id == card_id, AlertLogModel.target_name == name,
                    AlertLogModel.handled == 0, AlertLogModel.is_deleted == 0,
                ))).scalars().all()
                if action == "alert":
                    if not alerts:
                        db.add(AlertLogModel(
                            target_type=AlertTargetType.card, target_id=card_id, target_name=name,
                            alert_level=AlertLevel.warning, usage_percent=0, threshold=0,
                            user_id=card.user_id, notified=0, handled=0,
                            handle_remark="状态冲突告警（非流量超限）；保留手动停机意图，请核实供应商开网原因。",
                        ))
                    for alert in alerts:
                        alert.user_id = card.user_id
                else:
                    previous = card.suspend_type.value if card.suspend_type else "none"
                    card.status = CardStatus.activated
                    card.suspend_type = SuspendType.none
                    card.suspend_at = None
                    card.suspend_reason = None
                    db.add(SuspendLogModel(
                        card_id=card_id, iccid=iccid, action=SuspendActionType.resume,
                        suspend_type=previous, api_called=0,
                        reason="用户授权状态校正：供应商已激活" if authorized_iccids else "自动状态校正：供应商已激活",
                        api_result=json.dumps({"source": "supplier_state_reconcile", "upstream": upstream}, ensure_ascii=False),
                    ))
                    for alert in alerts:
                        alert.handled = 1
                        alert.handled_at = datetime.now()
                        alert.handle_remark = "已根据供应商状态完成校正，历史停机记录保留"
                await db.commit()
                counts[action] += 1
            except Exception:
                await db.rollback()
                counts["failed"] += 1
                logger.exception("卡状态对账失败: %s", iccid)
    logger.info("供应商卡状态对账: supplier=%s counts=%s", supplier_id, counts)
    return counts
