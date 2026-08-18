"""
套餐周期管理服务
"""
import asyncio
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.supplier_api import get_supplier_client
from app.crud.pool_crud import AUTO_POOL_REMARK, pool_crud
from app.crud.system_crud import SysOperationLogCRUD
from app.db.models.iot_card import CardStatus, CardType, IotCardModel, SuspendType
from app.db.models.package import CARRIER_NAMES, PERIOD_CONFIG, PackageStatus, PeriodType, SalePackageModel
from app.db.models.pool import PoolCardLogModel, PoolStatus, TrafficPoolModel
from app.db.models.supplier import SupplierModel
from app.db.models.sys_log import SysOperationLogModel
from app.flow_packages import is_flow_cycle_active
from app.schemas.package_period import (
    BatchCancelPackagePeriodRequest,
    BatchChangePackageRequest,
    BatchForceActivateRequest,
)
from app.services.sync_service import sync_service
from app.utils.date_utils import calculate_expiry_date, reduce_expiry_date
from app.utils.exceptions import BusinessException

logger = logging.getLogger(__name__)


class PackagePeriodService:
    MODULE_NAME = "package_period"
    MANUAL_FORCE_ACTIVATE_SUPPLIER_CODES = {"002"}
    FORCE_ACTIVATE_RETRY_DELAYS = (3, 8)
    RATE_LIMIT_KEYWORDS = (
        "访问频率",
        "频率限制",
        "限流",
        "rate limit",
        "too many",
        "429",
    )

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
    def _build_change_package_detail(
        old_package: SalePackageModel,
        new_package: SalePackageModel,
        old_pool_name: Optional[str],
        new_pool_name: Optional[str],
        reason: Optional[str],
    ) -> str:
        detail = (
            f"本地修改套餐，原套餐 {old_package.name}({old_package.id})，"
            f"新套餐 {new_package.name}({new_package.id})，"
            f"原流量池 {old_pool_name or '-'}，新流量池 {new_pool_name or '-'}，"
            "未调用供应商改套餐接口"
        )
        if reason:
            detail += f"，原因：{reason}"
        return detail

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
    async def _find_or_create_change_pool(
        db: AsyncSession,
        card: IotCardModel,
        target_package: SalePackageModel,
        operator_id: int,
    ) -> TrafficPoolModel:
        result = await db.execute(
            select(TrafficPoolModel).where(
                TrafficPoolModel.user_id == card.user_id,
                TrafficPoolModel.sale_package_id == target_package.id,
                TrafficPoolModel.carrier == target_package.carrier,
                TrafficPoolModel.flow_size == target_package.flow_size,
                TrafficPoolModel.period_type == target_package.period_type,
                TrafficPoolModel.status == PoolStatus.enable,
                TrafficPoolModel.is_deleted == 0,
            ).order_by(TrafficPoolModel.id).limit(1)
        )
        pool = result.scalar_one_or_none()
        if pool:
            return pool

        carrier = target_package.carrier.value
        period_type = target_package.period_type.value
        flow_size = int(target_package.flow_size)
        flow_display = f"{flow_size}MB" if flow_size < 1024 else f"{flow_size / 1024:g}GB"
        pool = TrafficPoolModel(
            name=f"{CARRIER_NAMES.get(carrier, carrier)}-{flow_display}-{PERIOD_CONFIG[period_type]['name']}-自动池",
            carrier=target_package.carrier,
            flow_size=flow_size,
            period_type=target_package.period_type,
            user_id=card.user_id,
            sale_package_id=target_package.id,
            alert_threshold_1=80,
            alert_threshold_2=90,
            alert_threshold_3=95,
            created_by=operator_id,
            remark=AUTO_POOL_REMARK,
        )
        db.add(pool)
        await db.flush()
        return pool

    @staticmethod
    async def _join_manual_force_activated_card_to_pool(
        db: AsyncSession,
        card: IotCardModel,
        operator_id: int,
    ) -> None:
        if card.card_type != CardType.pool:
            return
        if card.user_id is None:
            raise BusinessException(code=400, msg="SIMBOSS 流量池卡未关联客户，无法自动入池")
        if card.pool_id is not None:
            card.is_pool_member = 1
            await db.flush()
            updated_pool = await pool_crud.update_stats(
                db,
                card.pool_id,
                commit=False,
                run_checks=False,
            )
            if not updated_pool:
                raise BusinessException(code=400, msg="SIMBOSS 卡本地激活后更新流量池失败")
            return
        if not card.sale_package_id:
            raise BusinessException(code=400, msg="SIMBOSS 流量池卡缺少销售套餐，无法自动入池")

        package_result = await db.execute(
            select(SalePackageModel).where(
                SalePackageModel.id == card.sale_package_id,
                SalePackageModel.is_deleted == 0,
            )
        )
        sale_package = package_result.scalar_one_or_none()
        if not sale_package:
            raise BusinessException(code=400, msg="SIMBOSS 流量池卡销售套餐不存在，无法自动入池")

        pool = await PackagePeriodService._find_or_create_change_pool(
            db=db,
            card=card,
            target_package=sale_package,
            operator_id=operator_id,
        )
        card.pool_id = pool.id
        card.is_pool_member = 1
        db.add(PoolCardLogModel(
            pool_id=pool.id,
            card_id=card.id,
            iccid=card.iccid,
            action="add",
            operator_id=operator_id,
            remark="SIMBOSS 管理员确认激活后自动加入流量池",
        ))
        await db.flush()
        updated_pool = await pool_crud.update_stats(
            db,
            pool.id,
            commit=False,
            run_checks=False,
        )
        if not updated_pool:
            raise BusinessException(code=400, msg="SIMBOSS 卡本地激活后更新流量池失败")

    @staticmethod
    async def _fetch_supplier_lifecycle(
        card: IotCardModel,
        supplier: SupplierModel
    ) -> Dict[str, Any]:
        client = get_supplier_client(
            supplier_id=supplier.id,
            api_url=supplier.api_url or "",
            api_key=supplier.api_key or "",
            api_secret=supplier.api_secret or "",
            supplier_code=supplier.code,
            api_config=supplier.api_config,
        )
        return await client.get_card_lifecycle(card.iccid)

    @staticmethod
    def _resolve_force_activate_expired_at(card: IotCardModel, activated_at: date) -> Optional[date]:
        if not card.period_type:
            return None
        return calculate_expiry_date(
            start_date=activated_at,
            period_type=card.period_type.value,
            period_months=card.period_count * 12 if card.period_type.value == "yearly" else card.period_count,
            carrier=card.carrier.value if card.carrier else None
        )

    @staticmethod
    def _supplier_error_text(supplier_meta: Dict[str, Any]) -> str:
        for key in ("supplier_msg", "error", "result", "message", "msg"):
            value = supplier_meta.get(key)
            if value:
                return str(value)
        return ""

    @staticmethod
    def _is_rate_limited_supplier_result(supplier_meta: Dict[str, Any]) -> bool:
        text = PackagePeriodService._supplier_error_text(supplier_meta).lower()
        return any(keyword.lower() in text for keyword in PackagePeriodService.RATE_LIMIT_KEYWORDS)

    @staticmethod
    def _uses_manual_force_activation(supplier: SupplierModel) -> bool:
        supplier_code = str(supplier.code or "").strip().upper()
        return supplier_code in PackagePeriodService.MANUAL_FORCE_ACTIVATE_SUPPLIER_CODES

    @staticmethod
    async def _call_force_activate_supplier(
        client: Any,
        card: IotCardModel
    ) -> tuple[bool, Dict[str, Any]]:
        attempts = len(PackagePeriodService.FORCE_ACTIVATE_RETRY_DELAYS) + 1
        last_meta: Dict[str, Any] = {}

        for attempt in range(attempts):
            supplier_success = await client.force_activate_card(
                iccid=card.iccid,
                card_no=card.msisdn or card.iccid
            )
            supplier_meta = dict(getattr(client, "last_force_activate_result", None) or {"submitted": supplier_success})
            supplier_meta["attempts"] = attempt + 1
            last_meta = supplier_meta

            if supplier_success:
                return True, supplier_meta

            if (
                attempt < attempts - 1
                and PackagePeriodService._is_rate_limited_supplier_result(supplier_meta)
            ):
                delay_seconds = PackagePeriodService.FORCE_ACTIVATE_RETRY_DELAYS[attempt]
                logger.warning(
                    "force activate rate limited, retrying: iccid=%s attempt=%s delay=%ss error=%s",
                    card.iccid,
                    attempt + 1,
                    delay_seconds,
                    PackagePeriodService._supplier_error_text(supplier_meta),
                )
                await asyncio.sleep(delay_seconds)
                continue

            return False, supplier_meta

        return False, last_meta

    @staticmethod
    def _add_operation_log(
        db: AsyncSession,
        action: str,
        operator_id: int,
        operator_name: Optional[str],
        card: IotCardModel,
        detail: str
    ) -> None:
        db.add(SysOperationLogModel(
            module=PackagePeriodService.MODULE_NAME,
            action=action,
            user_id=operator_id,
            user_name=operator_name,
            target_type="card",
            target_id=card.id,
            target_name=card.iccid,
            detail=detail,
            is_success=1,
        ))

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
            manual_force_activation = PackagePeriodService._uses_manual_force_activation(supplier)
            if manual_force_activation and card.status != CardStatus.silent:
                failed_list.append({"iccid": iccid, "error": "SIMBOSS 手动激活仅支持沉默期卡"})
                continue

            old_status = card.status.value if card.status else "unknown"
            old_activated_at = card.activated_at
            old_expired_at = card.expired_at

            try:
                lifecycle_source = "supplier_force_activate"
                if manual_force_activation:
                    supplier_meta = {
                        "submitted": False,
                        "skipped": True,
                        "manual_supplier_activation": True,
                        "supplier_code": supplier.code,
                        "supplier_msg": "管理员已确认供应商侧完成激活，平台仅同步本地状态",
                    }
                    lifecycle_source = "manual_supplier_confirmed"
                else:
                    client = get_supplier_client(
                        supplier_id=supplier.id,
                        api_url=supplier.api_url or "",
                        api_key=supplier.api_key or "",
                        api_secret=supplier.api_secret or "",
                        supplier_code=supplier.code,
                        api_config=supplier.api_config,
                    )
                    supplier_success, supplier_meta = await PackagePeriodService._call_force_activate_supplier(client, card)
                    if not supplier_success:
                        failed_list.append({
                            "iccid": iccid,
                            "error": PackagePeriodService._supplier_error_text(supplier_meta) or "供应商接口调用失败"
                        })
                        continue

                today = date.today()
                activated_at = today
                expired_at = PackagePeriodService._resolve_force_activate_expired_at(card, activated_at)

                card.activated_at = activated_at
                card.expired_at = expired_at
                card.status = CardStatus.activated
                card.suspend_type = SuspendType.none
                card.suspend_at = None
                card.suspend_reason = None

                if manual_force_activation:
                    await PackagePeriodService._join_manual_force_activated_card_to_pool(
                        db=db,
                        card=card,
                        operator_id=operator_id,
                    )
                elif card.card_type == CardType.pool and card.pool_id is None and card.user_id is not None:
                    await sync_service._auto_join_pool(db, card)

                detail = PackagePeriodService._build_force_activate_detail(
                    card=card,
                    old_status=old_status,
                    old_activated_at=old_activated_at,
                    old_expired_at=old_expired_at,
                    reason=data.reason,
                    lifecycle_source=lifecycle_source
                )
                PackagePeriodService._add_operation_log(
                    db=db,
                    action="force_activate",
                    operator_id=operator_id,
                    operator_name=operator_name,
                    card=card,
                    detail=detail
                )
                await db.commit()
                await db.refresh(card)

                success_list.append({
                    "iccid": card.iccid,
                    "activated_at": card.activated_at.isoformat() if card.activated_at else None,
                    "expired_at": card.expired_at.isoformat() if card.expired_at else None,
                    "pool_id": card.pool_id,
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
                PackagePeriodService._add_operation_log(
                    db=db,
                    action="cancel_period",
                    operator_id=operator_id,
                    operator_name=operator_name,
                    card=card,
                    detail=detail
                )
                await db.commit()
                await db.refresh(card)

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
    async def get_package_options(db: AsyncSession) -> List[Dict[str, Any]]:
        result = await db.execute(
            select(SalePackageModel).where(
                SalePackageModel.period_type == PeriodType.monthly,
                SalePackageModel.status == PackageStatus.enable,
                SalePackageModel.is_deleted == 0,
            ).order_by(
                SalePackageModel.user_id,
                SalePackageModel.sort_order,
                SalePackageModel.name,
            )
        )
        return [package.to_dict() for package in result.scalars().all()]

    @staticmethod
    async def batch_change_package(
        db: AsyncSession,
        data: BatchChangePackageRequest,
        operator_id: int,
        operator_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        iccids = PackagePeriodService._normalize_iccids(data.iccids)
        target_result = await db.execute(
            select(SalePackageModel).where(
                SalePackageModel.id == data.target_sale_package_id,
                SalePackageModel.status == PackageStatus.enable,
                SalePackageModel.is_deleted == 0,
            )
        )
        target_package = target_result.scalar_one_or_none()
        if not target_package:
            raise BusinessException(code=400, msg="目标销售套餐不存在或已停用")
        if target_package.period_type != PeriodType.monthly:
            raise BusinessException(code=400, msg="修改套餐当前仅支持月包")

        cards = await PackagePeriodService._load_cards_by_iccids(db, iccids)
        card_map = {card.iccid: card for card in cards}
        package_ids = {card.sale_package_id for card in cards if card.sale_package_id}
        package_result = await db.execute(
            select(SalePackageModel).where(SalePackageModel.id.in_(package_ids))
        ) if package_ids else None
        package_map = {
            package.id: package
            for package in (package_result.scalars().all() if package_result else [])
        }

        success_list: List[Dict[str, Any]] = []
        failed_list: List[Dict[str, Any]] = []
        affected_pool_ids = set()
        allowed_statuses = {
            CardStatus.testing,
            CardStatus.silent,
            CardStatus.activated,
            CardStatus.suspended,
        }

        for iccid in iccids:
            card = card_map.get(iccid)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在"})
                continue
            old_package = package_map.get(card.sale_package_id or 0)
            if not old_package:
                failed_list.append({"iccid": iccid, "error": "卡片缺少有效的原销售套餐"})
                continue
            if card.sale_package_id == target_package.id:
                failed_list.append({"iccid": iccid, "error": "卡片已使用目标套餐"})
                continue
            if card.user_id is None:
                failed_list.append({"iccid": iccid, "error": "仅支持已出库卡片修改套餐"})
                continue
            if card.status not in allowed_statuses:
                failed_list.append({"iccid": iccid, "error": f"当前卡片状态不支持修改套餐: {card.status.value}"})
                continue
            if card.period_type != PeriodType.monthly:
                failed_list.append({"iccid": iccid, "error": "仅支持原月包卡片修改套餐"})
                continue
            if card.carrier != target_package.carrier:
                failed_list.append({"iccid": iccid, "error": "目标套餐运营商与卡片不一致"})
                continue
            if target_package.user_id is not None and target_package.user_id != card.user_id:
                failed_list.append({"iccid": iccid, "error": "目标套餐不属于该卡片客户"})
                continue

            old_pool_id = card.pool_id
            old_pool_name = None
            new_pool = None
            was_pool_member = bool(card.pool_id and card.is_pool_member == 1)

            try:
                async with db.begin_nested():
                    if old_pool_id:
                        old_pool = await pool_crud.get_by_id(db, old_pool_id)
                        old_pool_name = old_pool.name if old_pool else None
                        card.pool_id = None
                        card.is_pool_member = 0
                        if was_pool_member:
                            db.add(PoolCardLogModel(
                                pool_id=old_pool_id,
                                card_id=card.id,
                                iccid=card.iccid,
                                action="remove",
                                operator_id=operator_id,
                                remark="修改套餐自动退出原流量池",
                            ))
                        affected_pool_ids.add(old_pool_id)

                    effective_addon = int(card.addon_flow or 0)
                    if card.addon_flow_month and not is_flow_cycle_active(card.addon_flow_month):
                        effective_addon = 0
                        card.addon_flow = 0
                        card.addon_flow_month = None

                    card.sale_package_id = target_package.id
                    card.sale_price = target_package.price_sale
                    card.flow_size = target_package.flow_size
                    card.period_type = target_package.period_type
                    card.data_total = int(target_package.flow_size) + effective_addon

                    should_join_pool = (
                        card.card_type == CardType.pool
                        and (was_pool_member or card.status == CardStatus.activated)
                    )
                    if should_join_pool:
                        new_pool = await PackagePeriodService._find_or_create_change_pool(
                            db=db,
                            card=card,
                            target_package=target_package,
                            operator_id=operator_id,
                        )
                        card.pool_id = new_pool.id
                        card.is_pool_member = 1
                        db.add(PoolCardLogModel(
                            pool_id=new_pool.id,
                            card_id=card.id,
                            iccid=card.iccid,
                            action="add",
                            operator_id=operator_id,
                            remark="修改套餐自动加入目标流量池",
                        ))
                        affected_pool_ids.add(new_pool.id)

                    PackagePeriodService._add_operation_log(
                        db=db,
                        action="change_package",
                        operator_id=operator_id,
                        operator_name=operator_name,
                        card=card,
                        detail=PackagePeriodService._build_change_package_detail(
                            old_package=old_package,
                            new_package=target_package,
                            old_pool_name=old_pool_name,
                            new_pool_name=new_pool.name if new_pool else None,
                            reason=data.reason,
                        ),
                    )

                success_list.append({
                    "iccid": card.iccid,
                    "old_package_id": old_package.id,
                    "old_package_name": old_package.name,
                    "new_package_id": target_package.id,
                    "new_package_name": target_package.name,
                    "old_pool_id": old_pool_id,
                    "old_pool_name": old_pool_name,
                    "new_pool_id": new_pool.id if new_pool else None,
                    "new_pool_name": new_pool.name if new_pool else None,
                })
            except Exception:
                logger.exception("修改本地套餐失败: iccid=%s", iccid)
                failed_list.append({"iccid": iccid, "error": "处理失败，请查看后台日志"})

        for pool_id in sorted(affected_pool_ids):
            await pool_crud.update_stats(
                db,
                pool_id,
                commit=False,
                run_checks=False,
            )

        await db.commit()

        pool_check_warnings = []
        for pool_id in sorted(affected_pool_ids):
            try:
                await pool_crud.update_stats(db, pool_id)
            except Exception as exc:
                await db.rollback()
                logger.exception("套餐修改后流量池检查失败: pool_id=%s", pool_id)
                pool_check_warnings.append({"pool_id": pool_id, "error": str(exc)})

        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list,
            "pool_check_warnings": pool_check_warnings,
            "supplier_synced": False,
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
        if action not in {"force_activate", "cancel_period", "change_package"}:
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
