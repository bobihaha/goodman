"""
停卡策略服务层
"""
import asyncio
import json
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, date
import logging

from app.crud.suspend_crud import (
    SuspendPolicyCRUD, SuspendLogCRUD, SupplierSuspendOperationCRUD, AlertLogCRUD, CardSuspendCRUD
)
from app.db.models.suspend import (
    SuspendPolicyModel, SuspendLogModel, SupplierSuspendOperationModel, AlertLogModel,
    SuspendActionType, AlertLevel, AlertTargetType
)
from app.db.models.iot_card import IotCardModel, CardStatus, CardType, SuspendType
from app.db.models.supplier import SupplierModel
from app.db.models.sys_user import SysUserModel, UserLevel
from app.schemas.suspend import (
    PolicyCreate, PolicyUpdate, ManualSuspend, ManualResume, SuspendResult
)
from app.config import settings
from app.clients.supplier_api import get_supplier_client
from app.clients.upiot_client import UPIOT_STATUS_MAP
from app.services.notification_service import NotificationService
from sqlalchemy import select
from app.db.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class SuspendPolicyService:
    """停卡策略服务"""

    @staticmethod
    async def create_policy(
        db: AsyncSession,
        data: PolicyCreate,
        created_by: int
    ) -> SuspendPolicyModel:
        """创建策略"""
        return await SuspendPolicyCRUD.create(
            db=db,
            name=data.name,
            description=data.description,
            policy_type=data.policy_type,
            warning_threshold=data.warning_threshold,
            critical_threshold=data.critical_threshold,
            stop_threshold=data.stop_threshold,
            user_id=data.user_id,
            pool_id=data.pool_id,
            auto_suspend=data.auto_suspend,
            auto_resume=data.auto_resume,
            notify_warning=data.notify_warning,
            notify_critical=data.notify_critical,
            notify_suspend=data.notify_suspend,
            is_enabled=data.is_enabled,
            created_by=created_by
        )

    @staticmethod
    async def get_policy(db: AsyncSession, policy_id: int) -> Optional[SuspendPolicyModel]:
        """获取策略详情"""
        return await SuspendPolicyCRUD.get_by_id(db, policy_id)

    @staticmethod
    async def get_policies(
        db: AsyncSession,
        policy_type: Optional[str] = None,
        user_id: Optional[int] = None,
        is_enabled: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取策略列表"""
        policies, total = await SuspendPolicyCRUD.get_list(
            db=db,
            policy_type=policy_type,
            user_id=user_id,
            is_enabled=is_enabled,
            page=page,
            page_size=page_size
        )
        return [p.to_dict() for p in policies], total

    @staticmethod
    async def update_policy(
        db: AsyncSession,
        policy_id: int,
        data: PolicyUpdate
    ) -> Optional[SuspendPolicyModel]:
        """更新策略"""
        update_data = data.model_dump(exclude_unset=True)
        return await SuspendPolicyCRUD.update(db, policy_id, **update_data)

    @staticmethod
    async def delete_policy(db: AsyncSession, policy_id: int) -> bool:
        """删除策略"""
        return await SuspendPolicyCRUD.delete(db, policy_id)


class SuspendActionService:
    """停卡/复机操作服务"""

    @staticmethod
    def _supplier_supports_network_switch(card: IotCardModel, supplier: Optional[SupplierModel]) -> bool:
        """判断供应商是否支持当前卡片的网络开关操作。"""
        if not supplier:
            return False
        supplier_code = str(supplier.code or "").strip()
        if supplier_code != "002":
            return True
        card_type = card.card_type.value if hasattr(card.card_type, "value") else str(card.card_type or "")
        return card_type == CardType.pool.value

    @staticmethod
    async def _create_alert_and_notify(
        db: AsyncSession,
        target_type: AlertTargetType,
        target_id: int,
        target_name: str,
        alert_level: AlertLevel,
        usage_percent: int,
        threshold: int,
        policy_id: Optional[int] = None,
        user_id: Optional[int] = None,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> AlertLogModel:
        """创建告警后尝试发送通知邮件"""
        alert = await AlertLogCRUD.create(
            db=db,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            alert_level=alert_level,
            usage_percent=usage_percent,
            threshold=threshold,
            policy_id=policy_id,
            user_id=user_id
        )
        await NotificationService.send_alert_email(
            db=db,
            alert=alert,
            extra_context=extra_context
        )
        return alert

    @staticmethod
    def _check_card_not_expired(card: IotCardModel) -> Tuple[bool, Optional[str]]:
        if card.expired_at and card.expired_at < date.today():
            return False, "套餐已过期，请先续费"
        return True, None

    @staticmethod
    def _check_single_card_resume_eligibility(card: IotCardModel) -> Tuple[bool, Optional[str]]:
        if card.data_used > card.data_total:
            return False, "单卡流量仍超限，请先补量"
        return True, None

    @staticmethod
    async def _check_manual_suspend_resume_permission(
        db: AsyncSession,
        card: IotCardModel,
        operator_id: Optional[int],
        is_admin: bool
    ) -> Tuple[bool, Optional[str]]:
        """超级管理员手动停卡后，仅超级管理员可复机。"""
        if is_admin:
            return True, None

        latest_suspend_log = await SuspendLogCRUD.get_latest_by_card_and_action(
            db=db,
            card_id=card.id,
            action=SuspendActionType.suspend
        )
        if not latest_suspend_log or latest_suspend_log.suspend_type != SuspendType.manual.value:
            return True, None

        suspend_operator_id = latest_suspend_log.operator_id
        if not suspend_operator_id or suspend_operator_id == operator_id:
            return True, None

        operator_result = await db.execute(
            select(SysUserModel.user_level).where(
                SysUserModel.id == suspend_operator_id,
                SysUserModel.is_deleted == 0
            )
        )
        suspend_operator_level = operator_result.scalar_one_or_none()
        if suspend_operator_level == UserLevel.SUPER_ADMIN.value:
            return False, "该卡由超级管理员手动停卡，普通用户不可复机"

        return True, None

    @staticmethod
    async def _check_pool_card_resume_eligibility(
        db: AsyncSession,
        card: IotCardModel
    ) -> Tuple[bool, Optional[str]]:
        if not card.pool_id:
            return False, "流量池信息缺失，暂不可复机"

        from app.crud.pool_crud import pool_crud
        from app.db.models.sys_user import SysUserModel
        import json

        pool = await pool_crud.update_stats(db, card.pool_id)
        if not pool:
            return False, "流量池不存在，暂不可复机"

        threshold = 100
        if pool.user_id:
            quota_result = await db.execute(
                select(SysUserModel.quota).where(
                    SysUserModel.id == pool.user_id,
                    SysUserModel.is_deleted == 0
                )
            )
            quota_data = quota_result.scalar_one_or_none()
            if quota_data:
                quota = quota_data if isinstance(quota_data, dict) else json.loads(quota_data)
                threshold = quota.get("pool_stop_threshold", 100)

        if pool.get_usage_percent() >= threshold:
            return False, "流量池仍超限，请先补量"
        return True, None

    @staticmethod
    def normalize_card_suspend_state(
        card: IotCardModel,
        target_status: Optional[str],
        suspend_type: Optional[SuspendType] = None,
        reason: Optional[str] = None
    ) -> None:
        if not target_status or target_status not in {status.value for status in CardStatus}:
            return

        card.status = CardStatus(target_status)

        if target_status == CardStatus.suspended.value:
            resolved_suspend_type = suspend_type
            if resolved_suspend_type is None:
                current_suspend_type = card.suspend_type or SuspendType.none
                resolved_suspend_type = (
                    current_suspend_type
                    if current_suspend_type != SuspendType.none
                    else SuspendType.manual
                )
            card.suspend_type = resolved_suspend_type
            if card.suspend_at is None:
                card.suspend_at = datetime.now()
            if reason:
                card.suspend_reason = reason
            elif not card.suspend_reason:
                card.suspend_reason = "供应商状态同步为停机"
            return

        if target_status in {
            CardStatus.activated.value,
            CardStatus.testing.value,
            CardStatus.silent.value,
            CardStatus.expired.value,
            CardStatus.cancelled.value,
            CardStatus.stock.value
        }:
            card.suspend_type = SuspendType.none
            card.suspend_at = None
            card.suspend_reason = None

    @staticmethod
    def _matches_operation_target(
        action: SuspendActionType,
        lifecycle_status: Optional[str]
    ) -> bool:
        if not lifecycle_status:
            return False
        if action == SuspendActionType.suspend:
            return lifecycle_status == CardStatus.suspended.value
        if action == SuspendActionType.resume:
            return lifecycle_status in {
                CardStatus.activated.value,
                CardStatus.testing.value,
                CardStatus.silent.value,
            }
        return False

    @staticmethod
    def _generate_callback_no(action: SuspendActionType, iccid: str) -> str:
        action_prefix = "sus" if action == SuspendActionType.suspend else "res"
        suffix = uuid.uuid4().hex[:10]
        return f"{action_prefix}_{iccid[-8:]}_{suffix}"

    @staticmethod
    async def _create_supplier_operation(
        db: AsyncSession,
        card: IotCardModel,
        supplier: Optional[SupplierModel],
        action: SuspendActionType,
        operator_id: Optional[int],
        request_payload: Dict[str, Any]
    ) -> SupplierSuspendOperationModel:
        callback_no = request_payload["callback_no"]
        return await SupplierSuspendOperationCRUD.create(
            db=db,
            card_id=card.id,
            supplier_id=supplier.id if supplier else None,
            iccid=card.iccid,
            msisdn=card.msisdn,
            action=action,
            callback_no=callback_no,
            request_payload=json.dumps(request_payload, ensure_ascii=False),
            operator_id=operator_id
        )

    @staticmethod
    async def _load_supplier_map(
        db: AsyncSession,
        cards: List[IotCardModel]
    ) -> Dict[int, SupplierModel]:
        supplier_ids = {c.supplier_id for c in cards if c.supplier_id}
        if not supplier_ids:
            return {}
        supplier_result = await db.execute(
            select(SupplierModel).where(
                SupplierModel.id.in_(supplier_ids),
                SupplierModel.is_deleted == 0
            )
        )
        return {item.id: item for item in supplier_result.scalars().all()}

    @staticmethod
    def schedule_pending_operation_reconcile(
        callback_no: str,
        delay_seconds: Optional[int] = None
    ) -> None:
        effective_delay = max(5, delay_seconds or settings.supplier_callback_reconcile_seconds)
        asyncio.create_task(
            SuspendActionService._run_pending_operation_reconcile(
                callback_no=callback_no,
                delay_seconds=effective_delay
            )
        )

    @staticmethod
    async def _run_pending_operation_reconcile(
        callback_no: str,
        delay_seconds: int
    ) -> None:
        await asyncio.sleep(delay_seconds)

        async with AsyncSessionLocal() as db:
            try:
                operation = await SupplierSuspendOperationCRUD.get_by_callback_no(db, callback_no)
                if not operation or operation.callback_status != "pending":
                    return

                card = await db.get(IotCardModel, operation.card_id)
                if not card:
                    return

                supplier = None
                if operation.supplier_id:
                    supplier_result = await db.execute(
                        select(SupplierModel).where(
                            SupplierModel.id == operation.supplier_id,
                            SupplierModel.is_deleted == 0
                        )
                    )
                    supplier = supplier_result.scalar_one_or_none()
                if not supplier:
                    return

                supplier_client = get_supplier_client(
                    supplier_id=card.supplier_id,
                    api_url=supplier.api_url or "",
                    api_key=supplier.api_key or "",
                    api_secret=supplier.api_secret or "",
                    supplier_code=supplier.code,
                    api_config=supplier.api_config,
                )
                lifecycle_data = await supplier_client.get_card_lifecycle(card.iccid)
                lifecycle_status = lifecycle_data.get("status")

                request_meta: Dict[str, Any] = {}
                if operation.request_result:
                    try:
                        request_meta = json.loads(operation.request_result)
                    except Exception:
                        request_meta = {"raw_request_result": operation.request_result}
                request_meta["auto_reconcile_checked_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                request_meta["auto_reconcile_observed_status"] = lifecycle_status
                request_meta["auto_reconcile_attempts"] = int(request_meta.get("auto_reconcile_attempts") or 0) + 1
                await SupplierSuspendOperationCRUD.update_request_result(
                    db=db,
                    operation_id=operation.id,
                    request_result=json.dumps(request_meta, ensure_ascii=False)
                )

                if not SuspendActionService._matches_operation_target(operation.action, lifecycle_status):
                    if (
                        operation.action == SuspendActionType.resume
                        and request_meta.get("submitted")
                        and lifecycle_status == CardStatus.suspended.value
                    ):
                        await SuspendActionService._retry_refresh_resume_if_needed(
                            db=db,
                            card=card,
                            supplier=supplier,
                            resume_callback_no=callback_no,
                            observed_attempts=request_meta["auto_reconcile_attempts"]
                        )
                        if request_meta["auto_reconcile_attempts"] < 5:
                            SuspendActionService.schedule_pending_operation_reconcile(
                                callback_no=callback_no,
                                delay_seconds=settings.supplier_callback_reconcile_seconds
                            )
                    return

                SuspendActionService.normalize_card_suspend_state(
                    card,
                    lifecycle_status,
                    suspend_type=SuspendType.manual if operation.action == SuspendActionType.suspend else None,
                    reason="供应商生命周期自动对账收敛"
                )
                await SupplierSuspendOperationCRUD.update_callback_result(
                    db=db,
                    operation=operation,
                    callback_payload=json.dumps(
                        {
                            "source": "auto_reconcile",
                            "callback_no": callback_no,
                            "status": lifecycle_status,
                            "checked_at": request_meta["auto_reconcile_checked_at"],
                        },
                        ensure_ascii=False
                    ),
                    callback_code="AUTO_RECONCILE",
                    callback_msg="Supplier lifecycle status matched expected state",
                    account_status=lifecycle_status,
                    callback_status="success"
                )
                if operation.action == SuspendActionType.suspend:
                    if request_meta.get("refresh_resume_pending") and not request_meta.get("refresh_resume_submitted"):
                        await SuspendActionService.schedule_refresh_resume_after_suspend_confirmed(
                            db=db,
                            suspend_callback_no=callback_no,
                            source="auto_reconcile"
                        )
                if operation.action == SuspendActionType.resume:
                    await SuspendActionService._close_refresh_suspend_chain(
                        db=db,
                        card=card,
                        resume_callback_no=callback_no,
                        lifecycle_status=lifecycle_status
                    )
            except Exception as exc:
                logger.error("供应商操作自动收敛失败: callback_no=%s error=%s", callback_no, exc, exc_info=True)

    @staticmethod
    async def _close_refresh_suspend_chain(
        db: AsyncSession,
        card: IotCardModel,
        resume_callback_no: str,
        lifecycle_status: Optional[str]
    ) -> None:
        result = await db.execute(
            select(SupplierSuspendOperationModel).where(
                SupplierSuspendOperationModel.card_id == card.id,
                SupplierSuspendOperationModel.action == SuspendActionType.suspend,
                SupplierSuspendOperationModel.callback_status == "pending",
                SupplierSuspendOperationModel.is_deleted == 0
            ).order_by(SupplierSuspendOperationModel.id.desc())
        )
        operations = list(result.scalars().all())
        for operation in operations:
            request_meta: Dict[str, Any] = {}
            if operation.request_result:
                try:
                    request_meta = json.loads(operation.request_result)
                except Exception:
                    request_meta = {"raw_request_result": operation.request_result}

            if request_meta.get("refresh_resume_callback_no") != resume_callback_no:
                continue

            await SupplierSuspendOperationCRUD.update_callback_result(
                db=db,
                operation=operation,
                callback_payload=json.dumps(
                    {
                        "source": "auto_chain_resume",
                        "resume_callback_no": resume_callback_no,
                        "status": lifecycle_status,
                        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    },
                    ensure_ascii=False
                ),
                callback_code="AUTO_CHAINED",
                callback_msg="Refresh suspend chain completed by resume operation",
                account_status=lifecycle_status,
                callback_status="success"
            )
            break

    @staticmethod
    async def _retry_refresh_resume_if_needed(
        db: AsyncSession,
        card: IotCardModel,
        supplier: Optional[SupplierModel],
        resume_callback_no: str,
        observed_attempts: int
    ) -> bool:
        if observed_attempts < 2:
            return False

        result = await db.execute(
            select(SupplierSuspendOperationModel).where(
                SupplierSuspendOperationModel.card_id == card.id,
                SupplierSuspendOperationModel.action == SuspendActionType.suspend,
                SupplierSuspendOperationModel.is_deleted == 0
            ).order_by(SupplierSuspendOperationModel.id.desc())
        )
        operations = list(result.scalars().all())

        for operation in operations:
            request_meta: Dict[str, Any] = {}
            if operation.request_result:
                try:
                    request_meta = json.loads(operation.request_result)
                except Exception:
                    request_meta = {"raw_request_result": operation.request_result}

            if request_meta.get("refresh_resume_callback_no") != resume_callback_no:
                continue

            retry_count = int(request_meta.get("refresh_resume_retry_count") or 0)
            if retry_count >= 2:
                return False

            resume_success, new_resume_callback_no, _ = await SuspendActionService._call_supplier_resume(
                db=db,
                card=card,
                supplier=supplier,
                operator_id=operation.operator_id
            )
            request_meta["refresh_resume_submitted"] = resume_success
            request_meta["refresh_resume_callback_no"] = new_resume_callback_no
            request_meta["refresh_resume_retry_count"] = retry_count + 1
            request_meta["refresh_resume_retry_triggered_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            request_meta["refresh_resume_retry_source"] = "resume_auto_reconcile"
            await SupplierSuspendOperationCRUD.update_request_result(
                db=db,
                operation_id=operation.id,
                request_result=json.dumps(request_meta, ensure_ascii=False)
            )
            if not resume_success:
                logger.error("刷新复机重试提交失败: callback_no=%s iccid=%s", resume_callback_no, operation.iccid)
            return resume_success

        return False

    @staticmethod
    async def _call_supplier_suspend(
        db: AsyncSession,
        card: IotCardModel,
        supplier: Optional[SupplierModel],
        reason: Optional[str],
        operator_id: Optional[int] = None
    ) -> tuple[bool, Optional[str], Optional[str]]:
        if not SuspendActionService._supplier_supports_network_switch(card, supplier):
            logger.warning(
                "供应商不支持当前卡片网络关停: supplier_code=%s iccid=%s card_type=%s",
                getattr(supplier, "code", None),
                card.iccid,
                card.card_type,
            )
            return False, None, None
        callback_no = SuspendActionService._generate_callback_no(SuspendActionType.suspend, card.iccid)
        request_payload = {"number": card.iccid, "type": "01", "callback_no": callback_no}
        operation = await SuspendActionService._create_supplier_operation(
            db=db,
            card=card,
            supplier=supplier,
            action=SuspendActionType.suspend,
            operator_id=operator_id,
            request_payload=request_payload
        )
        try:
            supplier_client = get_supplier_client(
                supplier_id=card.supplier_id,
                api_url=supplier.api_url or "",
                api_key=supplier.api_key or "",
                api_secret=supplier.api_secret or "",
                supplier_code=supplier.code,
                api_config=supplier.api_config,
            )
            result = await supplier_client.suspend_card(card.iccid, reason, callback_no=callback_no)
            request_meta = getattr(supplier_client, "last_sor_result", None) or {"submitted": result}
            await SupplierSuspendOperationCRUD.update_request_result(
                db=db,
                operation_id=operation.id,
                request_result=json.dumps(request_meta, ensure_ascii=False)
            )
            if request_meta.get("submitted"):
                SuspendActionService.schedule_pending_operation_reconcile(callback_no)
            return result, callback_no, request_meta.get("reconciled_status")
        except Exception as exc:
            await SupplierSuspendOperationCRUD.update_request_result(
                db=db,
                operation_id=operation.id,
                request_result=json.dumps({"submitted": False, "error": str(exc)}, ensure_ascii=False)
            )
            logger.error(f"供应商API停机失败: iccid={card.iccid}, error={exc}")
            return False, callback_no, None

    @staticmethod
    async def _call_supplier_resume(
        db: AsyncSession,
        card: IotCardModel,
        supplier: Optional[SupplierModel],
        operator_id: Optional[int] = None
    ) -> tuple[bool, Optional[str], Optional[str]]:
        if not SuspendActionService._supplier_supports_network_switch(card, supplier):
            logger.warning(
                "供应商不支持当前卡片网络恢复: supplier_code=%s iccid=%s card_type=%s",
                getattr(supplier, "code", None),
                card.iccid,
                card.card_type,
            )
            return False, None, None
        callback_no = SuspendActionService._generate_callback_no(SuspendActionType.resume, card.iccid)
        request_payload = {"number": card.iccid, "type": "00", "callback_no": callback_no}
        operation = await SuspendActionService._create_supplier_operation(
            db=db,
            card=card,
            supplier=supplier,
            action=SuspendActionType.resume,
            operator_id=operator_id,
            request_payload=request_payload
        )
        try:
            supplier_client = get_supplier_client(
                supplier_id=card.supplier_id,
                api_url=supplier.api_url or "",
                api_key=supplier.api_key or "",
                api_secret=supplier.api_secret or "",
                supplier_code=supplier.code,
                api_config=supplier.api_config,
            )
            result = await supplier_client.resume_card(card.iccid, callback_no=callback_no)
            request_meta = getattr(supplier_client, "last_sor_result", None) or {"submitted": result}
            await SupplierSuspendOperationCRUD.update_request_result(
                db=db,
                operation_id=operation.id,
                request_result=json.dumps(request_meta, ensure_ascii=False)
            )
            if request_meta.get("submitted"):
                SuspendActionService.schedule_pending_operation_reconcile(callback_no)
            return result, callback_no, request_meta.get("reconciled_status")
        except Exception as exc:
            await SupplierSuspendOperationCRUD.update_request_result(
                db=db,
                operation_id=operation.id,
                request_result=json.dumps({"submitted": False, "error": str(exc)}, ensure_ascii=False)
            )
            logger.error(f"供应商API复机失败: iccid={card.iccid}, error={exc}")
            return False, callback_no, None

    @staticmethod
    async def mark_refresh_resume_pending(
        db: AsyncSession,
        suspend_callback_no: str
    ) -> None:
        operation = await SupplierSuspendOperationCRUD.get_by_callback_no(db, suspend_callback_no)
        if not operation:
            return

        metadata: Dict[str, Any] = {}
        if operation.request_result:
            try:
                metadata = json.loads(operation.request_result)
            except Exception:
                metadata = {"raw_request_result": operation.request_result}

        metadata["refresh_resume_pending"] = True
        await SupplierSuspendOperationCRUD.update_request_result(
            db=db,
            operation_id=operation.id,
            request_result=json.dumps(metadata, ensure_ascii=False)
        )

    @staticmethod
    async def schedule_refresh_resume_after_suspend_confirmed(
        db: AsyncSession,
        suspend_callback_no: str,
        delay_seconds: Optional[int] = None,
        source: str = "unknown"
    ) -> None:
        operation = await SupplierSuspendOperationCRUD.get_by_callback_no(db, suspend_callback_no)
        if not operation:
            return

        metadata: Dict[str, Any] = {}
        if operation.request_result:
            try:
                metadata = json.loads(operation.request_result)
            except Exception:
                metadata = {"raw_request_result": operation.request_result}

        if not metadata.get("refresh_resume_pending") or metadata.get("refresh_resume_submitted"):
            return

        effective_delay = max(1, delay_seconds or settings.refresh_resume_delay_seconds)
        existing_delay = int(metadata.get("refresh_resume_delay_seconds") or 0)
        if metadata.get("refresh_resume_scheduled") and existing_delay == effective_delay:
            return

        metadata["refresh_resume_scheduled"] = True
        metadata["refresh_resume_schedule_source"] = source
        metadata["refresh_resume_delay_seconds"] = effective_delay
        metadata["refresh_resume_scheduled_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await SupplierSuspendOperationCRUD.update_request_result(
            db=db,
            operation_id=operation.id,
            request_result=json.dumps(metadata, ensure_ascii=False)
        )

        SuspendActionService.schedule_refresh_resume_fallback(
            suspend_callback_no=suspend_callback_no,
            delay_seconds=effective_delay
        )

    @staticmethod
    async def mark_refresh_resume_submitted(
        db: AsyncSession,
        suspend_callback_no: str,
        resume_callback_no: Optional[str],
        submitted: bool
    ) -> None:
        operation = await SupplierSuspendOperationCRUD.get_by_callback_no(db, suspend_callback_no)
        if not operation:
            return

        metadata: Dict[str, Any] = {}
        if operation.request_result:
            try:
                metadata = json.loads(operation.request_result)
            except Exception:
                metadata = {"raw_request_result": operation.request_result}

        metadata["refresh_resume_pending"] = True
        metadata["refresh_resume_submitted"] = submitted
        metadata["refresh_resume_callback_no"] = resume_callback_no
        await SupplierSuspendOperationCRUD.update_request_result(
            db=db,
            operation_id=operation.id,
            request_result=json.dumps(metadata, ensure_ascii=False)
        )

    @staticmethod
    def schedule_refresh_resume_fallback(
        suspend_callback_no: str,
        delay_seconds: Optional[int] = None
    ) -> None:
        effective_delay = max(1, delay_seconds or settings.refresh_resume_fallback_seconds)
        asyncio.create_task(
            SuspendActionService._run_refresh_resume_fallback(
                suspend_callback_no=suspend_callback_no,
                delay_seconds=effective_delay
            )
        )

    @staticmethod
    async def _run_refresh_resume_fallback(
        suspend_callback_no: str,
        delay_seconds: int
    ) -> None:
        await asyncio.sleep(delay_seconds)

        async with AsyncSessionLocal() as db:
            try:
                operation = await SupplierSuspendOperationCRUD.get_by_callback_no(db, suspend_callback_no)
                if not operation or operation.action != SuspendActionType.suspend:
                    return

                request_meta: Dict[str, Any] = {}
                if operation.request_result:
                    try:
                        request_meta = json.loads(operation.request_result)
                    except Exception:
                        request_meta = {"raw_request_result": operation.request_result}

                if not request_meta.get("refresh_resume_pending"):
                    return

                card = await db.get(IotCardModel, operation.card_id)
                if not card:
                    logger.warning("刷新兜底复机未找到卡片: callback_no=%s", suspend_callback_no)
                    return

                supplier = None
                if operation.supplier_id:
                    supplier_result = await db.execute(
                        select(SupplierModel).where(
                            SupplierModel.id == operation.supplier_id,
                            SupplierModel.is_deleted == 0
                        )
                    )
                    supplier = supplier_result.scalar_one_or_none()

                if not supplier:
                    return

                supplier_client = get_supplier_client(
                    supplier_id=card.supplier_id,
                    api_url=supplier.api_url or "",
                    api_key=supplier.api_key or "",
                    api_secret=supplier.api_secret or "",
                    supplier_code=supplier.code,
                    api_config=supplier.api_config,
                )
                lifecycle_data = await supplier_client.get_card_lifecycle(card.iccid)
                lifecycle_status = lifecycle_data.get("status")

                request_meta["refresh_resume_fallback_checked_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                request_meta["refresh_resume_fallback_observed_status"] = lifecycle_status

                if lifecycle_status != CardStatus.suspended.value:
                    await SupplierSuspendOperationCRUD.update_request_result(
                        db=db,
                        operation_id=operation.id,
                        request_result=json.dumps(request_meta, ensure_ascii=False)
                    )
                    return

                existing_resume_callback_no = request_meta.get("refresh_resume_callback_no")
                if existing_resume_callback_no:
                    existing_resume_operation = await SupplierSuspendOperationCRUD.get_by_callback_no(
                        db,
                        existing_resume_callback_no
                    )
                    if existing_resume_operation and existing_resume_operation.callback_status == "success":
                        await SupplierSuspendOperationCRUD.update_request_result(
                            db=db,
                            operation_id=operation.id,
                            request_result=json.dumps(request_meta, ensure_ascii=False)
                        )
                        return

                resume_success, resume_callback_no, _ = await SuspendActionService._call_supplier_resume(
                    db=db,
                    card=card,
                    supplier=supplier,
                    operator_id=operation.operator_id
                )

                request_meta["refresh_resume_fallback_delay_seconds"] = delay_seconds
                request_meta["refresh_resume_fallback_triggered_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                request_meta["refresh_resume_submitted"] = resume_success
                request_meta["refresh_resume_callback_no"] = resume_callback_no
                request_meta["refresh_resume_fallback_triggered"] = True
                request_meta["refresh_resume_retry_count"] = int(request_meta.get("refresh_resume_retry_count") or 0) + 1
                await SupplierSuspendOperationCRUD.update_request_result(
                    db=db,
                    operation_id=operation.id,
                    request_result=json.dumps(request_meta, ensure_ascii=False)
                )
            except Exception as exc:
                logger.error("刷新兜底复机执行失败: callback_no=%s error=%s", suspend_callback_no, exc, exc_info=True)

    @staticmethod
    async def _check_resume_eligibility(
        db: AsyncSession,
        card: IotCardModel,
        operator_id: Optional[int] = None,
        is_admin: bool = False,
        force: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """检查卡片是否满足复机条件"""
        if force:
            return True, None

        suspend_type = card.suspend_type or SuspendType.none
        card_valid, card_invalid_reason = SuspendActionService._check_card_not_expired(card)
        if not card_valid and suspend_type != SuspendType.expired:
            return False, card_invalid_reason

        if suspend_type == SuspendType.expired:
            return SuspendActionService._check_card_not_expired(card)

        if suspend_type == SuspendType.manual:
            permission_ok, permission_reason = await SuspendActionService._check_manual_suspend_resume_permission(
                db=db,
                card=card,
                operator_id=operator_id,
                is_admin=is_admin
            )
            if not permission_ok:
                return False, permission_reason
            if card.pool_id:
                return await SuspendActionService._check_pool_card_resume_eligibility(db, card)
            return SuspendActionService._check_single_card_resume_eligibility(card)

        if suspend_type == SuspendType.card_exceed:
            return SuspendActionService._check_single_card_resume_eligibility(card)

        if suspend_type == SuspendType.pool_exceed:
            return await SuspendActionService._check_pool_card_resume_eligibility(db, card)

        if suspend_type == SuspendType.device_separation:
            return False, "该卡因机卡分离被锁定，如需解锁请使用强制复机"

        return True, None

    @staticmethod
    async def _resume_card_with_logging(
        db: AsyncSession,
        card: IotCardModel,
        operator_id: Optional[int] = None,
        reason: Optional[str] = None,
        api_called: bool = False,
        api_result: Optional[str] = None
    ) -> None:
        """执行复机并记录日志"""
        old_suspend_type = card.suspend_type.value if card.suspend_type else "manual"
        await CardSuspendCRUD.resume_card(db=db, card_id=card.id)

        await SuspendLogCRUD.create(
            db=db,
            card_id=card.id,
            iccid=card.iccid,
            action=SuspendActionType.resume,
            suspend_type=old_suspend_type,
            reason=reason,
            api_called=api_called,
            api_result=api_result,
            operator_id=operator_id
        )

    @staticmethod
    async def manual_suspend(
        db: AsyncSession,
        data: ManualSuspend,
        operator_id: int,
        user_id: Optional[int] = None,
        user_ids: Optional[List[int]] = None,
        is_admin: bool = False
    ) -> SuspendResult:
        """手动停卡"""
        success_cards = []
        fail_cards = []

        # 获取卡片
        cards = await CardSuspendCRUD.get_cards_by_ids(
            db, data.card_ids,
            user_id=None if is_admin else user_id,
            user_ids=None if is_admin else user_ids
        )
        card_map = {c.id: c for c in cards}

        supplier_map = await SuspendActionService._load_supplier_map(db, cards)

        for card_id in data.card_ids:
            card = card_map.get(card_id)
            
            if not card:
                fail_cards.append({"card_id": card_id, "iccid": "未知", "reason": "卡片不存在或无权限"})
                continue

            if card.status == CardStatus.suspended:
                fail_cards.append({"card_id": card_id, "iccid": card.iccid, "reason": "卡片已停机"})
                continue

            if card.status not in [CardStatus.activated, CardStatus.testing, CardStatus.silent]:
                fail_cards.append({"card_id": card_id, "iccid": card.iccid, "reason": f"卡片状态不支持停卡: {card.status.value}"})
                continue

            # 调用供应商API停机
            supplier = supplier_map.get(card.supplier_id)
            api_success, callback_no, reconciled_status = await SuspendActionService._call_supplier_suspend(
                db=db,
                card=card,
                supplier=supplier,
                reason=data.reason,
                operator_id=operator_id
            )

            # 只有API成功才更新数据库
            if not api_success:
                fail_cards.append({"card_id": card_id, "iccid": card.iccid, "reason": "供应商API调用失败"})
                continue

            # 执行停卡
            if reconciled_status == CardStatus.suspended.value:
                SuspendActionService.normalize_card_suspend_state(
                    card,
                    reconciled_status,
                    suspend_type=SuspendType.manual,
                    reason=data.reason,
                )
                await db.commit()
                await db.refresh(card)
            else:
                await CardSuspendCRUD.suspend_card(
                    db=db,
                    card_id=card_id,
                    suspend_type=SuspendType.manual,
                    reason=data.reason
                )

            # 记录日志
            await SuspendLogCRUD.create(
                db=db,
                card_id=card_id,
                iccid=card.iccid,
                action=SuspendActionType.suspend,
                suspend_type="manual",
                reason=data.reason,
                api_called=True,
                api_result=json.dumps({"callback_no": callback_no}, ensure_ascii=False) if callback_no else None,
                operator_id=operator_id
            )

            success_cards.append(card.iccid)

        return SuspendResult(
            success_count=len(success_cards),
            fail_count=len(fail_cards),
            success_cards=success_cards,
            fail_cards=fail_cards
        )

    @staticmethod
    async def manual_resume(
        db: AsyncSession,
        data: ManualResume,
        operator_id: int,
        user_id: Optional[int] = None,
        user_ids: Optional[List[int]] = None,
        is_admin: bool = False,
        force: bool = False
    ) -> SuspendResult:
        """手动复机"""
        success_cards = []
        fail_cards = []

        # 获取卡片
        cards = await CardSuspendCRUD.get_cards_by_ids(
            db, data.card_ids,
            user_id=None if is_admin else user_id,
            user_ids=None if is_admin else user_ids
        )
        card_map = {c.id: c for c in cards}

        supplier_map = await SuspendActionService._load_supplier_map(db, cards)

        for card_id in data.card_ids:
            card = card_map.get(card_id)
            
            if not card:
                fail_cards.append({"card_id": card_id, "iccid": "未知", "reason": "卡片不存在或无权限"})
                continue

            if card.status != CardStatus.suspended:
                fail_cards.append({"card_id": card_id, "iccid": card.iccid, "reason": "卡片未处于停机状态"})
                continue

            can_resume, fail_reason = await SuspendActionService._check_resume_eligibility(
                db=db,
                card=card,
                operator_id=operator_id,
                is_admin=is_admin,
                force=force
            )
            if not can_resume:
                fail_cards.append({"card_id": card_id, "iccid": card.iccid, "reason": fail_reason or "当前不允许复机"})
                continue

            # 调用供应商API复机
            supplier = supplier_map.get(card.supplier_id)
            api_success, callback_no, reconciled_status = await SuspendActionService._call_supplier_resume(
                db=db,
                card=card,
                supplier=supplier,
                operator_id=operator_id
            )

            # 只有API成功才更新数据库
            if not api_success:
                fail_cards.append({"card_id": card_id, "iccid": card.iccid, "reason": "供应商API调用失败"})
                continue

            if reconciled_status in {
                CardStatus.activated.value,
                CardStatus.testing.value,
                CardStatus.silent.value
            }:
                await SuspendActionService._resume_card_with_logging(
                    db=db,
                    card=card,
                    operator_id=operator_id,
                    reason=data.reason or "供应商返回已在使用，已自动纠正本地状态",
                    api_called=bool(callback_no),
                    api_result=json.dumps({"callback_no": callback_no}, ensure_ascii=False) if callback_no else None
                )
            else:
                await SuspendActionService._resume_card_with_logging(
                    db=db,
                    card=card,
                    operator_id=operator_id,
                    reason=data.reason,
                    api_called=bool(callback_no),
                    api_result=json.dumps({"callback_no": callback_no}, ensure_ascii=False) if callback_no else None
                )

            success_cards.append(card.iccid)

        return SuspendResult(
            success_count=len(success_cards),
            fail_count=len(fail_cards),
            success_cards=success_cards,
            fail_cards=fail_cards
        )

    @staticmethod
    async def auto_suspend_expired(db: AsyncSession) -> Dict[str, Any]:
        """自动停卡：到期停卡"""
        cards = await CardSuspendCRUD.get_expired_cards(db)
        suspended_count = 0

        for card in cards:
            # 检查是否有生效的策略
            policies = await SuspendPolicyCRUD.get_active_policies(
                db, "expired", user_id=card.user_id
            )
            
            policy = policies[0] if policies else None
            if policy and policy.auto_suspend != 1:
                continue

            # 执行停卡
            await CardSuspendCRUD.suspend_card(
                db=db,
                card_id=card.id,
                suspend_type=SuspendType.expired,
                reason="套餐到期自动停卡"
            )

            # 记录日志
            await SuspendLogCRUD.create(
                db=db,
                card_id=card.id,
                iccid=card.iccid,
                action=SuspendActionType.suspend,
                suspend_type="expired",
                policy_id=policy.id if policy else None,
                reason="套餐到期自动停卡"
            )

            suspended_count += 1

        return {"suspended_count": suspended_count}

    @staticmethod
    async def auto_suspend_card_exceed(db: AsyncSession) -> Dict[str, Any]:
        """自动停卡：单卡超量"""
        suspended_count = 0
        alerts_created = 0

        # 获取所有启用的单卡超量策略
        policies, _ = await SuspendPolicyCRUD.get_list(
            db, policy_type="card_exceed", is_enabled=True, page_size=1000
        )

        if not policies:
            return {"suspended_count": 0, "alerts_created": 0}

        # 获取激活状态的非池卡
        from sqlalchemy import select
        from app.db.models.iot_card import IotCardModel, CardStatus
        
        result = await db.execute(
            select(IotCardModel).where(
                IotCardModel.is_deleted == 0,
                IotCardModel.status == CardStatus.activated,
                IotCardModel.is_pool_member == 0,
                IotCardModel.data_total > 0
            )
        )
        cards = result.scalars().all()

        for card in cards:
            usage_percent = card.get_data_usage_percent()
            
            # 找到适用的策略
            policy = None
            for p in policies:
                if p.user_id is None or p.user_id == card.user_id:
                    policy = p
                    break
            
            if not policy:
                continue

            # 检查告警阈值
            if usage_percent >= policy.warning_threshold and usage_percent < policy.critical_threshold:
                # 警告级别
                exists = await AlertLogCRUD.check_exists(
                    db, AlertTargetType.card, card.id, AlertLevel.warning
                )
                if not exists:
                    await SuspendActionService._create_alert_and_notify(
                        db=db,
                        target_type=AlertTargetType.card,
                        target_id=card.id,
                        target_name=card.iccid,
                        alert_level=AlertLevel.warning,
                        usage_percent=int(usage_percent),
                        threshold=policy.warning_threshold,
                        policy_id=policy.id,
                        user_id=card.user_id,
                        extra_context={
                            "reason": "单卡流量达到预警阈值"
                        }
                    )
                    alerts_created += 1

            elif usage_percent >= policy.critical_threshold and usage_percent < policy.stop_threshold:
                # 紧急级别
                exists = await AlertLogCRUD.check_exists(
                    db, AlertTargetType.card, card.id, AlertLevel.critical
                )
                if not exists:
                    await SuspendActionService._create_alert_and_notify(
                        db=db,
                        target_type=AlertTargetType.card,
                        target_id=card.id,
                        target_name=card.iccid,
                        alert_level=AlertLevel.critical,
                        usage_percent=int(usage_percent),
                        threshold=policy.critical_threshold,
                        policy_id=policy.id,
                        user_id=card.user_id,
                        extra_context={
                            "reason": "单卡流量达到紧急阈值"
                        }
                    )
                    alerts_created += 1

            elif usage_percent >= policy.stop_threshold:
                # 超限 - 执行停卡
                if policy.auto_suspend == 1:
                    supplier_map = await SuspendActionService._load_supplier_map(db, [card])
                    supplier = supplier_map.get(card.supplier_id)
                    reason = f"单卡流量超限自动停卡({usage_percent}%)"
                    api_success, _, _ = await SuspendActionService._call_supplier_suspend(
                        db=db,
                        card=card,
                        supplier=supplier,
                        reason=reason
                    )
                    if api_success:
                        await CardSuspendCRUD.suspend_card(
                            db=db,
                            card_id=card.id,
                            suspend_type=SuspendType.card_exceed,
                            reason=f"单卡流量超限({usage_percent}%)"
                        )

                        await SuspendLogCRUD.create(
                            db=db,
                            card_id=card.id,
                            iccid=card.iccid,
                            action=SuspendActionType.suspend,
                            suspend_type="card_exceed",
                            policy_id=policy.id,
                            reason=reason
                        )
                        suspended_count += 1

                # 记录超限告警
                exists = await AlertLogCRUD.check_exists(
                    db, AlertTargetType.card, card.id, AlertLevel.exceed
                )
                if not exists:
                    await SuspendActionService._create_alert_and_notify(
                        db=db,
                        target_type=AlertTargetType.card,
                        target_id=card.id,
                        target_name=card.iccid,
                        alert_level=AlertLevel.exceed,
                        usage_percent=int(usage_percent),
                        threshold=policy.stop_threshold,
                        policy_id=policy.id,
                        user_id=card.user_id,
                        extra_context={
                            "reason": f"单卡流量超限({usage_percent}%)"
                        }
                    )
                    alerts_created += 1

        return {"suspended_count": suspended_count, "alerts_created": alerts_created}

    @staticmethod
    async def auto_resume_cards_after_flow_adjustment(
        db: AsyncSession,
        cards: List[IotCardModel],
        operator_id: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Dict[str, int]:
        """补量后自动重检并复机"""
        resumed_count = 0
        supplier_map = await SuspendActionService._load_supplier_map(db, cards)

        for card in cards:
            if card.status != CardStatus.suspended:
                continue

            can_resume, _ = await SuspendActionService._check_resume_eligibility(db, card)
            if not can_resume:
                continue

            supplier = supplier_map.get(card.supplier_id)
            api_success, _, _ = await SuspendActionService._call_supplier_resume(
                db=db,
                card=card,
                supplier=supplier,
                operator_id=operator_id
            )
            if not api_success:
                continue

            await SuspendActionService._resume_card_with_logging(
                db=db,
                card=card,
                operator_id=operator_id,
                reason=reason or "补量后自动复机"
            )
            resumed_count += 1

        return {"resumed_count": resumed_count}


class SupplierCallbackService:
    """供应商回调处理服务"""

    @staticmethod
    async def handle_upiot_sor_callback(
        db: AsyncSession,
        payload: Dict[str, Any]
    ) -> None:
        callback_no = str(payload.get("callback_no") or "").strip()
        if not callback_no:
            logger.warning("UPIOT 停复机回调缺少 callback_no: payload=%s", payload)
            return

        operation = await SupplierSuspendOperationCRUD.get_by_callback_no(db, callback_no)
        if not operation:
            logger.warning("UPIOT 停复机回调未找到操作记录: callback_no=%s payload=%s", callback_no, payload)
            return

        callback_code = str(payload.get("code") or "").strip() or None
        callback_msg = str(payload.get("msg") or "").strip() or None
        account_status = str(payload.get("account_status") or "").strip() or None

        callback_success = (callback_code in {"200", "0", "SUCCESS", "success"} or callback_code is None) and bool(account_status)
        mapped_status = UPIOT_STATUS_MAP.get(account_status or "", None)

        card = await db.get(IotCardModel, operation.card_id)
        if card and mapped_status:
            SuspendActionService.normalize_card_suspend_state(card, mapped_status)

        await SupplierSuspendOperationCRUD.update_callback_result(
            db=db,
            operation=operation,
            callback_payload=json.dumps(payload, ensure_ascii=False),
            callback_code=callback_code,
            callback_msg=callback_msg,
            account_status=account_status,
            callback_status="success" if callback_success else "failed"
        )

        if not callback_success or operation.action != SuspendActionType.suspend:
            return

        request_meta: Dict[str, Any] = {}
        if operation.request_result:
            try:
                request_meta = json.loads(operation.request_result)
            except Exception:
                request_meta = {"raw_request_result": operation.request_result}

        if not request_meta.get("refresh_resume_pending") or request_meta.get("refresh_resume_submitted"):
            return

        if not card:
            logger.warning("刷新自动复机未找到卡片: callback_no=%s", callback_no)
            return

        supplier = None
        if operation.supplier_id:
            supplier_result = await db.execute(
                select(SupplierModel).where(
                    SupplierModel.id == operation.supplier_id,
                    SupplierModel.is_deleted == 0
                )
            )
            supplier = supplier_result.scalar_one_or_none()

        await SuspendActionService.schedule_refresh_resume_after_suspend_confirmed(
            db=db,
            suspend_callback_no=callback_no,
            source="supplier_callback"
        )


class SuspendLogService:
    """停卡记录服务"""

    @staticmethod
    async def get_logs(
        db: AsyncSession,
        card_id: Optional[int] = None,
        action: Optional[str] = None,
        suspend_type: Optional[str] = None,
        pool_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取停卡记录列表"""
        logs, total = await SuspendLogCRUD.get_list(
            db=db,
            card_id=card_id,
            action=action,
            suspend_type=suspend_type,
            pool_id=pool_id,
            start_time=start_time,
            end_time=end_time,
            page=page,
            page_size=page_size
        )
        return [log.to_dict() for log in logs], total


class AlertLogService:
    """告警记录服务"""

    @staticmethod
    async def get_alerts(
        db: AsyncSession,
        target_type: Optional[str] = None,
        alert_level: Optional[str] = None,
        user_id: Optional[int] = None,
        handled: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取告警记录列表"""
        alerts, total = await AlertLogCRUD.get_list(
            db=db,
            target_type=target_type,
            alert_level=alert_level,
            user_id=user_id,
            handled=handled,
            start_time=start_time,
            end_time=end_time,
            page=page,
            page_size=page_size
        )
        return [a.to_dict() for a in alerts], total

    @staticmethod
    async def handle_alert(
        db: AsyncSession,
        alert_id: int,
        handled_by: int,
        handle_remark: Optional[str] = None
    ) -> Optional[dict]:
        """处理告警"""
        alert = await AlertLogCRUD.handle_alert(
            db=db,
            alert_id=alert_id,
            handled_by=handled_by,
            handle_remark=handle_remark
        )
        return alert.to_dict() if alert else None

    @staticmethod
    async def get_unhandled_count(
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> Dict[str, int]:
        """获取未处理告警统计"""
        from sqlalchemy import select
        from sqlalchemy.sql import func
        
        query = select(
            AlertLogModel.alert_level,
            func.count(AlertLogModel.id).label('count')
        ).where(
            AlertLogModel.is_deleted == 0,
            AlertLogModel.handled == 0
        )
        
        if user_id:
            query = query.where(AlertLogModel.user_id == user_id)
        
        query = query.group_by(AlertLogModel.alert_level)
        
        result = await db.execute(query)
        rows = result.all()
        
        stats = {"warning": 0, "critical": 0, "exceed": 0, "total": 0}
        for row in rows:
            level = row[0].value if row[0] else "unknown"
            count = row[1]
            if level in stats:
                stats[level] = count
            stats["total"] += count
        
        return stats
