"""
流量池 CRUD 操作
"""
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, update, func, or_
from app.db.models.pool import TrafficPoolModel, PoolCardLogModel, PoolStatus
from app.db.models.iot_card import IotCardModel, CardStatus
from app.db.models.suspend import AlertLevel, AlertTargetType
from app.flow_packages import get_current_flow_cycle_month, is_flow_cycle_active

AUTO_POOL_REMARK = "系统自动创建的流量池"


def valid_pool_member_conditions(pool_id_expr):
    """有效池成员：已归属用户、仍标记为池成员、未删除。"""
    return (
        IotCardModel.pool_id == pool_id_expr,
        IotCardModel.is_pool_member == 1,
        IotCardModel.user_id.is_not(None),
        IotCardModel.is_deleted == 0,
    )


def pool_alert_condition():
    """流量池当前用量达到任一有效告警阈值。"""
    usage_percent = func.round(
        TrafficPoolModel.data_used * 100.0
        / func.nullif(TrafficPoolModel.data_total, 0),
        2,
    )
    return and_(
        TrafficPoolModel.data_total > 0,
        or_(
            and_(
                TrafficPoolModel.alert_threshold_1.is_not(None),
                TrafficPoolModel.alert_threshold_1 > 0,
                usage_percent >= TrafficPoolModel.alert_threshold_1,
            ),
            and_(
                TrafficPoolModel.alert_threshold_2.is_not(None),
                TrafficPoolModel.alert_threshold_2 > 0,
                usage_percent >= TrafficPoolModel.alert_threshold_2,
            ),
            and_(
                TrafficPoolModel.alert_threshold_3.is_not(None),
                TrafficPoolModel.alert_threshold_3 > 0,
                usage_percent >= TrafficPoolModel.alert_threshold_3,
            ),
        ),
    )


class TrafficPoolCRUD:
    """流量池 CRUD"""

    def _exclude_empty_auto_pools(self, query):
        """隐藏没有有效成员的系统自动池，避免历史空池继续展示。"""
        member_exists = (
            select(IotCardModel.id)
            .where(*valid_pool_member_conditions(TrafficPoolModel.id))
            .exists()
        )
        return query.where(
            or_(
                TrafficPoolModel.remark.is_(None),
                TrafficPoolModel.remark != AUTO_POOL_REMARK,
                member_exists,
            )
        )

    def _apply_user_scope(self, query, user_ids: Optional[List[int]] = None):
        """按用户可见范围过滤流量池。

        可见流量池包括：
        1. 流量池归属在当前可见用户范围内
        2. 当前可见用户名下有卡片加入的共享流量池
        """
        if user_ids is None:
            return query

        visible_pool_ids = (
            select(IotCardModel.pool_id)
            .where(
                IotCardModel.user_id.in_(user_ids),
                IotCardModel.pool_id.is_not(None),
                IotCardModel.is_pool_member == 1,
                IotCardModel.is_deleted == 0
            )
            .distinct()
        )
        return query.where(
            or_(
                TrafficPoolModel.user_id.in_(user_ids),
                TrafficPoolModel.id.in_(visible_pool_ids)
            )
        )

    async def create(
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
    ) -> TrafficPoolModel:
        """创建流量池"""
        pool = TrafficPoolModel(
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
        db.add(pool)
        await db.commit()
        await db.refresh(pool)
        return pool

    async def get_by_id(self, db: AsyncSession, pool_id: int) -> Optional[TrafficPoolModel]:
        """根据ID获取流量池"""
        query = select(TrafficPoolModel).where(
            TrafficPoolModel.id == pool_id,
            TrafficPoolModel.is_deleted == 0
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_in_scope(
        self,
        db: AsyncSession,
        pool_id: int,
        user_ids: Optional[List[int]] = None
    ) -> Optional[TrafficPoolModel]:
        """根据可见范围获取流量池"""
        query = select(TrafficPoolModel).where(
            TrafficPoolModel.id == pool_id,
            TrafficPoolModel.is_deleted == 0
        )
        query = self._apply_user_scope(query, user_ids)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        user_ids: Optional[List[int]] = None,
        name: Optional[str] = None,
        carrier: Optional[str] = None,
        status: Optional[str] = None,
        is_alert: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[TrafficPoolModel], int]:
        """获取流量池列表"""
        query = select(TrafficPoolModel).where(TrafficPoolModel.is_deleted == 0)
        count_query = select(func.count(TrafficPoolModel.id)).where(TrafficPoolModel.is_deleted == 0)
        query = self._exclude_empty_auto_pools(query)
        count_query = self._exclude_empty_auto_pools(count_query)

        if user_ids is not None:
            query = self._apply_user_scope(query, user_ids)
            count_query = self._apply_user_scope(count_query, user_ids)
        elif user_id is not None:
            query = query.where(TrafficPoolModel.user_id == user_id)
            count_query = count_query.where(TrafficPoolModel.user_id == user_id)
        if name:
            query = query.where(TrafficPoolModel.name.like(f"%{name}%"))
            count_query = count_query.where(TrafficPoolModel.name.like(f"%{name}%"))
        if carrier:
            query = query.where(TrafficPoolModel.carrier == carrier)
            count_query = count_query.where(TrafficPoolModel.carrier == carrier)
        if status:
            query = query.where(TrafficPoolModel.status == status)
            count_query = count_query.where(TrafficPoolModel.status == status)
        if is_alert is not None:
            alert_condition = pool_alert_condition()
            if not is_alert:
                alert_condition = ~alert_condition
            query = query.where(alert_condition)
            count_query = count_query.where(alert_condition)

        # 总数
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 分页
        query = query.order_by(TrafficPoolModel.id.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = result.scalars().all()

        return list(items), total

    async def update(
        self,
        db: AsyncSession,
        pool_id: int,
        **kwargs
    ) -> Optional[TrafficPoolModel]:
        """更新流量池"""
        pool = await self.get_by_id(db, pool_id)
        if not pool:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(pool, key):
                setattr(pool, key, value)

        await db.commit()
        await db.refresh(pool)
        return pool

    async def delete(self, db: AsyncSession, pool_id: int) -> bool:
        """软删除流量池"""
        pool = await self.get_by_id(db, pool_id)
        if not pool:
            return False

        pool.is_deleted = 1
        await db.commit()
        return True

    async def update_stats(
        self,
        db: AsyncSession,
        pool_id: int,
        commit: bool = True,
        run_checks: bool = True,
    ) -> Optional[TrafficPoolModel]:
        """更新流量池统计数据，并检查是否需要停卡"""
        pool = await self.get_by_id(db, pool_id)
        if not pool:
            return None

        # 查询池内卡片统计
        query = select(
            func.count(IotCardModel.id).label("card_count"),
            func.coalesce(func.sum(IotCardModel.data_total), 0).label("data_total"),
            func.coalesce(func.sum(IotCardModel.data_used), 0).label("data_used")
        ).where(
            *valid_pool_member_conditions(pool_id)
        )
        result = await db.execute(query)
        row = result.one()

        package_flow = int(row.data_total or 0)
        if pool.addon_flow and not pool.addon_flow_month:
            pool.addon_flow_month = get_current_flow_cycle_month()
        effective_addon = int(pool.addon_flow or 0) if is_flow_cycle_active(pool.addon_flow_month) else 0
        if not effective_addon and pool.addon_flow:
            pool.addon_flow = 0
            pool.addon_flow_month = None
        pool.card_count = int(row.card_count or 0)
        pool.package_flow = package_flow
        pool.data_total = package_flow + effective_addon
        pool.data_used = int(row.data_used or 0)

        if commit:
            await db.commit()
            await db.refresh(pool)
        else:
            await db.flush()

        if run_checks:
            await self._check_pool_alert_thresholds(db, pool)
            # 检查是否需要根据用户设置的停卡阈值进行停卡
            await self._check_pool_stop_threshold(db, pool)

        return pool

    async def _check_pool_alert_thresholds(self, db: AsyncSession, pool: TrafficPoolModel) -> None:
        """检查流量池预警阈值，记录告警并发送通知"""
        if not pool.user_id or not pool.data_total:
            return

        usage_percent = pool.get_usage_percent()
        if usage_percent <= 0:
            return

        from app.crud.suspend_crud import AlertLogCRUD
        from app.services.notification_service import NotificationService

        alert_rules = [
            (
                pool.alert_threshold_1,
                AlertLevel.warning
            ),
            (
                pool.alert_threshold_2,
                AlertLevel.critical
            ),
            (
                pool.alert_threshold_3,
                AlertLevel.exceed
            ),
        ]

        should_notify = False
        for threshold, alert_level in alert_rules:
            if not threshold or usage_percent < threshold:
                continue

            exists = await AlertLogCRUD.check_exists(
                db,
                AlertTargetType.pool,
                pool.id,
                alert_level
            )
            if exists:
                continue

            await AlertLogCRUD.create(
                db=db,
                target_type=AlertTargetType.pool,
                target_id=pool.id,
                target_name=pool.name,
                alert_level=alert_level,
                usage_percent=int(usage_percent),
                threshold=threshold,
                user_id=pool.user_id
            )
            should_notify = True

        if should_notify:
            await NotificationService.send_pending_usage_alerts_for_user(db, pool.user_id)

    async def _check_pool_stop_threshold(self, db: AsyncSession, pool: TrafficPoolModel) -> None:
        """检查流量池是否超过用户设置的停卡阈值，超过则全池停卡"""
        if not pool.user_id:
            return

        usage_percent = pool.get_usage_percent()
        if usage_percent <= 0:
            return

        # 查询用户的 quota 配置获取 pool_stop_threshold
        from sqlalchemy import select
        from app.db.models.sys_user import SysUserModel

        user_stmt = select(SysUserModel.quota).where(
            SysUserModel.id == pool.user_id,
            SysUserModel.is_deleted == 0
        )
        user_result = await db.execute(user_stmt)
        quota_data = user_result.scalar_one_or_none()

        if not quota_data:
            return

        import json
        quota = quota_data if isinstance(quota_data, dict) else json.loads(quota_data)
        pool_stop_threshold = quota.get("pool_stop_threshold")

        if pool_stop_threshold is None:
            return

        if usage_percent >= pool_stop_threshold:
            # 超过阈值，将池内所有已激活卡片停卡
            from app.db.models.iot_card import SuspendType
            from app.db.models.suspend import SuspendActionType, SuspendLogModel
            from app.db.models.supplier import SupplierModel
            from app.clients.supplier_api import get_supplier_client
            import logging

            reason = f"流量池用量超限停卡(用量{usage_percent}%，阈值{pool_stop_threshold}%)"
            suspend_time = datetime.now()
            logger = logging.getLogger(__name__)

            cards_result = await db.execute(
                select(IotCardModel).where(
                    IotCardModel.pool_id == pool.id,
                    IotCardModel.status == CardStatus.activated,
                    IotCardModel.is_deleted == 0
                )
            )
            cards = list(cards_result.scalars().all())

            supplier_ids = {card.supplier_id for card in cards if card.supplier_id}
            supplier_map = {}
            if supplier_ids:
                supplier_result = await db.execute(
                    select(SupplierModel).where(
                        SupplierModel.id.in_(supplier_ids),
                        SupplierModel.is_deleted == 0
                    )
                )
                supplier_map = {item.id: item for item in supplier_result.scalars().all()}

            for card in cards:
                supplier = supplier_map.get(card.supplier_id)
                if not supplier:
                    continue
                try:
                    supplier_client = get_supplier_client(
                        supplier_id=card.supplier_id,
                        api_url=supplier.api_url or "",
                        api_key=supplier.api_key or "",
                        api_secret=supplier.api_secret or ""
                    )
                    api_success = await supplier_client.suspend_card(card.iccid, reason)
                except Exception as exc:
                    logger.error(f"流量池超限供应商停卡失败: iccid={card.iccid}, error={exc}")
                    api_success = False

                if not api_success:
                    continue

                card.status = CardStatus.suspended
                card.suspend_type = SuspendType.pool_exceed
                card.suspend_at = suspend_time
                card.suspend_reason = reason
                db.add(SuspendLogModel(
                    card_id=card.id,
                    iccid=card.iccid,
                    action=SuspendActionType.suspend,
                    suspend_type="pool_exceed",
                    pool_id=pool.id,
                    reason=reason
                ))

            await db.commit()

    async def get_stats(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        user_ids: Optional[List[int]] = None
    ) -> dict:
        """获取流量池总体统计"""
        query = select(TrafficPoolModel).where(TrafficPoolModel.is_deleted == 0)
        query = self._exclude_empty_auto_pools(query)

        if user_ids is not None:
            query = self._apply_user_scope(query, user_ids)
        elif user_id is not None:
            query = query.where(TrafficPoolModel.user_id == user_id)

        result = await db.execute(query)
        pools = result.scalars().all()

        total_pools = len(pools)
        total_cards = sum(pool.card_count for pool in pools)
        total_flow = sum(pool.data_total for pool in pools)
        used_flow = sum(pool.data_used for pool in pools)
        alert_pools = sum(1 for pool in pools if pool.is_alert())
        enabled_count = sum(1 for p in pools if p.status == PoolStatus.enable)
        disabled_count = sum(1 for p in pools if p.status == PoolStatus.disable)

        by_carrier = {"cmcc": 0, "cucc": 0, "ctcc": 0}
        for p in pools:
            carrier_val = p.carrier.value if p.carrier else None
            if carrier_val in by_carrier:
                by_carrier[carrier_val] += 1

        return {
            "total": total_pools,
            "enabled": enabled_count,
            "disabled": disabled_count,
            "alert_count": alert_pools,
            "total_cards": total_cards,
            "total_flow": total_flow,
            "used_flow": used_flow,
            "by_carrier": by_carrier
        }

    async def find_or_create_pool(
        self,
        db: AsyncSession,
        user_id: int,
        carrier: str,
        flow_size: int,
        period_type: str,
        created_by: int,
        sale_package_id: Optional[int] = None
    ) -> TrafficPoolModel:
        """查找或创建流量池（用于自动加入）"""
        # 查找是否已存在相同规格的流量池
        query = select(TrafficPoolModel).where(
            TrafficPoolModel.user_id == user_id,
            TrafficPoolModel.carrier == carrier,
            TrafficPoolModel.flow_size == flow_size,
            TrafficPoolModel.period_type == period_type,
            TrafficPoolModel.status == PoolStatus.enable,
            TrafficPoolModel.is_deleted == 0
        )
        if sale_package_id is not None:
            query = query.where(TrafficPoolModel.sale_package_id == sale_package_id)
        result = await db.execute(query)
        pool = result.scalar_one_or_none()

        if pool:
            return pool

        # 不存在则创建新流量池
        from app.db.models.package import CARRIER_NAMES, PERIOD_CONFIG

        carrier_name = CARRIER_NAMES.get(carrier, carrier)
        flow_display = f"{flow_size}MB" if flow_size < 1024 else f"{flow_size // 1024}GB"
        period_name = PERIOD_CONFIG.get(period_type, {}).get("name", period_type)

        pool_name = f"{carrier_name}-{flow_display}-{period_name}-自动池"

        pool = await self.create(
            db=db,
            name=pool_name,
            carrier=carrier,
            flow_size=flow_size,
            period_type=period_type,
            user_id=user_id,
            sale_package_id=sale_package_id,
            alert_threshold_1=80,
            alert_threshold_2=90,
            alert_threshold_3=95,
            created_by=created_by,
            remark=AUTO_POOL_REMARK
        )

        return pool


class PoolCardCRUD:
    """流量池卡片操作 CRUD"""

    async def add_cards(
        self,
        db: AsyncSession,
        pool: TrafficPoolModel,
        card_ids: List[int],
        operator_id: int,
        user_ids: Optional[List[int]] = None,
        remark: Optional[str] = None
    ) -> Tuple[int, int, List[dict]]:
        """添加卡片到流量池"""
        from app.db.models.iot_card import CardType
        
        success = 0
        failed = 0
        fail_details = []

        for card_id in card_ids:
            # 查询卡片
            query = select(IotCardModel).where(
                IotCardModel.id == card_id,
                IotCardModel.is_deleted == 0
            )
            if user_ids is not None:
                query = query.where(IotCardModel.user_id.in_(user_ids))
            result = await db.execute(query)
            card = result.scalar_one_or_none()

            if not card:
                failed += 1
                fail_details.append({"card_id": card_id, "reason": "卡片不存在或无权访问"})
                continue

            # 检查卡片类型：只有流量池卡才能加入流量池
            if card.card_type != CardType.pool:
                failed += 1
                fail_details.append({
                    "card_id": card_id,
                    "iccid": card.iccid,
                    "reason": "单卡类型不能加入流量池，只有流量池卡才能加入"
                })
                continue

            # 检查卡片是否已在其他池中
            if card.pool_id and card.pool_id != pool.id:
                failed += 1
                fail_details.append({"card_id": card_id, "iccid": card.iccid, "reason": "卡片已在其他流量池中"})
                continue

            # 检查卡片状态是否为已激活
            if card.status != CardStatus.activated:
                failed += 1
                fail_details.append({"card_id": card_id, "iccid": card.iccid, "reason": f"卡片状态不是已激活: {card.status.value}"})
                continue

            # 检查规格是否匹配
            if (card.carrier != pool.carrier or
                card.flow_size != pool.flow_size or
                card.period_type != pool.period_type):
                failed += 1
                fail_details.append({
                    "card_id": card_id,
                    "iccid": card.iccid,
                    "reason": f"规格不匹配: 卡片[{card.carrier.value}/{card.flow_size}MB/{card.period_type.value}] vs 流量池[{pool.carrier.value}/{pool.flow_size}MB/{pool.period_type.value}]"
                })
                continue

            # 添加到流量池
            card.pool_id = pool.id
            card.is_pool_member = 1

            # 记录日志
            log = PoolCardLogModel(
                pool_id=pool.id,
                card_id=card.id,
                iccid=card.iccid,
                action="add",
                operator_id=operator_id,
                remark=remark
            )
            db.add(log)
            success += 1

        await db.commit()

        # 更新流量池统计
        await pool_crud.update_stats(db, pool.id)

        return success, failed, fail_details

    async def remove_cards(
        self,
        db: AsyncSession,
        pool: TrafficPoolModel,
        card_ids: List[int],
        operator_id: int,
        user_ids: Optional[List[int]] = None,
        remark: Optional[str] = None
    ) -> Tuple[int, int, List[dict]]:
        """从流量池移除卡片"""
        success = 0
        failed = 0
        fail_details = []

        for card_id in card_ids:
            # 查询卡片
            query = select(IotCardModel).where(
                IotCardModel.id == card_id,
                IotCardModel.is_deleted == 0
            )
            if user_ids is not None:
                query = query.where(IotCardModel.user_id.in_(user_ids))
            result = await db.execute(query)
            card = result.scalar_one_or_none()

            if not card:
                failed += 1
                fail_details.append({"card_id": card_id, "reason": "卡片不存在或无权访问"})
                continue

            # 检查卡片是否在此流量池中
            if card.pool_id != pool.id:
                failed += 1
                fail_details.append({"card_id": card_id, "iccid": card.iccid, "reason": "卡片不在此流量池中"})
                continue

            # 从流量池移除
            card.pool_id = None
            card.is_pool_member = 0

            # 记录日志
            log = PoolCardLogModel(
                pool_id=pool.id,
                card_id=card.id,
                iccid=card.iccid,
                action="remove",
                operator_id=operator_id,
                remark=remark
            )
            db.add(log)
            success += 1

        await db.commit()

        # 更新流量池统计
        await pool_crud.update_stats(db, pool.id)

        return success, failed, fail_details

    async def get_pool_cards(
        self,
        db: AsyncSession,
        pool_id: int,
        user_ids: Optional[List[int]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[IotCardModel], int]:
        """获取流量池内卡片列表"""
        query = select(IotCardModel).where(
            *valid_pool_member_conditions(pool_id)
        )
        count_query = select(func.count(IotCardModel.id)).where(
            *valid_pool_member_conditions(pool_id)
        )
        if user_ids is not None:
            query = query.where(IotCardModel.user_id.in_(user_ids))
            count_query = count_query.where(IotCardModel.user_id.in_(user_ids))

        # 总数
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 分页
        query = query.order_by(IotCardModel.id.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = result.scalars().all()

        return list(items), total


class PoolLogCRUD:
    """流量池日志 CRUD"""

    async def get_logs(
        self,
        db: AsyncSession,
        pool_id: int,
        action: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[PoolCardLogModel], int]:
        """获取流量池操作日志"""
        query = select(PoolCardLogModel).where(
            PoolCardLogModel.pool_id == pool_id,
            PoolCardLogModel.is_deleted == 0
        )
        count_query = select(func.count(PoolCardLogModel.id)).where(
            PoolCardLogModel.pool_id == pool_id,
            PoolCardLogModel.is_deleted == 0
        )

        if action:
            query = query.where(PoolCardLogModel.action == action)
            count_query = count_query.where(PoolCardLogModel.action == action)

        total_result = await db.execute(count_query)
        total = total_result.scalar()

        query = query.order_by(PoolCardLogModel.id.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = result.scalars().all()

        return list(items), total


pool_crud = TrafficPoolCRUD()
pool_card_crud = PoolCardCRUD()
pool_log_crud = PoolLogCRUD()
