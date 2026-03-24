"""
流量池管理服务层
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.crud.pool_crud import pool_crud, pool_card_crud, pool_log_crud
from app.db.models.pool import TrafficPoolModel
from app.db.models.iot_card import IotCardModel, CardStatus, SuspendType
from app.db.models.sys_user import UserLevel
from app.crud.sys_user_crud_enhanced import SysUserCRUDEnhanced
from app.crud.system_crud import SysOperationLogCRUD
from app.services.suspend_service import SuspendActionService
from app.services.account_balance_service import account_balance_service
from app.flow_packages import get_current_flow_cycle_month, is_flow_cycle_active
from app.utils.exceptions import BusinessException


class PoolService:
    """流量池服务"""

    @staticmethod
    def _normalize_price(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _get_effective_pool_addon_flow(pool: TrafficPoolModel) -> int:
        if pool.addon_flow and not pool.addon_flow_month:
            return int(pool.addon_flow or 0)
        if is_flow_cycle_active(pool.addon_flow_month):
            return int(pool.addon_flow or 0)
        return 0

    def _apply_pool_addon_flow(self, pool: TrafficPoolModel, added_flow_mb: int) -> None:
        effective_addon = self._get_effective_pool_addon_flow(pool)
        if not effective_addon and pool.addon_flow:
            pool.addon_flow = 0
            pool.addon_flow_month = None
        pool.addon_flow = effective_addon + added_flow_mb
        pool.addon_flow_month = get_current_flow_cycle_month()

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

    async def _get_pool_in_scope(
        self,
        db: AsyncSession,
        pool_id: int,
        current_user_id: int,
        user_level: int
    ) -> TrafficPoolModel:
        """获取当前用户可见范围内的流量池"""
        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)
        pool = await pool_crud.get_by_id_in_scope(db, pool_id, user_ids)
        if not pool:
            raise BusinessException(code=404, msg="流量池不存在或无权访问")
        return pool

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

        sys_user_crud = SysUserCRUDEnhanced()
        return await sys_user_crud.get_children_ids(db, current_user_id, max_depth=1)

    async def create_pool(
        self,
        db: AsyncSession,
        name: str,
        carrier: str,
        flow_size: int,
        period_type: str,
        user_id: Optional[int] = None,
        sale_package_id: Optional[int] = None,
        alert_threshold_1: Optional[int] = None,
        alert_threshold_2: Optional[int] = None,
        alert_threshold_3: Optional[int] = None,
        created_by: Optional[int] = None,
        remark: Optional[str] = None
    ) -> dict:
        """创建流量池"""
        pool = await pool_crud.create(
            db=db,
            name=name,
            carrier=carrier,
            flow_size=flow_size,
            period_type=period_type,
            user_id=user_id,
            sale_package_id=sale_package_id,
            alert_threshold_1=alert_threshold_1,
            alert_threshold_2=alert_threshold_2,
            alert_threshold_3=alert_threshold_3,
            created_by=created_by,
            remark=remark
        )
        return pool.to_dict()

    async def get_pool(
        self,
        db: AsyncSession,
        pool_id: int,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """获取流量池详情"""
        await self._get_pool_in_scope(db, pool_id, current_user_id, user_level)
        pool = await pool_crud.update_stats(db, pool_id)
        if not pool:
            raise BusinessException(code=404, msg="流量池不存在或无权访问")
        pool_dict = pool.to_dict()
        await self._enrich_pool_dict(db, pool, pool_dict)
        pool_dict["can_self_topup"] = pool.user_id == current_user_id
        return pool_dict

    async def get_pools(
        self,
        db: AsyncSession,
        current_user_id: int,
        user_level: int,
        name: Optional[str] = None,
        carrier: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取流量池列表"""
        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)
        items, total = await pool_crud.get_list(
            db=db,
            user_ids=user_ids,
            name=name,
            carrier=carrier,
            status=status,
            page=page,
            page_size=page_size
        )

        # 批量查询所有流量池的卡片统计（避免N+1）
        from sqlalchemy import func
        pool_ids = [p.id for p in items]
        if pool_ids:
            stmt = select(
                IotCardModel.pool_id,
                IotCardModel.status,
                func.count(IotCardModel.id).label('count')
            ).where(
                IotCardModel.pool_id.in_(pool_ids),
                IotCardModel.is_deleted == 0
            ).group_by(IotCardModel.pool_id, IotCardModel.status)

            card_stats_result = await db.execute(stmt)
            # 构建统计字典 {pool_id: {status: count}}
            pool_stats_map = {}
            for row in card_stats_result.fetchall():
                pool_id = row[0]
                status_value = row[1].value if hasattr(row[1], 'value') else row[1]
                count = row[2]
                if pool_id not in pool_stats_map:
                    pool_stats_map[pool_id] = {"activated": 0, "suspended": 0, "stock": 0, "testing": 0, "cancelled": 0, "silent": 0, "expired": 0}
                if status_value in pool_stats_map[pool_id]:
                    pool_stats_map[pool_id][status_value] = count
        else:
            pool_stats_map = {}

        # 为每个流量池添加卡片统计信息
        result = []
        for pool in items:
            card_stats = pool_stats_map.get(pool.id, {"activated": 0, "suspended": 0, "stock": 0, "testing": 0, "cancelled": 0, "silent": 0, "expired": 0})

            # 转换为字典并添加卡片统计
            pool_dict = pool.to_dict(include_card_stats=True, card_stats=card_stats)
            # 添加关联信息
            await self._enrich_pool_dict(db, pool, pool_dict)
            pool_dict["can_self_topup"] = pool.user_id == current_user_id
            result.append(pool_dict)

        return result, total

    async def _enrich_pool_dict(self, db: AsyncSession, pool: TrafficPoolModel, pool_dict: dict) -> None:
        """为流量池字典添加 user_name 和 sale_package_name"""
        from app.db.models.sys_user import SysUserModel
        from app.db.models.package import SalePackageModel

        # 获取 user_name
        if pool.user_id:
            user_stmt = select(SysUserModel.name).where(
                SysUserModel.id == pool.user_id,
                SysUserModel.is_deleted == 0
            )
            user_r = await db.execute(user_stmt)
            pool_dict["user_name"] = user_r.scalar_one_or_none()
        else:
            pool_dict["user_name"] = None

        # 获取 sale_package_name
        if pool.sale_package_id:
            pkg_stmt = select(SalePackageModel.name).where(
                SalePackageModel.id == pool.sale_package_id,
                SalePackageModel.is_deleted == 0
            )
            pkg_r = await db.execute(pkg_stmt)
            pool_dict["sale_package_name"] = pkg_r.scalar_one_or_none()
        else:
            pool_dict["sale_package_name"] = None

        if not pool_dict.get("last_sync_at"):
            last_sync_stmt = select(func.max(IotCardModel.data_sync_at)).where(
                IotCardModel.pool_id == pool.id,
                IotCardModel.is_deleted == 0
            )
            last_sync_result = await db.execute(last_sync_stmt)
            last_sync_at = last_sync_result.scalar_one_or_none()
            pool_dict["last_sync_at"] = last_sync_at.isoformat() if last_sync_at else None

    async def update_pool(
        self,
        db: AsyncSession,
        pool_id: int,
        current_user_id: int,
        user_level: int,
        **kwargs
    ) -> dict:
        """更新流量池"""
        pool = await self._get_pool_in_scope(db, pool_id, current_user_id, user_level)
        pool = await pool_crud.update(db, pool.id, **kwargs)
        return pool.to_dict()

    async def delete_pool(
        self,
        db: AsyncSession,
        pool_id: int,
        current_user_id: int,
        user_level: int
    ) -> bool:
        """删除流量池"""
        # 检查池内是否还有卡片
        pool = await self._get_pool_in_scope(db, pool_id, current_user_id, user_level)

        if pool.card_count > 0:
            raise BusinessException(code=400, msg=f"流量池内还有 {pool.card_count} 张卡片，请先移除")

        success = await pool_crud.delete(db, pool_id)
        return success

    async def add_cards(
        self,
        db: AsyncSession,
        pool_id: int,
        card_ids: List[int],
        current_user_id: int,
        user_level: int,
        operator_id: int,
        remark: Optional[str] = None
    ) -> dict:
        """添加卡片到流量池"""
        MAX_BATCH_SIZE = 10000
        if len(card_ids) > MAX_BATCH_SIZE:
            raise BusinessException(code=400, msg=f"单次最多操作{MAX_BATCH_SIZE}张卡片")

        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)
        pool = await self._get_pool_in_scope(db, pool_id, current_user_id, user_level)

        if pool.status.value != "enable":
            raise BusinessException(code=400, msg="流量池已停用")

        success, failed, fail_details = await pool_card_crud.add_cards(
            db=db,
            pool=pool,
            card_ids=card_ids,
            operator_id=operator_id,
            user_ids=user_ids,
            remark=remark
        )

        return {
            "total": len(card_ids),
            "success": success,
            "failed": failed,
            "fail_details": fail_details if fail_details else None
        }

    async def remove_cards(
        self,
        db: AsyncSession,
        pool_id: int,
        card_ids: List[int],
        current_user_id: int,
        user_level: int,
        operator_id: int,
        remark: Optional[str] = None
    ) -> dict:
        """从流量池移除卡片"""
        MAX_BATCH_SIZE = 10000
        if len(card_ids) > MAX_BATCH_SIZE:
            raise BusinessException(code=400, msg=f"单次最多操作{MAX_BATCH_SIZE}张卡片")

        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)
        pool = await self._get_pool_in_scope(db, pool_id, current_user_id, user_level)

        success, failed, fail_details = await pool_card_crud.remove_cards(
            db=db,
            pool=pool,
            card_ids=card_ids,
            operator_id=operator_id,
            user_ids=user_ids,
            remark=remark
        )

        return {
            "total": len(card_ids),
            "success": success,
            "failed": failed,
            "fail_details": fail_details if fail_details else None
        }

    async def get_pool_cards(
        self,
        db: AsyncSession,
        pool_id: int,
        current_user_id: int,
        user_level: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取流量池内卡片列表"""
        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)
        await self._get_pool_in_scope(db, pool_id, current_user_id, user_level)

        items, total = await pool_card_crud.get_pool_cards(
            db=db, pool_id=pool_id, user_ids=user_ids, page=page, page_size=page_size
        )
        return [item.to_dict() for item in items], total

    async def get_pool_stats(
        self,
        db: AsyncSession,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """获取流量池总体统计"""
        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)
        stats = await pool_crud.get_stats(db, user_ids=user_ids)
        return stats

    async def get_pool_usage(
        self,
        db: AsyncSession,
        pool_id: int,
        current_user_id: int,
        user_level: int
    ) -> dict:
        """获取流量池用量统计"""
        user_ids = await self._get_accessible_user_ids(db, current_user_id, user_level)
        pool = await self._get_pool_in_scope(db, pool_id, current_user_id, user_level)

        # 先更新统计数据
        pool = await pool_crud.update_stats(db, pool_id)

        # 获取池内卡片用量明细
        cards, _ = await pool_card_crud.get_pool_cards(
            db, pool_id, user_ids=user_ids, page=1, page_size=1000
        )
        card_usage = []
        for card in cards:
            card_usage.append({
                "card_id": card.id,
                "iccid": card.iccid,
                "data_used": card.data_used,
                "data_total": card.data_total,
                "usage_percent": card.get_data_usage_percent()
            })

        return {
            "pool_id": pool.id,
            "pool_name": pool.name,
            "spec_name": pool.get_spec_name(),
            "card_count": pool.card_count,
            "data_total": pool.data_total,
            "data_used": pool.data_used,
            "data_remain": pool.get_data_remain(),
            "usage_percent": pool.get_usage_percent(),
            "alert_threshold_1": pool.alert_threshold_1,
            "alert_threshold_2": pool.alert_threshold_2,
            "alert_threshold_3": pool.alert_threshold_3,
            "is_alert": pool.is_alert(),
            "is_exceed": pool.is_exceed(),
            "cards": card_usage
        }

    async def get_pool_logs(
        self,
        db: AsyncSession,
        pool_id: int,
        current_user_id: int,
        user_level: int,
        action: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取流量池操作日志"""
        await self._get_pool_in_scope(db, pool_id, current_user_id, user_level)

        items, total = await pool_log_crud.get_logs(
            db=db, pool_id=pool_id, action=action, page=page, page_size=page_size
        )
        return [item.to_dict() for item in items], total

    async def recharge_pool(
        self,
        db: AsyncSession,
        pool_id: int,
        added_flow_mb: int,
        current_user_id: int,
        user_level: int,
        remark: Optional[str] = None
    ) -> dict:
        """后台给流量池补量，并自动重检池超限停卡"""
        if user_level == UserLevel.SUB_USER.value:
            raise BusinessException(code=403, msg="子用户无权给流量池补量")

        pool = await self._get_pool_in_scope(db, pool_id, current_user_id, user_level)
        direct_child_ids = await self._get_direct_child_user_ids(db, current_user_id, user_level)

        if direct_child_ids is not None and pool.user_id not in direct_child_ids:
            raise BusinessException(code=403, msg="只能给直属下级用户的流量池补量")

        self._apply_pool_addon_flow(pool, added_flow_mb)
        await db.commit()
        pool = await pool_crud.update_stats(db, pool.id)

        suspended_cards_result = await db.execute(
            select(IotCardModel).where(
                IotCardModel.pool_id == pool.id,
                IotCardModel.status == CardStatus.suspended,
                IotCardModel.suspend_type == SuspendType.pool_exceed,
                IotCardModel.is_deleted == 0
            )
        )
        suspended_cards = list(suspended_cards_result.scalars().all())
        auto_resume_result = await SuspendActionService.auto_resume_cards_after_flow_adjustment(
            db=db,
            cards=suspended_cards,
            operator_id=current_user_id,
            reason="流量池补量后自动复机"
        )

        await SysOperationLogCRUD.create(
            db=db,
            module="pools",
            action="add_flow",
            user_id=current_user_id,
            target_type="pool",
            target_id=pool.id,
            target_name=pool.name,
            detail=f"流量池补量 {added_flow_mb}MB，自动复机{auto_resume_result['resumed_count']}张。备注：{remark or ''}"
        )

        pool_dict = pool.to_dict()
        await self._enrich_pool_dict(db, pool, pool_dict)
        pool_dict["auto_resumed"] = auto_resume_result["resumed_count"]
        pool_dict["can_self_topup"] = pool.user_id == current_user_id
        return pool_dict

    async def quote_pool_topup(
        self,
        db: AsyncSession,
        pool_id: int,
        current_user_id: int
    ) -> dict:
        pool = await self._get_pool_in_scope(db, pool_id, current_user_id, user_level=3)
        if pool.user_id != current_user_id:
            raise BusinessException(code=403, msg="只能购买自己名下流量池的加油包")

        avg_price_result = await db.execute(
            select(func.avg(IotCardModel.sale_price)).where(
                IotCardModel.pool_id == pool.id,
                IotCardModel.is_deleted == 0,
                IotCardModel.sale_price.is_not(None)
            )
        )
        avg_sale_price = avg_price_result.scalar_one_or_none()
        if avg_sale_price is None:
            raise BusinessException(code=400, msg="流量池缺少销售价格数据，暂不可购买加油包")

        unit_price = self._normalize_price(Decimal(str(avg_sale_price)) * Decimal("3"))
        balance_info = await account_balance_service.get_balance_info(db, current_user_id)
        return {
            "pool_id": pool.id,
            "pool_name": pool.name,
            "unit_flow_mb": pool.flow_size,
            "unit_price": float(unit_price),
            "balance": balance_info["balance"]
        }

    async def purchase_pool_topup(
        self,
        db: AsyncSession,
        pool_id: int,
        quantity: int,
        current_user_id: int,
        remark: Optional[str] = None
    ) -> dict:
        pool = await self._get_pool_in_scope(db, pool_id, current_user_id, user_level=3)
        if pool.user_id != current_user_id:
            raise BusinessException(code=403, msg="只能购买自己名下流量池的加油包")
        if quantity <= 0:
            raise BusinessException(code=400, msg="购买份数必须大于0")

        avg_price_result = await db.execute(
            select(func.avg(IotCardModel.sale_price)).where(
                IotCardModel.pool_id == pool.id,
                IotCardModel.is_deleted == 0,
                IotCardModel.sale_price.is_not(None)
            )
        )
        avg_sale_price = avg_price_result.scalar_one_or_none()
        if avg_sale_price is None:
            raise BusinessException(code=400, msg="流量池缺少销售价格数据，暂不可购买加油包")

        unit_price = self._normalize_price(Decimal(str(avg_sale_price)) * Decimal("3"))
        total_price = self._normalize_price(unit_price * Decimal(str(quantity)))
        added_flow_mb = pool.flow_size * quantity

        balance_result = await account_balance_service.consume_balance(
            db=db,
            user_id=current_user_id,
            amount=total_price,
            detail=f"流量池加油包购买 {quantity} 份",
            target_type="pool",
            target_id=pool.id,
            target_name=pool.name
        )

        self._apply_pool_addon_flow(pool, added_flow_mb)
        await db.flush()
        pool = await pool_crud.update_stats(db, pool.id)

        suspended_cards_result = await db.execute(
            select(IotCardModel).where(
                IotCardModel.pool_id == pool.id,
                IotCardModel.status == CardStatus.suspended,
                IotCardModel.suspend_type == SuspendType.pool_exceed,
                IotCardModel.is_deleted == 0
            )
        )
        suspended_cards = list(suspended_cards_result.scalars().all())
        auto_resume_result = await SuspendActionService.auto_resume_cards_after_flow_adjustment(
            db=db,
            cards=suspended_cards,
            operator_id=current_user_id,
            reason="购买流量池加油包后自动复机"
        )

        await SysOperationLogCRUD.create(
            db=db,
            module="orders",
            action="pool_topup_purchase",
            user_id=current_user_id,
            target_type="pool",
            target_id=pool.id,
            target_name=pool.name,
            detail=(
                f"购买流量池加油包 {quantity} 份，补量 {added_flow_mb}MB，扣减余额 {total_price} 元，"
                f"自动复机 {auto_resume_result['resumed_count']} 张。备注：{remark or ''}"
            )
        )

        pool_dict = pool.to_dict()
        await self._enrich_pool_dict(db, pool, pool_dict)
        pool_dict.update({
            "can_self_topup": pool.user_id == current_user_id,
            "quantity": quantity,
            "unit_price": float(unit_price),
            "total_price": float(total_price),
            "added_flow_mb": added_flow_mb,
            "balance": balance_result["after_balance"],
            "auto_resumed": auto_resume_result["resumed_count"]
        })
        return pool_dict


pool_service = PoolService()
