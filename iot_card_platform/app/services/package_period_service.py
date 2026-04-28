"""
套餐周期管理服务
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.supplier_api import get_supplier_client
from app.crud.system_crud import SysOperationLogCRUD
from app.db.models.iot_card import CardStatus, IotCardModel, SuspendType
from app.db.models.sys_user import UserLevel
from app.db.models.supplier import SupplierModel
from app.schemas.package_period import (
    BatchCancelPackagePeriodRequest,
    BatchForceActivateRequest,
)
from app.services.sync_service import sync_service
from app.utils.date_utils import calculate_expiry_date, reduce_expiry_date
from app.utils.exceptions import BusinessException


class PackagePeriodService:
    MODULE_NAME = "package_period"

    @staticmethod
    def _normalize_iccids(iccids: List[str]) -> List[str]:
        normalized: List[str] = []
        seen = set()
        for item in iccids:
            iccid = (item or "").strip()
            if not iccid or iccid in seen:
                continue
            seen.add(iccid)
            normalized.append(iccid)
        if not normalized:
            raise BusinessException(code=400, msg="请输入有效的 ICCID")
        return normalized

    @staticmethod
    def _format_date(value: Optional[date]) -> str:
        return value.isoformat() if value else "-"

    @staticmethod
    def _build_force_activate_detail(
        card: IotCardModel,
        old_status: str,
        old_activated_at: Optional[date],
        old_expired_at: Optional[date],
        reason: Optional[str],
        lifecycle_source: str
    ) -> str:
        base = (
            f"强制激活，原状态 {old_status}，原激活日 {PackagePeriodService._format_date(old_activated_at)}，"
            f"原到期 {PackagePeriodService._format_date(old_expired_at)}，"
            f"新激活日 {PackagePeriodService._format_date(card.activated_at)}，"
            f"新到期 {PackagePeriodService._format_date(card.expired_at)}，"
            f"来源 {lifecycle_source}"
        )
        if reason:
            base += f"，原因：{reason}"
        return base

    @staticmethod
    def _build_cancel_period_detail(
        old_expired_at: Optional[date],
        new_expired_at: Optional[date],
        cancel_count: int,
        unit_name: str,
        reason: Optional[str]
    ) -> str:
        base = (
            f"取消计划套餐 {cancel_count}{unit_name}，原到期 {PackagePeriodService._format_date(old_expired_at)}，"
            f"新到期 {PackagePeriodService._format_date(new_expired_at)}"
        )
        if reason:
            base += f"，原因：{reason}"
        return base

    @staticmethod
    async def _load_cards_by_iccids(
        db: AsyncSession,
        iccids: List[str]
    ) -> List[IotCardModel]:
        result = await db.execute(
            select(IotCardModel).where(
                IotCardModel.iccid.in_(iccids),
                IotCardModel.is_deleted == 0
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def _load_supplier_map(
        db: AsyncSession,
        cards: List[IotCardModel]
    ) -> Dict[int, SupplierModel]:
        supplier_ids = sorted({card.supplier_id for card in cards if card.supplier_id})
        if not supplier_ids:
            return {}
        result = await db.execute(
            select(SupplierModel).where(
                SupplierModel.id.in_(supplier_ids),
                SupplierModel.is_deleted == 0
            )
        )
        return {item.id: item for item in result.scalars().all()}

    @staticmethod
    async def _fetch_supplier_lifecycle(
        card: IotCardModel,
        supplier: SupplierModel
    ) -> Dict[str, Any]:
        client = get_supplier_client(
            supplier_id=supplier.id,
            api_url=supplier.api_url or "",
            api_key=supplier.api_key or "",
            api_secret=supplier.api_secret or ""
        )
        return await client.get_card_lifecycle(card.iccid)

    @staticmethod
    async def batch_force_activate(
        db: AsyncSession,
        data: BatchForceActivateRequest,
        operator_id: int,
        operator_name: Optional[str] = None
    ) -> Dict[str, Any]:
        iccids = PackagePeriodService._normalize_iccids(data.iccids)
        cards = await PackagePeriodService._load_cards_by_iccids(db, iccids)
        card_map = {card.iccid: card for card in cards}
        supplier_map = await PackagePeriodService._load_supplier_map(db, cards)

        success_list: List[Dict[str, Any]] = []
        failed_list: List[Dict[str, Any]] = []

        for iccid in iccids:
            card = card_map.get(iccid)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在"})
                continue
            if card.status not in {CardStatus.testing, CardStatus.silent}:
                failed_list.append({"iccid": iccid, "error": f"仅支持测试期/沉默期卡，当前状态: {card.status.value}"})
                continue
            supplier = supplier_map.get(card.supplier_id or 0)
            if not supplier:
                failed_list.append({"iccid": iccid, "error": "卡片未绑定供应商或供应商不存在"})
                continue

            old_status = card.status.value if card.status else "unknown"
            old_activated_at = card.activated_at
            old_expired_at = card.expired_at

            try:
                client = get_supplier_client(
                    supplier_id=supplier.id,
                    api_url=supplier.api_url or "",
                    api_key=supplier.api_key or "",
                    api_secret=supplier.api_secret or ""
                )
                supplier_success = await client.force_activate_card(
                    iccid=card.iccid,
                    card_no=card.msisdn or card.iccid
                )
                supplier_meta = getattr(client, "last_force_activate_result", None) or {"submitted": supplier_success}
                if not supplier_success:
                    failed_list.append({
                        "iccid": iccid,
                        "error": supplier_meta.get("supplier_msg") or "供应商接口调用失败"
                    })
                    continue

                lifecycle_source = "fallback_local"
                lifecycle = {}
                try:
                    lifecycle = await PackagePeriodService._fetch_supplier_lifecycle(card, supplier)
                except Exception:
                    lifecycle = {}

                supplier_status = str(lifecycle.get("status") or "").strip()
                supplier_activated_at = lifecycle.get("activated_at")
                supplier_expired_at = lifecycle.get("expired_at")

                today = date.today()
                activated_at = today
                if supplier_activated_at:
                    activated_at = datetime.strptime(supplier_activated_at, "%Y-%m-%d").date()
                    lifecycle_source = "supplier_lifecycle"

                expired_at = None
                if supplier_expired_at:
                    expired_at = datetime.strptime(supplier_expired_at, "%Y-%m-%d").date()
                    lifecycle_source = "supplier_lifecycle"
                elif card.period_type:
                    expired_at = calculate_expiry_date(
                        start_date=activated_at,
                        period_type=card.period_type.value,
                        period_months=card.period_count * 12 if card.period_type.value == "yearly" else card.period_count,
                        carrier=card.carrier.value if card.carrier else None
                    )

                card.activated_at = activated_at
                card.expired_at = expired_at
                card.status = CardStatus.activated if supplier_status not in {"testing", "silent"} else CardStatus.activated
                card.suspend_type = SuspendType.none
                card.suspend_at = None
                card.suspend_reason = None

                if card.card_type.value == "pool" and card.pool_id is None and card.user_id is not None:
                    await sync_service._auto_join_pool(db, card)

                detail = PackagePeriodService._build_force_activate_detail(
                    card=card,
                    old_status=old_status,
                    old_activated_at=old_activated_at,
                    old_expired_at=old_expired_at,
                    reason=data.reason,
                    lifecycle_source=lifecycle_source
                )
                await db.commit()
                await db.refresh(card)

                await SysOperationLogCRUD.create(
                    db=db,
                    module=PackagePeriodService.MODULE_NAME,
                    action="force_activate",
                    user_id=operator_id,
                    user_name=operator_name,
                    target_type="card",
                    target_id=card.id,
                    target_name=card.iccid,
                    detail=detail
                )

                success_list.append({
                    "iccid": card.iccid,
                    "activated_at": card.activated_at.isoformat() if card.activated_at else None,
                    "expired_at": card.expired_at.isoformat() if card.expired_at else None,
                    "supplier_result": supplier_meta
                })
            except Exception as exc:
                await db.rollback()
                failed_list.append({"iccid": iccid, "error": str(exc)})

        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    @staticmethod
    async def batch_cancel_package_period(
        db: AsyncSession,
        data: BatchCancelPackagePeriodRequest,
        operator_id: int,
        operator_name: Optional[str] = None
    ) -> Dict[str, Any]:
        iccids = PackagePeriodService._normalize_iccids(data.iccids)
        cards = await PackagePeriodService._load_cards_by_iccids(db, iccids)
        card_map = {card.iccid: card for card in cards}

        success_list: List[Dict[str, Any]] = []
        failed_list: List[Dict[str, Any]] = []
        today = date.today()

        for iccid in iccids:
            card = card_map.get(iccid)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在"})
                continue
            if card.status != CardStatus.activated:
                failed_list.append({"iccid": iccid, "error": f"仅支持已激活卡片，当前状态: {card.status.value}"})
                continue
            if not card.expired_at:
                failed_list.append({"iccid": iccid, "error": "卡片缺少到期日期"})
                continue
            if not card.period_type:
                failed_list.append({"iccid": iccid, "error": "卡片缺少套餐周期类型"})
                continue

            try:
                old_expired_at = card.expired_at
                new_expired_at = reduce_expiry_date(
                    current_expiry=card.expired_at,
                    period_type=card.period_type.value,
                    reduce_count=data.cancel_count,
                    carrier=card.carrier.value if card.carrier else None
                )
                if card.activated_at and new_expired_at < card.activated_at:
                    failed_list.append({"iccid": iccid, "error": "减少后到期时间早于激活时间，无法取消"})
                    continue
                if new_expired_at < today:
                    failed_list.append({"iccid": iccid, "error": "减少后到期时间早于今天，请先人工核对后再处理"})
                    continue

                card.expired_at = new_expired_at
                detail = PackagePeriodService._build_cancel_period_detail(
                    old_expired_at=old_expired_at,
                    new_expired_at=new_expired_at,
                    cancel_count=data.cancel_count,
                    unit_name="年" if card.period_type.value == "yearly" else "个月",
                    reason=data.reason
                )
                await db.commit()
                await db.refresh(card)

                await SysOperationLogCRUD.create(
                    db=db,
                    module=PackagePeriodService.MODULE_NAME,
                    action="cancel_period",
                    user_id=operator_id,
                    user_name=operator_name,
                    target_type="card",
                    target_id=card.id,
                    target_name=card.iccid,
                    detail=detail
                )

                success_list.append({
                    "iccid": card.iccid,
                    "old_expired_at": old_expired_at.isoformat() if old_expired_at else None,
                    "new_expired_at": new_expired_at.isoformat() if new_expired_at else None
                })
            except Exception as exc:
                await db.rollback()
                failed_list.append({"iccid": iccid, "error": str(exc)})

        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    @staticmethod
    async def get_operation_logs(
        db: AsyncSession,
        action: str,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        if action not in {"force_activate", "cancel_period"}:
            raise BusinessException(code=400, msg="不支持的操作类型")

        logs, total = await SysOperationLogCRUD.get_list(
            db=db,
            module=PackagePeriodService.MODULE_NAME,
            action=action,
            target_type="card",
            is_success=True,
            start_time=start_time,
            end_time=end_time,
            page=page,
            page_size=page_size
        )

        return {
            "items": [
                {
                    "id": log.id,
                    "action": log.action,
                    "operation_time": log.created_at.isoformat() if log.created_at else None,
                    "card_no": log.target_name,
                    "operator_name": log.user_name,
                    "detail": log.detail
                }
                for log in logs
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }


package_period_service = PackagePeriodService()
