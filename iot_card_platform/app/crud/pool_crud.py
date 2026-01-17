"""
流量池 CRUD 操作
"""
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.db.models.pool import TrafficPoolModel, PoolCardLogModel, PoolStatus
from app.db.models.iot_card import IotCardModel, CardStatus


class TrafficPoolCRUD:
    """流量池 CRUD"""

    async def create(
        self,
        db: AsyncSession,
        name: str,
        carrier: str,
        flow_size: int,
        period_type: str,
        user_id: Optional[int] = None,
        alert_threshold: Optional[int] = None,
        stop_threshold: Optional[int] = None,
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
            alert_threshold=alert_threshold,
            stop_threshold=stop_threshold,
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

    async def get_list(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        carrier: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[TrafficPoolModel], int]:
        """获取流量池列表"""
        query = select(TrafficPoolModel).where(TrafficPoolModel.is_deleted == 0)
        count_query = select(func.count(TrafficPoolModel.id)).where(TrafficPoolModel.is_deleted == 0)

        if user_id is not None:
            query = query.where(TrafficPoolModel.user_id == user_id)
            count_query = count_query.where(TrafficPoolModel.user_id == user_id)
        if carrier:
            query = query.where(TrafficPoolModel.carrier == carrier)
            count_query = count_query.where(TrafficPoolModel.carrier == carrier)
        if status:
            query = query.where(TrafficPoolModel.status == status)
            count_query = count_query.where(TrafficPoolModel.status == status)

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

    async def update_stats(self, db: AsyncSession, pool_id: int) -> Optional[TrafficPoolModel]:
        """更新流量池统计数据"""
        pool = await self.get_by_id(db, pool_id)
        if not pool:
            return None

        # 查询池内卡片统计
        query = select(
            func.count(IotCardModel.id).label("card_count"),
            func.coalesce(func.sum(IotCardModel.data_total), 0).label("data_total"),
            func.coalesce(func.sum(IotCardModel.data_used), 0).label("data_used")
        ).where(
            IotCardModel.pool_id == pool_id,
            IotCardModel.is_deleted == 0
        )
        result = await db.execute(query)
        row = result.one()

        pool.card_count = row.card_count or 0
        pool.data_total = row.data_total or 0
        pool.data_used = row.data_used or 0

        await db.commit()
        await db.refresh(pool)
        return pool


class PoolCardCRUD:
    """流量池卡片操作 CRUD"""

    async def add_cards(
        self,
        db: AsyncSession,
        pool: TrafficPoolModel,
        card_ids: List[int],
        operator_id: int,
        remark: Optional[str] = None
    ) -> Tuple[int, int, List[dict]]:
        """添加卡片到流量池"""
        success = 0
        failed = 0
        fail_details = []

        for card_id in card_ids:
            # 查询卡片
            query = select(IotCardModel).where(
                IotCardModel.id == card_id,
                IotCardModel.is_deleted == 0
            )
            result = await db.execute(query)
            card = result.scalar_one_or_none()

            if not card:
                failed += 1
                fail_details.append({"card_id": card_id, "reason": "卡片不存在"})
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
            result = await db.execute(query)
            card = result.scalar_one_or_none()

            if not card:
                failed += 1
                fail_details.append({"card_id": card_id, "reason": "卡片不存在"})
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
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[IotCardModel], int]:
        """获取流量池内卡片列表"""
        query = select(IotCardModel).where(
            IotCardModel.pool_id == pool_id,
            IotCardModel.is_deleted == 0
        )
        count_query = select(func.count(IotCardModel.id)).where(
            IotCardModel.pool_id == pool_id,
            IotCardModel.is_deleted == 0
        )

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
