"""
物联网卡服务层
"""
import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, bindparam
from app.crud.iot_card_crud import iot_card_crud, card_transfer_crud
from app.crud.package_crud import sale_package_crud
from app.db.models.iot_card import IotCardModel, CardStatus, SuspendType
from app.db.models.package import PeriodType
from app.db.models.sys_user import UserLevel, SysUserModel
from app.crud.sys_user_crud_enhanced import SysUserCRUDEnhanced
from app.crud.system_crud import SysOperationLogCRUD
from app.services.suspend_service import SuspendActionService
from app.schemas.suspend import ManualResume, ManualSuspend
from app.config import settings
from app.flow_packages import (
    FLOW_PACKAGE_LABELS,
    FLOW_PACKAGE_PRICES,
    get_current_flow_cycle_month,
    is_flow_cycle_active,
)
from app.services.account_balance_service import account_balance_service
from app.utils.exceptions import BusinessException
from app.clients.supplier_api import get_supplier_client


class IotCardService:
    """物联网卡服务"""

    RESTART_ACTIVE_STATUSES = {
        CardStatus.activated.value,
        CardStatus.testing.value,
        CardStatus.silent.value,
    }
    RESTART_ALLOWED_STATUSES = RESTART_ACTIVE_STATUSES | {
        CardStatus.suspended.value,
    }
    RESTART_PROTECTED_SUSPEND_TYPES = {
        SuspendType.expired,
        SuspendType.card_exceed,
        SuspendType.pool_exceed,
        SuspendType.device_separation,
    }

    async def _get_stock_out_no_map(
        self,
        db: AsyncSession,
        card_ids: List[int]
    ) -> dict[int, str]:
        """获取卡片最近一次出库单号"""
        if not card_ids:
            return {}

        sql = text("""
            SELECT sorc.card_id, sor.record_no
            FROM stock_out_record_cards sorc
            INNER JOIN stock_out_records sor ON sorc.record_id = sor.id
            WHERE sorc.card_id IN :card_ids
              AND sor.is_deleted = 0
              AND sorc.is_deleted = 0
            ORDER BY sor.id DESC, sorc.id DESC
        """).bindparams(bindparam("card_ids", expanding=True))

        result = await db.execute(sql, {"card_ids": card_ids})
        stock_out_no_map: dict[int, str] = {}
        for card_id, record_no in result.all():
            if card_id not in stock_out_no_map:
                stock_out_no_map[card_id] = record_no
        return stock_out_no_map

    async def _hydrate_card_dicts(
        self,
        db: AsyncSession,
        card_dicts: List[dict],
        current_user_id: int
    ) -> List[dict]:
        """补齐当前用户视角下的备注和出库单号"""
        if not card_dicts:
            return card_dicts

        card_ids = [item["id"] for item in card_dicts if item.get("id") is not None]
        card_user_ids = {
            item["user_id"] for item in card_dicts
            if item.get("user_id") is not None
        }
        remark_map = await iot_card_crud.get_user_remark_map(db, card_ids, current_user_id)
        stock_out_no_map = await self._get_stock_out_no_map(db, card_ids)
        user_ids_for_display = list(card_user_ids | {current_user_id})
        user_result = await db.execute(
            select(SysUserModel).where(SysUserModel.id.in_(user_ids_for_display))
        )
        user_map = {
            user.id: user
            for user in user_result.scalars().all()
        }
        current_user = user_map.get(current_user_id)
        current_user_display_name = None
        if current_user:
            current_user_display_name = current_user.name or current_user.account

        for item in card_dicts:
            card_id = item.get("id")
            item["remark"] = remark_map.get(card_id)
            item["stock_out_no"] = stock_out_no_map.get(card_id)
            related_user = user_map.get(item.get("user_id"))
            if related_user:
                item["related_user_name"] = related_user.name or related_user.account
            else:
                item["related_user_name"] = current_user_display_name

        return card_dicts

    @staticmethod
    def _normalize_price(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _build_supplier_renew_warning(card: IotCardModel) -> Optional[str]:
        """
        当前续费逻辑仅更新本地套餐周期，未调用供应商续费接口。
        对供应商卡直接返回提示，避免前端继续把本地续费误认为供应商已同步。
        """
        if not getattr(card, "supplier_id", None):
            return None
        return "已更新本地套餐周期，当前版本未同步供应商续费周期"

    @staticmethod
    def _get_effective_card_addon_flow(card: IotCardModel) -> int:
        if card.addon_flow and not card.addon_flow_month:
            return int(card.addon_flow or 0)
        if is_flow_cycle_active(card.addon_flow_month):
            return int(card.addon_flow or 0)
        return 0

    def _reset_expired_card_addon_flow(self, card: IotCardModel) -> None:
        if not card.addon_flow:
            card.addon_flow_month = None
            return
        if is_flow_cycle_active(card.addon_flow_month):
            return
        card.data_total = max(0, int(card.data_total or 0) - int(card.addon_flow or 0))
        card.addon_flow = 0
        card.addon_flow_month = None

    def _apply_card_addon_flow(self, card: IotCardModel, added_flow_mb: int) -> None:
        self._reset_expired_card_addon_flow(card)
        base_total = max(0, int(card.data_total or 0) - self._get_effective_card_addon_flow(card))
        card.addon_flow = self._get_effective_card_addon_flow(card) + added_flow_mb
        card.addon_flow_month = get_current_flow_cycle_month()
        card.data_total = base_total + card.addon_flow

    async def _resolve_card_sale_price(
        self,
        db: AsyncSession,
        card: IotCardModel
    ) -> Optional[Decimal]:
        if card.sale_price:
            return Decimal(str(card.sale_price))

        if not card.sale_package_id:
            return None

        package = await sale_package_crud.get_by_id(db, card.sale_package_id)
        if package and package.price_sale:
            return Decimal(str(package.price_sale))

        return None

    @staticmethod
    def _resolve_renew_period(
        card: IotCardModel,
        package,
        renew_cycles: int
    ) -> tuple[str, Optional[int], Optional[int]]:
        """解析续费周期，按用户选择的续费月数计算。"""
        if package and package.period_type:
            period_type = package.period_type.value if hasattr(package.period_type, "value") else str(package.period_type)
        else:
            period_type = card.period_type.value if hasattr(card.period_type, "value") else str(card.period_type)

        return period_type, renew_cycles, None

    @staticmethod
    def _resolve_yearly_renew_flow(package, renew_months: int) -> int:
        """年包流量跨月累计，续费时按续费月数追加新周期可用流量。"""
        flow_size = int(getattr(package, "flow_size", 0) or 0)
        if flow_size <= 0 or renew_months <= 0:
            return 0
        return (flow_size * renew_months + 11) // 12

    @staticmethod
    def _apply_yearly_renew_flow(card: IotCardModel, package, renew_months: int) -> None:
        card_period_type = getattr(card, "period_type", None)
        period_type = card_period_type.value if hasattr(card_period_type, "value") else str(card_period_type)
        if period_type != PeriodType.yearly.value:
            return
        added_flow = IotCardService._resolve_yearly_renew_flow(package, renew_months)
        if added_flow > 0:
            card.data_total = int(card.data_total or 0) + added_flow

    @staticmethod
    def _parse_supplier_expired_at(value) -> Optional[date]:
        """解析供应商返回的到期日。"""
        if not value:
            return None
        if isinstance(value, date):
            return value
        try:
            return datetime.strptime(str(value), "%Y-%m-%d").date()
        except ValueError:
            return None

    async def _resolve_renew_base_date(
        self,
        db: AsyncSession,
        card: IotCardModel
    ) -> date:
        """续费基准日优先取本地到期日，超量停卡年包从停卡月份重新起算。"""
        card_period_type = getattr(card, "period_type", None)
        card_suspend_type = getattr(card, "suspend_type", None)
        period_type = card_period_type.value if hasattr(card_period_type, "value") else str(card_period_type)
        suspend_type = card_suspend_type.value if hasattr(card_suspend_type, "value") else str(card_suspend_type)
        if period_type == PeriodType.yearly.value and suspend_type == SuspendType.card_exceed.value:
            suspend_date = card.suspend_at.date() if card.suspend_at else date.today()
            return suspend_date - timedelta(days=1)

        if card.expired_at:
            return card.expired_at

        if card.supplier_id:
            from app.crud.supplier_crud import supplier_crud

            supplier = await supplier_crud.get_by_id(db, card.supplier_id)
            if supplier:
                try:
                    client = get_supplier_client(
                        supplier_id=card.supplier_id,
                        api_url=supplier.api_url or "",
                        api_key=supplier.api_key or "",
                        api_secret=supplier.api_secret or ""
                    )
                    lifecycle = await client.get_card_lifecycle(card.iccid)
                    supplier_expired_at = self._parse_supplier_expired_at(
                        lifecycle.get("expired_at")
                    )
                    if supplier_expired_at:
                        return supplier_expired_at
                except Exception:
                    pass

        return date.today()

    async def _get_accessible_user_ids(
        self,
        db: AsyncSession,
        current_user_id: int,
        user_level: int
    ) -> Optional[List[int]]:
        """获取当前用户可见的用户范围"""
        if user_level == UserLevel.SUPER_ADMIN.value:
            return None

        if user_level == UserLevel.SUB_USER.value:
            return [current_user_id]

        sys_user_crud = SysUserCRUDEnhanced()
        child_ids = await sys_user_crud.get_children_ids(db, current_user_id)
        return [current_user_id, *child_ids]

    async def _get_cards_by_iccids_in_scope(
        self,
        db: AsyncSession,
        iccids: List[str],
        current_user_id: int,
        user_level: int
    ) -> List[IotCardModel]:
        """按当前用户可见范围查询卡片"""
        from sqlalchemy import select

        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        if user_ids is not None:
            query = query.where(IotCardModel.user_id.in_(user_ids))

        result = await db.execute(query)
        return list(result.scalars().all())

    async def _get_direct_child_user_ids(
        self,
        db: AsyncSession,
        current_user_id: int,
        user_level: int
    ) -> Optional[List[int]]:
        """获取可直接后台补量的目标用户"""
        if user_level == UserLevel.SUPER_ADMIN.value:
            return None
        if user_level == UserLevel.SUB_USER.value:
            return []

        result = await db.execute(
            select(SysUserModel.id).where(
                SysUserModel.parent_id == current_user_id,
                SysUserModel.is_deleted == 0
            )
        )
        return [row[0] for row in result.all()]

    async def _get_supplier_lifecycle_status(
        self,
        card: IotCardModel,
        supplier
    ) -> str:
        supplier_client = get_supplier_client(
            supplier_id=card.supplier_id,
            api_url=supplier.api_url or "",
            api_key=supplier.api_key or "",
            api_secret=supplier.api_secret or ""
        )
        lifecycle = await supplier_client.get_card_lifecycle(card.iccid)
        return str(lifecycle.get("status") or "").strip()

    async def _wait_for_supplier_status(
        self,
        db: AsyncSession,
        card: IotCardModel,
        supplier,
        expected_statuses: set[str],
        timeout_seconds: int
    ) -> Optional[str]:
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        latest_status = None

        while True:
            latest_status = await self._get_supplier_lifecycle_status(card, supplier)
            if latest_status:
                SuspendActionService.normalize_card_suspend_state(card, latest_status)
                await db.commit()
                await db.refresh(card)

            if latest_status in expected_statuses:
                return latest_status

            if asyncio.get_running_loop().time() >= deadline:
                return latest_status

            await asyncio.sleep(settings.refresh_status_poll_interval_seconds)

    async def get_cards(
        self,
        db: AsyncSession,
        current_user_id: int,
        user_level: int,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        carrier: Optional[str] = None,
        flow_size: Optional[int] = None,
        period_type: Optional[str] = None,
        card_type: Optional[str] = None,
        pool_id: Optional[int] = None,
        is_pool_member: Optional[bool] = None,
        over_usage: Optional[bool] = None,
        remark: Optional[str] = None,
        customer_id: Optional[int] = None,
        batch_id: Optional[str] = None,
        project_id: Optional[int] = None,
        stock_out_start: Optional[str] = None,
        stock_out_end: Optional[str] = None,
        activated_start: Optional[str] = None,
        activated_end: Optional[str] = None,
        expired_start: Optional[str] = None,
        expired_end: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        """获取卡片列表 (根据用户权限过滤)"""
        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)

        items, total = await iot_card_crud.get_list(
            db=db,
            user_ids=user_ids,
            keyword=keyword,
            status=status,
            carrier=carrier,
            flow_size=flow_size,
            period_type=period_type,
            card_type=card_type,
            pool_id=pool_id,
            is_pool_member=is_pool_member,
            over_usage=over_usage,
            remark=remark,
            customer_id=customer_id,
            batch_id=batch_id,
            project_id=project_id,
            stock_out_start=stock_out_start,
            stock_out_end=stock_out_end,
            activated_start=activated_start,
            activated_end=activated_end,
            expired_start=expired_start,
            expired_end=expired_end,
            page=page,
            page_size=page_size,
            remark_user_id=current_user_id,
            sort_by=sort_by,
            sort_order=sort_order
        )

        card_dicts = [item.to_dict() for item in items]
        await self._hydrate_card_dicts(db, card_dicts, current_user_id)
        return card_dicts, total

    async def get_card_detail(
        self,
        db: AsyncSession,
        card_id: int,
        current_user_id: int,
        user_level: int
    ) -> Optional[dict]:
        """获取卡片详情"""
        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)
        card = await iot_card_crud.get_by_id_in_scope(db, card_id, user_ids)
        if not card:
            raise BusinessException(code=404, msg="卡片不存在或无权访问")

        card_dict = card.to_dict()
        await self._hydrate_card_dicts(db, [card_dict], current_user_id)

        # 兼容历史数据：部分停机卡状态已更新，但卡表未回填 suspend_at/suspend_reason
        if card.status and card.status.value == "suspended" and not card_dict.get("suspend_at"):
            from sqlalchemy import select
            from app.db.models.suspend import SuspendLogModel, SuspendActionType

            log_result = await db.execute(
                select(SuspendLogModel)
                .where(
                    SuspendLogModel.card_id == card_id,
                    SuspendLogModel.action == SuspendActionType.suspend,
                    SuspendLogModel.is_deleted == 0
                )
                .order_by(SuspendLogModel.created_at.desc())
                .limit(1)
            )
            latest_suspend_log = log_result.scalar_one_or_none()
            if latest_suspend_log:
                card_dict["suspend_at"] = latest_suspend_log.created_at.isoformat() if latest_suspend_log.created_at else None
                if not card_dict.get("suspend_reason"):
                    card_dict["suspend_reason"] = latest_suspend_log.reason
                if not card_dict.get("suspend_type"):
                    card_dict["suspend_type"] = latest_suspend_log.suspend_type
            elif card_dict.get("updated_at"):
                # 兼容早期 pool_exceed 数据：状态已改但未落停卡时间/日志，退化使用最近更新时间展示
                card_dict["suspend_at"] = card_dict["updated_at"]

        return card_dict

    async def get_card_diagnostics(
        self,
        db: AsyncSession,
        card_id: int,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """获取单卡诊断信息"""
        from app.crud.supplier_crud import supplier_crud

        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)
        card = await iot_card_crud.get_by_id_in_scope(db, card_id, user_ids)
        if not card:
            raise BusinessException(code=404, msg="卡片不存在或无权访问")

        if not card.supplier_id:
            raise BusinessException(code=400, msg="该卡片未绑定供应商，无法诊断")

        supplier = await supplier_crud.get_by_id(db, card.supplier_id)
        if not supplier:
            raise BusinessException(code=404, msg="供应商不存在")

        try:
            client = get_supplier_client(
                supplier_id=card.supplier_id,
                api_url=supplier.api_url or "",
                api_key=supplier.api_key or "",
                api_secret=supplier.api_secret or ""
            )
            result = await client.get_card_diagnostics(card.iccid)
        except Exception as exc:
            raise BusinessException(code=500, msg=f"供应商诊断失败: {exc}") from exc

        return {
            "card_id": card.id,
            "iccid": card.iccid,
            "msisdn": card.msisdn,
            "supplier_id": card.supplier_id,
            "supplier_name": supplier.name,
            **result
        }

    async def restart_card(
        self,
        db: AsyncSession,
        card_id: int,
        current_user_id: int,
        user_level: int
    ) -> dict:
        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)
        card = await iot_card_crud.get_by_id_in_scope(db, card_id, user_ids)
        if not card:
            raise BusinessException(code=404, msg="卡片不存在或无权访问")

        current_card_status = card.status.value if card.status else None
        if current_card_status not in self.RESTART_ALLOWED_STATUSES:
            raise BusinessException(code=400, msg=f"当前卡片状态不支持重启: {current_card_status or '-'}")

        if card.suspend_type in self.RESTART_PROTECTED_SUSPEND_TYPES:
            raise BusinessException(code=400, msg="当前卡片处于业务停卡状态，不支持重启")

        supplier_map = await SuspendActionService._load_supplier_map(db, [card])
        supplier = supplier_map.get(card.supplier_id)
        if not supplier:
            raise BusinessException(code=404, msg="供应商不存在")

        current_supplier_status = await self._get_supplier_lifecycle_status(card, supplier)
        if current_supplier_status not in self.RESTART_ALLOWED_STATUSES:
            raise BusinessException(code=400, msg=f"当前供应商状态不支持重启: {current_supplier_status or current_card_status}")

        suspend_callback_no = None
        if current_supplier_status in self.RESTART_ACTIVE_STATUSES:
            suspend_success, suspend_callback_no, _ = await SuspendActionService._call_supplier_suspend(
                db=db,
                card=card,
                supplier=supplier,
                reason="网页端重启操作-停机",
                operator_id=current_user_id
            )
            if not suspend_success:
                raise BusinessException(code=502, msg="供应商停机请求提交失败")
            if suspend_callback_no:
                await SuspendActionService.mark_refresh_resume_pending(db, suspend_callback_no)

            suspended_status = await self._wait_for_supplier_status(
                db=db,
                card=card,
                supplier=supplier,
                expected_statuses={CardStatus.suspended.value},
                timeout_seconds=settings.refresh_suspend_confirm_timeout_seconds
            )
            if suspended_status != CardStatus.suspended.value:
                return {
                    "card_id": card.id,
                    "iccid": card.iccid,
                    "action": "restart",
                    "status": "processing",
                    "suspend_callback_no": suspend_callback_no,
                    "resume_callback_no": None,
                    "message": "重启请求已提交，停机处理中，请稍后刷新页面查看状态"
                }
        elif current_supplier_status != CardStatus.suspended.value:
            raise BusinessException(code=400, msg=f"当前卡片状态不支持重启: {current_supplier_status or current_card_status}")

        resume_success, resume_callback_no, _ = await SuspendActionService._call_supplier_resume(
            db=db,
            card=card,
            supplier=supplier,
            operator_id=current_user_id
        )
        if not resume_success:
            raise BusinessException(code=502, msg="供应商复机请求提交失败")
        if suspend_callback_no:
            await SuspendActionService.mark_refresh_resume_submitted(
                db=db,
                suspend_callback_no=suspend_callback_no,
                resume_callback_no=resume_callback_no,
                submitted=resume_success
            )

        resumed_status = await self._wait_for_supplier_status(
            db=db,
            card=card,
            supplier=supplier,
            expected_statuses=self.RESTART_ACTIVE_STATUSES,
            timeout_seconds=settings.refresh_resume_confirm_timeout_seconds
        )
        if resumed_status not in self.RESTART_ACTIVE_STATUSES:
            return {
                "card_id": card.id,
                "iccid": card.iccid,
                "action": "restart",
                "status": "processing",
                "suspend_callback_no": suspend_callback_no,
                "resume_callback_no": resume_callback_no,
                "message": "重启请求已提交，复机处理中，请稍后刷新页面查看状态"
            }

        return {
            "card_id": card.id,
            "iccid": card.iccid,
            "action": "restart",
            "status": "success",
            "suspend_callback_no": suspend_callback_no,
            "resume_callback_no": resume_callback_no,
            "message": "重启完成，卡片已恢复激活"
        }

    async def search_cards(
        self,
        db: AsyncSession,
        keyword: str,
        current_user_id: int,
        user_level: int,
        limit: int = 10
    ) -> List[dict]:
        """快速搜索卡片"""
        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)
        items = await iot_card_crud.search(db, keyword, user_ids=user_ids, limit=limit)
        return [item.to_dict() for item in items]

    async def get_stats(
        self,
        db: AsyncSession,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """获取卡片统计"""
        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)
        if user_ids is None:
            return await iot_card_crud.get_stats(db, None)
        return await iot_card_crud.get_stats_in_scope(db, user_ids)

    async def update_remark(
        self,
        db: AsyncSession,
        card_id: int,
        remark: str,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """更新卡片备注"""
        from app.utils.const import sanitize_text
        remark = sanitize_text(remark)
        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)
        card = await iot_card_crud.get_by_id_in_scope(db, card_id, user_ids)
        if not card:
            raise BusinessException(code=404, msg="卡片不存在或无权操作")
        await iot_card_crud.upsert_user_remark(db, card.id, current_user_id, remark)
        await db.commit()
        card_dict = card.to_dict()
        await self._hydrate_card_dicts(db, [card_dict], current_user_id)
        return card_dict

    async def batch_update_remark(
        self,
        db: AsyncSession,
        card_ids: List[int],
        remark: str,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """批量更新备注"""
        if len(card_ids) > settings.max_batch_operation_size:
            raise BusinessException(code=400, msg=f"单次最多操作{settings.max_batch_operation_size}张卡片")

        from app.utils.const import sanitize_text
        remark = sanitize_text(remark)
        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)
        cards = await iot_card_crud.get_by_ids(db, card_ids, user_ids=user_ids)
        for card in cards:
            await iot_card_crud.upsert_user_remark(db, card.id, current_user_id, remark)
        await db.commit()
        count = len(cards)
        return {
            "success": count,
            "total": len(card_ids),
            "failed": len(card_ids) - count
        }

    async def transfer_card(
        self,
        db: AsyncSession,
        card_id: int,
        to_user_id: int,
        current_user_id: int,
        user_level: int,
        remark: Optional[str] = None
    ) -> dict:
        """划拨卡片给子用户"""
        from sqlalchemy import select
        from app.db.models.sys_user import SysUserModel

        # 用户只能划拨自己的卡给子用户
        if user_level == UserLevel.SUB_USER.value:
            raise BusinessException(code=403, msg="子用户无权划拨卡片")

        # 验证目标用户存在
        target_user_result = await db.execute(select(SysUserModel).where(SysUserModel.id == to_user_id))
        target_user = target_user_result.scalar_one_or_none()
        if not target_user:
            raise BusinessException(code=422, msg="目标用户不存在")

        # 验证目标用户状态
        from app.db.models.sys_user import UserStatus
        if target_user.status != UserStatus.enable:
            raise BusinessException(code=422, msg="目标用户已被禁用")

        # 验证目标用户是当前用户的子用户
        if user_level != UserLevel.SUPER_ADMIN.value and target_user.parent_id != current_user_id:
            raise BusinessException(code=422, msg="只能划拨给直属子用户")

        from_user_id = current_user_id
        if user_level == UserLevel.SUPER_ADMIN.value:
            # 超级管理员可以操作任意卡片，需要先获取卡片当前归属
            card = await iot_card_crud.get_by_id(db, card_id, None)
            if not card:
                raise BusinessException(code=404, msg="卡片不存在")
            from_user_id = card.user_id

        card = await iot_card_crud.transfer(
            db=db,
            card_id=card_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            operator_id=current_user_id,
            remark=remark
        )

        if not card:
            raise BusinessException(code=404, msg="卡片不存在或无权操作")

        return card.to_dict()

    async def batch_transfer(
        self,
        db: AsyncSession,
        card_ids: List[int],
        to_user_id: int,
        current_user_id: int,
        user_level: int,
        remark: Optional[str] = None
    ) -> dict:
        """批量划拨"""
        if len(card_ids) > settings.max_batch_operation_size:
            raise BusinessException(code=400, msg=f"单次最多操作{settings.max_batch_operation_size}张卡片")

        from sqlalchemy import select
        from app.db.models.sys_user import SysUserModel

        if user_level == UserLevel.SUB_USER.value:
            raise BusinessException(code=403, msg="子用户无权划拨卡片")

        # 验证目标用户存在
        target_user_result = await db.execute(select(SysUserModel).where(SysUserModel.id == to_user_id))
        target_user = target_user_result.scalar_one_or_none()
        if not target_user:
            raise BusinessException(code=422, msg="目标用户不存在")

        # 验证目标用户状态
        from app.db.models.sys_user import UserStatus
        if target_user.status != UserStatus.enable:
            raise BusinessException(code=422, msg="目标用户已被禁用")

        # 验证目标用户是当前用户的子用户
        if user_level != UserLevel.SUPER_ADMIN.value and target_user.parent_id != current_user_id:
            raise BusinessException(code=422, msg="只能划拨给直属子用户")

        from_user_id = current_user_id

        success, failed = await iot_card_crud.batch_transfer(
            db=db,
            card_ids=card_ids,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            operator_id=current_user_id,
            remark=remark
        )

        return {
            "success": success,
            "failed": failed,
            "total": len(card_ids)
        }

    async def export_cards(
        self,
        db: AsyncSession,
        current_user_id: int,
        user_level: int,
        card_ids: Optional[List[int]] = None,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        carrier: Optional[str] = None,
        period_type: Optional[str] = None,
        is_pool_member: Optional[bool] = None,
        over_usage: Optional[bool] = None,
        remark: Optional[str] = None,
        customer_id: Optional[int] = None,
        batch_id: Optional[str] = None,
        stock_out_start: Optional[str] = None,
        stock_out_end: Optional[str] = None,
        activated_start: Optional[str] = None,
        activated_end: Optional[str] = None,
        expired_start: Optional[str] = None,
        expired_end: Optional[str] = None
    ) -> List[dict]:
        """导出卡片数据"""
        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)

        if card_ids:
            # 导出指定卡片
            items = await iot_card_crud.get_by_ids(db, card_ids, user_ids=user_ids)
        else:
            # 导出全部 (根据筛选条件)
            items, _ = await iot_card_crud.get_list(
                db=db,
                user_ids=user_ids,
                keyword=keyword,
                status=status,
                carrier=carrier,
                period_type=period_type,
                is_pool_member=is_pool_member,
                over_usage=over_usage,
                remark=remark,
                customer_id=customer_id,
                batch_id=batch_id,
                stock_out_start=stock_out_start,
                stock_out_end=stock_out_end,
                activated_start=activated_start,
                activated_end=activated_end,
                expired_start=expired_start,
                expired_end=expired_end,
                page=1,
                page_size=settings.max_export_size,
                remark_user_id=current_user_id
            )

        # 转换为导出格式
        item_dicts = [item.to_dict() for item in items]
        await self._hydrate_card_dicts(db, item_dicts, current_user_id)
        export_data = []
        for d in item_dicts:
            export_data.append({
                "ICCID": d["iccid"],
                "IMSI": d["imsi"] or "",
                "号码": d["msisdn"] or "",
                "材质": d.get("material_name") or "",
                "运营商": d["carrier_name"] or "",
                "套餐规格": d["spec_name"] or "",
                "状态": d["status_name"] or "",
                "已用流量(MB)": d["data_used"],
                "总流量(MB)": d["data_total"],
                "剩余流量(MB)": d["data_remain"],
                "使用率(%)": d["data_usage_percent"],
                "激活日期": d["activated_at"] or "",
                "到期日期": d["expired_at"] or "",
                "备注": d["remark"] or ""
            })

        return export_data

    async def get_card_transfers(
        self,
        db: AsyncSession,
        card_id: int,
        current_user_id: int,
        user_level: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取卡片划拨记录"""
        from sqlalchemy import select, func
        from app.db.models.iot_card import CardTransferModel
        from app.db.models.sys_user import SysUserModel

        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)
        card = await iot_card_crud.get_by_id_in_scope(db, card_id, user_ids)

        # 当前持卡人不在可见范围时，允许原上级用户查看自己发起的划拨记录
        if not card and user_ids is not None:
            transfer_permission_result = await db.execute(
                select(func.count(CardTransferModel.id)).where(
                    CardTransferModel.card_id == card_id,
                    CardTransferModel.from_user_id.in_(user_ids),
                    CardTransferModel.is_deleted == 0
                )
            )
            if (transfer_permission_result.scalar() or 0) == 0:
                raise BusinessException(code=404, msg="卡片不存在或无权访问")
        elif not card:
            existing_card = await iot_card_crud.get_by_id(db, card_id, None)
            if not existing_card:
                raise BusinessException(code=404, msg="卡片不存在或无权访问")

        items, total = await card_transfer_crud.get_list(
            db=db,
            card_id=card_id,
            from_user_ids=user_ids if user_ids is not None else None,
            page=page,
            page_size=page_size
        )

        user_id_set = set()
        for item in items:
            user_id_set.add(item.from_user_id)
            user_id_set.add(item.to_user_id)
            user_id_set.add(item.operator_id)

        user_name_map = {}
        if user_id_set:
            user_result = await db.execute(
                select(SysUserModel.id, SysUserModel.name).where(SysUserModel.id.in_(user_id_set))
            )
            user_name_map = {user_id: name for user_id, name in user_result.all()}

        data = []
        for item in items:
            item_dict = item.to_dict()
            item_dict["from_user_name"] = user_name_map.get(item.from_user_id)
            item_dict["to_user_name"] = user_name_map.get(item.to_user_id)
            item_dict["operator_name"] = user_name_map.get(item.operator_id)
            data.append(item_dict)

        return data, total

    async def query_renew_price(
        self,
        db: AsyncSession,
        iccids: List[str],
        current_user_id: int,
        user_level: int
    ) -> dict:
        """批量查询续费价格"""
        cards = await self._get_cards_by_iccids_in_scope(db, iccids, current_user_id, user_level)

        found_iccids = set()
        found_list = []
        for card in cards:
            found_iccids.add(card.iccid)
            card_dict = card.to_dict()
            # 使用卡片记录的单价，如果为空则查询套餐价格作为兜底
            if card.sale_price:
                card_dict["price_sale"] = float(card.sale_price)
            elif card.sale_package_id:
                from app.db.models.package import SalePackageModel
                pkg_query = select(SalePackageModel.price_sale).where(SalePackageModel.id == card.sale_package_id)
                pkg_result = await db.execute(pkg_query)
                price = pkg_result.scalar_one_or_none()
                card_dict["price_sale"] = float(price) if price else None
            else:
                card_dict["price_sale"] = None
            found_list.append(card_dict)

        await self._hydrate_card_dicts(db, found_list, current_user_id)

        not_found = [iccid for iccid in iccids if iccid not in found_iccids]

        return {
            "found": found_list,
            "not_found": not_found
        }

    async def batch_query_cards(
        self,
        db: AsyncSession,
        iccids: List[str],
        current_user_id: int,
        user_level: int
    ) -> dict:
        """批量查询卡片"""
        found_cards = await self._get_cards_by_iccids_in_scope(db, iccids, current_user_id, user_level)
        
        # 找到的ICCID
        found_iccids = {card.iccid for card in found_cards}
        
        # 未找到的ICCID
        not_found = [iccid for iccid in iccids if iccid not in found_iccids]
        
        found_list = [card.to_dict() for card in found_cards]
        await self._hydrate_card_dicts(db, found_list, current_user_id)

        return {
            "found": found_list,
            "not_found": not_found
        }

    async def batch_transfer_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        to_user_id: int,
        current_user_id: int,
        user_level: int,
        remark: Optional[str] = None
    ) -> dict:
        """通过ICCID批量划拨"""
        from sqlalchemy import select, update
        from app.db.models.sys_user import SysUserModel
        
        if user_level == UserLevel.SUB_USER.value:
            raise BusinessException(code=403, msg="子用户无权划拨卡片")
        
        # 验证目标用户存在
        target_user = await db.execute(select(SysUserModel).where(SysUserModel.id == to_user_id))
        if not target_user.scalar_one_or_none():
            raise BusinessException(code=404, msg="目标用户不存在")
        
        user_filter = None if user_level == UserLevel.SUPER_ADMIN.value else current_user_id
        
        # 查询所有匹配的卡片
        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(iccids),
            IotCardModel.is_deleted == 0
        )
        
        if user_filter is not None:
            query = query.where(IotCardModel.user_id == user_filter)
        
        result = await db.execute(query)
        cards = list(result.scalars().all())
        card_map = {card.iccid: card for card in cards}
        
        success_list = []
        failed_list = []
        renewed_cards = []
        
        for iccid in iccids:
            card = card_map.get(iccid)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                # 更新卡片归属
                old_user_id = card.user_id
                card.user_id = to_user_id
                
                # 记录划拨日志
                from app.db.models.iot_card import CardTransferModel
                transfer_log = CardTransferModel(
                    card_id=card.id,
                    iccid=card.iccid,
                    from_user_id=old_user_id,
                    to_user_id=to_user_id,
                    operator_id=current_user_id,
                    remark=remark
                )
                db.add(transfer_log)
                
                # 获取目标用户名称
                target_user_obj = await db.execute(select(SysUserModel).where(SysUserModel.id == to_user_id))
                target_user_name = target_user_obj.scalar_one().name
                
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "to_user_name": target_user_name,
                    "message": "划拨成功"
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_remark_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        remark: str,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量备注"""
        cards = await self._get_cards_by_iccids_in_scope(db, iccids, current_user_id, user_level)
        card_map = {card.iccid: card for card in cards}
        success_list = []
        failed_list = []

        for iccid in iccids:
            card = card_map.get(iccid)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue

            try:
                await iot_card_crud.upsert_user_remark(db, card.id, current_user_id, remark)
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "remark": remark
                })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()

        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_renew_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        renew_months: int,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量续费"""
        from app.crud.package_crud import sale_package_crud
        from app.utils.date_utils import calculate_expiry_date

        cards = await self._get_cards_by_iccids_in_scope(
            db,
            iccids,
            current_user_id,
            user_level
        )
        card_map = {card.iccid: card for card in cards}

        success_list = []
        failed_list = []
        renewed_cards = []
        renewed_expiry_map = {}
        warning_list = []

        for iccid in iccids:
            card = card_map.get(iccid)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue
            
            try:
                old_expired_at = card.expired_at

                # 续费逻辑：延长到期日期
                package = await sale_package_crud.get_by_id(db, card.sale_package_id) if card.sale_package_id else None
                if package:
                    base_date = await self._resolve_renew_base_date(db, card)
                    period_type, period_months, period_days = self._resolve_renew_period(card, package, renew_months)
                    card.expired_at = calculate_expiry_date(
                        base_date + timedelta(days=1),
                        period_type,
                        period_months,
                        period_days,
                        card.carrier.value if card.carrier else None
                    )
                    self._apply_yearly_renew_flow(card, package, renew_months)
                else:
                    # 兼容旧逻辑：无套餐信息时按30天/月计算
                    if card.expired_at:
                        card.expired_at = card.expired_at + timedelta(days=renew_months * 30)
                    else:
                        card.expired_at = date.today() + timedelta(days=renew_months * 30)
                
                success_list.append({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn,
                    "old_expired_at": old_expired_at.isoformat() if old_expired_at else None,
                    "new_expired_at": card.expired_at.isoformat() if card.expired_at else None,
                    "message": f"续费{renew_months}个月成功"
                })
                renewed_cards.append(card)
                renewed_expiry_map[card.iccid] = {
                    "old": old_expired_at.isoformat() if old_expired_at else None,
                    "new": card.expired_at.isoformat() if card.expired_at else None,
                }
                warning = self._build_supplier_renew_warning(card)
                if warning:
                    success_list[-1]["warning"] = warning
                    warning_list.append({
                        "iccid": card.iccid,
                        "warning": warning,
                    })
            except Exception as e:
                failed_list.append({"iccid": iccid, "error": str(e)})
        
        await db.commit()

        for card in renewed_cards:
            await SysOperationLogCRUD.create(
                db=db,
                module="cards",
                action="renew",
                user_id=current_user_id,
                target_type="card",
                target_id=card.id,
                target_name=card.iccid,
                detail=(
                    f"批量续费 {renew_months} 个月，原到期 {renewed_expiry_map.get(card.iccid, {}).get('old') or '-'}，"
                    f"新到期 {renewed_expiry_map.get(card.iccid, {}).get('new') or '-'}"
                )
            )
        
        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list,
            "warning_count": len(warning_list),
            "warning_list": warning_list,
        }

    async def batch_suspend_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        reason: Optional[str],
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量停机"""
        cards = await self._get_cards_by_iccids_in_scope(db, iccids, current_user_id, user_level)
        card_map = {card.iccid: card for card in cards}
        found_card_ids = [card_map[iccid].id for iccid in iccids if iccid in card_map]

        result = await SuspendActionService.manual_suspend(
            db=db,
            data=ManualSuspend(card_ids=found_card_ids, reason=reason),
            operator_id=current_user_id,
            user_id=current_user_id,
            user_ids=await self._get_accessible_user_ids(db, current_user_id, user_level),
            is_admin=user_level == UserLevel.SUPER_ADMIN.value
        )

        success_list = []
        failed_list = [{"iccid": iccid, "error": "卡片不存在或无权操作"} for iccid in iccids if iccid not in card_map]

        for iccid in result.success_cards:
            card = card_map.get(iccid)
            success_list.append({
                "iccid": iccid,
                "msisdn": card.msisdn if card else None,
                "message": "停机成功"
            })

        for item in result.fail_cards:
            failed_list.append({
                "iccid": item.get("iccid", "未知"),
                "error": item.get("reason", "停机失败")
            })

        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_resume_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        current_user_id: int,
        user_level: int
    ) -> dict:
        """通过ICCID批量复机"""
        cards = await self._get_cards_by_iccids_in_scope(db, iccids, current_user_id, user_level)
        card_map = {card.iccid: card for card in cards}
        found_card_ids = [card_map[iccid].id for iccid in iccids if iccid in card_map]

        result = await SuspendActionService.manual_resume(
            db=db,
            data=ManualResume(card_ids=found_card_ids),
            operator_id=current_user_id,
            user_id=current_user_id,
            user_ids=await self._get_accessible_user_ids(db, current_user_id, user_level),
            is_admin=user_level == UserLevel.SUPER_ADMIN.value
        )

        success_list = []
        failed_list = [{"iccid": iccid, "error": "卡片不存在或无权操作"} for iccid in iccids if iccid not in card_map]

        for iccid in result.success_cards:
            card = card_map.get(iccid)
            success_list.append({
                "iccid": iccid,
                "msisdn": card.msisdn if card else None,
                "message": "复机成功"
            })

        for item in result.fail_cards:
            failed_list.append({
                "iccid": item.get("iccid", "未知"),
                "error": item.get("reason", "复机失败")
            })

        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }

    async def batch_add_flow_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        added_flow_mb: int,
        current_user_id: int,
        user_level: int,
        remark: Optional[str] = None
    ) -> dict:
        """通过ICCID批量给非流量池卡补量"""
        if user_level == UserLevel.SUB_USER.value:
            raise BusinessException(code=403, msg="子用户无权补量")

        cards = await self._get_cards_by_iccids_in_scope(db, iccids, current_user_id, user_level)
        card_map = {card.iccid: card for card in cards}
        direct_child_ids = await self._get_direct_child_user_ids(db, current_user_id, user_level)

        success_list = []
        failed_list = []
        adjusted_cards = []

        for iccid in iccids:
            card = card_map.get(iccid)
            if not card:
                failed_list.append({"iccid": iccid, "error": "卡片不存在或无权操作"})
                continue

            if card.user_id is None:
                failed_list.append({"iccid": iccid, "error": "卡片尚未分配给客户"})
                continue

            if direct_child_ids is not None and card.user_id not in direct_child_ids:
                failed_list.append({"iccid": iccid, "error": "只能给直属下级用户卡片补量"})
                continue

            if card.is_pool_member == 1:
                failed_list.append({"iccid": iccid, "error": "流量池卡请在流量池维度补量"})
                continue

            self._apply_card_addon_flow(card, added_flow_mb)
            adjusted_cards.append(card)
            success_list.append({
                "iccid": card.iccid,
                "msisdn": card.msisdn,
                "message": f"增加{added_flow_mb}MB成功（仅当月有效）"
            })

        await db.commit()

        auto_resume_result = await SuspendActionService.auto_resume_cards_after_flow_adjustment(
            db=db,
            cards=adjusted_cards,
            operator_id=current_user_id,
            reason="单卡补量后自动复机"
        )

        for card in adjusted_cards:
            await SysOperationLogCRUD.create(
                db=db,
                module="cards",
                action="add_flow",
                user_id=current_user_id,
                target_type="card",
                target_id=card.id,
                target_name=card.iccid,
                detail=f"单卡补量 {added_flow_mb}MB。备注：{remark or ''}"
            )

        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list,
            "auto_resumed": auto_resume_result["resumed_count"]
        }

    async def quote_card_topup(
        self,
        db: AsyncSession,
        card_id: int,
        current_user_id: int
    ) -> dict:
        card_result = await db.execute(
            select(IotCardModel).where(
                IotCardModel.id == card_id,
                IotCardModel.user_id == current_user_id,
                IotCardModel.is_deleted == 0
            )
        )
        card = card_result.scalar_one_or_none()
        if not card:
            raise BusinessException(code=404, msg="卡片不存在或无权访问")
        if card.is_pool_member == 1:
            raise BusinessException(code=400, msg="流量池卡请购买流量池加油包")
        package_options = []
        for package_mb, label in FLOW_PACKAGE_LABELS.items():
            price = self._normalize_price(Decimal(str(FLOW_PACKAGE_PRICES[package_mb])))
            package_options.append({
                "label": label,
                "package_mb": package_mb,
                "price": float(price)
            })

        balance_info = await account_balance_service.get_balance_info(db, current_user_id)
        return {
            "card_id": card.id,
            "iccid": card.iccid,
            "flow_size": card.flow_size,
            "package_options": package_options,
            "balance": balance_info["balance"]
        }

    async def purchase_card_topup(
        self,
        db: AsyncSession,
        card_id: int,
        package_mb: int,
        current_user_id: int,
        remark: Optional[str] = None
    ) -> dict:
        card_result = await db.execute(
            select(IotCardModel).where(
                IotCardModel.id == card_id,
                IotCardModel.user_id == current_user_id,
                IotCardModel.is_deleted == 0
            )
        )
        card = card_result.scalar_one_or_none()
        if not card:
            raise BusinessException(code=404, msg="卡片不存在或无权访问")
        if card.is_pool_member == 1:
            raise BusinessException(code=400, msg="流量池卡请购买流量池加油包")
        if package_mb not in FLOW_PACKAGE_PRICES:
            raise BusinessException(code=400, msg="不支持的加油包规格")
        total_price = self._normalize_price(Decimal(str(FLOW_PACKAGE_PRICES[package_mb])))

        balance_result = await account_balance_service.consume_balance(
            db=db,
            user_id=current_user_id,
            amount=total_price,
            detail=f"单卡加油包购买 {FLOW_PACKAGE_LABELS.get(package_mb, f'{package_mb}MB')}",
            target_type="card",
            target_id=card.id,
            target_name=card.iccid
        )

        self._apply_card_addon_flow(card, package_mb)
        await db.flush()

        auto_resume_result = await SuspendActionService.auto_resume_cards_after_flow_adjustment(
            db=db,
            cards=[card],
            operator_id=current_user_id,
            reason="购买单卡加油包后自动复机"
        )

        await SysOperationLogCRUD.create(
            db=db,
            module="orders",
            action="card_topup_purchase",
            user_id=current_user_id,
            target_type="card",
            target_id=card.id,
            target_name=card.iccid,
            detail=(
                f"购买单卡加油包 {FLOW_PACKAGE_LABELS.get(package_mb, f'{package_mb}MB')}，"
                f"扣减余额 {total_price} 元，自动复机 {auto_resume_result['resumed_count']} 张。"
                f"备注：{remark or ''}"
            )
        )

        return {
            "card_id": card.id,
            "iccid": card.iccid,
            "package_mb": package_mb,
            "package_label": FLOW_PACKAGE_LABELS.get(package_mb, f"{package_mb}MB"),
            "price": float(total_price),
            "balance": balance_result["after_balance"],
            "auto_resumed": auto_resume_result["resumed_count"]
        }

    async def quote_card_renew(
        self,
        db: AsyncSession,
        card_id: int,
        renew_months: int,
        current_user_id: int
    ) -> dict:
        card_result = await db.execute(
            select(IotCardModel).where(
                IotCardModel.id == card_id,
                IotCardModel.user_id == current_user_id,
                IotCardModel.is_deleted == 0
            )
        )
        card = card_result.scalar_one_or_none()
        if not card:
            raise BusinessException(code=404, msg="卡片不存在或无权访问")
        sale_price = await self._resolve_card_sale_price(db, card)
        if not sale_price:
            raise BusinessException(code=400, msg="卡片缺少销售价格，暂不可续费")

        total_price = self._normalize_price(sale_price * Decimal(str(renew_months)))
        balance_info = await account_balance_service.get_balance_info(db, current_user_id)
        return {
            "card_id": card.id,
            "iccid": card.iccid,
            "renew_months": renew_months,
            "unit_price": float(sale_price),
            "total_price": float(total_price),
            "balance": balance_info["balance"],
            "expired_at": card.expired_at.isoformat() if card.expired_at else None
        }

    async def purchase_card_renew(
        self,
        db: AsyncSession,
        card_id: int,
        renew_months: int,
        current_user_id: int,
        remark: Optional[str] = None
    ) -> dict:
        from datetime import timedelta
        from app.crud.package_crud import sale_package_crud
        from app.utils.date_utils import calculate_expiry_date

        card_result = await db.execute(
            select(IotCardModel).where(
                IotCardModel.id == card_id,
                IotCardModel.user_id == current_user_id,
                IotCardModel.is_deleted == 0
            )
        )
        card = card_result.scalar_one_or_none()
        if not card:
            raise BusinessException(code=404, msg="卡片不存在或无权访问")
        sale_price = await self._resolve_card_sale_price(db, card)
        if not sale_price:
            raise BusinessException(code=400, msg="卡片缺少销售价格，暂不可续费")

        total_price = self._normalize_price(sale_price * Decimal(str(renew_months)))
        balance_result = await account_balance_service.consume_balance(
            db=db,
            user_id=current_user_id,
            amount=total_price,
            detail=f"单卡续费 {renew_months} 个月",
            target_type="card",
            target_id=card.id,
            target_name=card.iccid
        )

        package = await sale_package_crud.get_by_id(db, card.sale_package_id) if card.sale_package_id else None
        if package:
            base_date = await self._resolve_renew_base_date(db, card)
            period_type, period_months, period_days = self._resolve_renew_period(card, package, renew_months)
            card.expired_at = calculate_expiry_date(
                base_date + timedelta(days=1),
                period_type,
                period_months,
                period_days,
                card.carrier.value if card.carrier else None
            )
            self._apply_yearly_renew_flow(card, package, renew_months)
        else:
            if card.expired_at:
                card.expired_at = card.expired_at + timedelta(days=renew_months * 30)
            else:
                card.expired_at = date.today() + timedelta(days=renew_months * 30)

        await db.flush()

        auto_resume_result = await SuspendActionService.auto_resume_cards_after_flow_adjustment(
            db=db,
            cards=[card],
            operator_id=current_user_id,
            reason="购买续费后自动复机"
        )

        await SysOperationLogCRUD.create(
            db=db,
            module="orders",
            action="card_renew_purchase",
            user_id=current_user_id,
            target_type="card",
            target_id=card.id,
            target_name=card.iccid,
            detail=(
                f"购买单卡续费 {renew_months} 个月，扣减余额 {total_price} 元，"
                f"自动复机 {auto_resume_result['resumed_count']} 张。备注：{remark or ''}"
            )
        )

        warning_message = self._build_supplier_renew_warning(card)

        return {
            "card_id": card.id,
            "iccid": card.iccid,
            "renew_months": renew_months,
            "price": float(total_price),
            "balance": balance_result["after_balance"],
            "expired_at": card.expired_at.isoformat() if card.expired_at else None,
            "auto_resumed": auto_resume_result["resumed_count"],
            "warning_message": warning_message,
            "supplier_sync_status": "local_only" if warning_message else "not_applicable",
        }

    async def batch_force_resume_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        current_user_id: int
    ) -> dict:
        """通过ICCID批量强制复机，仅超级管理员使用"""
        cards = await self._get_cards_by_iccids_in_scope(
            db=db,
            iccids=iccids,
            current_user_id=current_user_id,
            user_level=UserLevel.SUPER_ADMIN.value
        )
        card_map = {card.iccid: card for card in cards}
        found_card_ids = [card_map[iccid].id for iccid in iccids if iccid in card_map]

        result = await SuspendActionService.manual_resume(
            db=db,
            data=ManualResume(card_ids=found_card_ids),
            operator_id=current_user_id,
            user_id=current_user_id,
            is_admin=True,
            force=True
        )

        success_list = []
        failed_list = [{"iccid": iccid, "error": "卡片不存在"} for iccid in iccids if iccid not in card_map]

        for iccid in result.success_cards:
            card = card_map.get(iccid)
            success_list.append({
                "iccid": iccid,
                "msisdn": card.msisdn if card else None,
                "message": "强制复机成功"
            })

        for item in result.fail_cards:
            failed_list.append({
                "iccid": item.get("iccid", "未知"),
                "error": item.get("reason", "强制复机失败")
            })

        return {
            "success": len(success_list),
            "failed": len(failed_list),
            "success_list": success_list,
            "failed_list": failed_list
        }


    async def get_card_usage_history(
        self,
        db: AsyncSession,
        card_id: int,
        current_user_id: int,
        user_level: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """获取卡片用量历史"""
        from app.crud.iot_card_crud import card_usage_history_crud
        from datetime import datetime

        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)
        card = await iot_card_crud.get_by_id_in_scope(db, card_id, user_ids)
        if not card:
            raise BusinessException(code=404, msg="卡片不存在或无权访问")

        start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

        history = await card_usage_history_crud.get_card_history(db, card_id, start, end)
        history_items = [h.to_dict() for h in history]
        daily_items = [item for item in history_items if item.get("snapshot_type") == "daily"]
        if daily_items:
            history_items = daily_items
        history_items.sort(key=lambda item: item.get("snapshot_date") or "")

        if not history_items and card.data_sync_at:
            history_items = [{
                "id": 0,
                "card_id": card.id,
                "iccid": card.iccid,
                "data_used": card.data_used,
                "daily_used": card.data_used,
                "data_total": card.data_total,
                "period_type": card.period_type.value if card.period_type else "",
                "snapshot_date": card.data_sync_at.date().isoformat(),
                "snapshot_type": "current",
                "snapshot_month": None,
                "created_at": card.data_sync_at.isoformat()
            }]
        else:
            previous_used = None
            for item in history_items:
                current_used = item.get("data_used") or 0
                if previous_used is None:
                    daily_used = current_used
                else:
                    daily_used = max(current_used - previous_used, 0)
                item["daily_used"] = daily_used
                previous_used = current_used

        return history_items

    async def export_cards_with_history(
        self,
        db: AsyncSession,
        current_user_id: int,
        user_level: int,
        card_ids: Optional[List[int]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        carrier: Optional[str] = None,
        period_type: Optional[str] = None,
        is_pool_member: Optional[bool] = None,
        over_usage: Optional[bool] = None,
        remark: Optional[str] = None,
        customer_id: Optional[int] = None,
        batch_id: Optional[str] = None,
        stock_out_start: Optional[str] = None,
        stock_out_end: Optional[str] = None,
        activated_start: Optional[str] = None,
        activated_end: Optional[str] = None,
        expired_start: Optional[str] = None,
        expired_end: Optional[str] = None
    ):
        """导出卡片历史用量"""
        from app.crud.iot_card_crud import card_usage_history_crud
        from datetime import datetime

        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)
        if card_ids:
            cards = await iot_card_crud.get_by_ids(db, card_ids, user_ids=user_ids)
        else:
            cards, _ = await iot_card_crud.get_list(
                db=db,
                user_ids=user_ids,
                keyword=keyword,
                status=status,
                carrier=carrier,
                period_type=period_type,
                is_pool_member=is_pool_member,
                over_usage=over_usage,
                remark=remark,
                customer_id=customer_id,
                batch_id=batch_id,
                stock_out_start=stock_out_start,
                stock_out_end=stock_out_end,
                activated_start=activated_start,
                activated_end=activated_end,
                expired_start=expired_start,
                expired_end=expired_end,
                page=1,
                page_size=100000
            )
        if not cards:
            return []

        start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

        card_ids_list = [c.id for c in cards]
        history_records = await card_usage_history_crud.get_cards_history(db, card_ids_list, start, end)

        history_map = {}
        for h in history_records:
            if h.card_id not in history_map:
                history_map[h.card_id] = []
            history_map[h.card_id].append(h)

        month_labels: List[str] = []
        if start and end:
            cursor_year = start.year
            cursor_month = start.month
            while (cursor_year, cursor_month) <= (end.year, end.month):
                month_labels.append(f"{cursor_year:04d}-{cursor_month:02d}")
                if cursor_month == 12:
                    cursor_year += 1
                    cursor_month = 1
                else:
                    cursor_month += 1
        else:
            month_labels = sorted({
                (h.snapshot_month or h.snapshot_date.strftime("%Y-%m"))
                for h in history_records
            })

        export_data = []
        for card in cards:
            d = card.to_dict()
            histories = history_map.get(card.id, [])
            month_history_map = {}
            for h in histories:
                month_key = h.snapshot_month or h.snapshot_date.strftime("%Y-%m")
                existing = month_history_map.get(month_key)
                if existing is None or h.snapshot_date > existing.snapshot_date:
                    month_history_map[month_key] = h

            row = {
                "ICCID": d["iccid"],
                "号码": d["msisdn"] or "",
                "IMSI": d["imsi"] or "",
                "运营商": d["carrier_name"],
                "套餐规格": d["spec_name"],
                "状态": d["status_name"],
                "总流量(GB)": round((d["data_total"] or 0) / 1024, 2),
            }

            for month_label in month_labels:
                record = month_history_map.get(month_label)
                row[f"{month_label}用量(GB)"] = round((record.data_used or 0) / 1024, 2) if record else ""

            export_data.append(row)

        return export_data



iot_card_service = IotCardService()
