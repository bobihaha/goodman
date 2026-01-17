"""
物联网卡 CRUD 操作
"""
from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.iot_card import IotCardModel, CardTransferModel, CardStatus
from app.db.models.package import CarrierType, PeriodType


class IotCardCRUD:
    """物联网卡 CRUD"""

    async def get_by_id(self, db: AsyncSession, card_id: int, user_id: Optional[int] = None) -> Optional[IotCardModel]:
        """根据ID获取卡片"""
        query = select(IotCardModel).where(
            IotCardModel.id == card_id,
            IotCardModel.is_deleted == 0
        )
        if user_id is not None:
            query = query.where(IotCardModel.user_id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_iccid(self, db: AsyncSession, iccid: str, user_id: Optional[int] = None) -> Optional[IotCardModel]:
        """根据ICCID获取卡片"""
        query = select(IotCardModel).where(
            IotCardModel.iccid == iccid,
            IotCardModel.is_deleted == 0
        )
        if user_id is not None:
            query = query.where(IotCardModel.user_id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        carrier: Optional[str] = None,
        period_type: Optional[str] = None,
        pool_id: Optional[int] = None,
        is_pool_member: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[IotCardModel], int]:
        """获取卡片列表"""
        query = select(IotCardModel).where(IotCardModel.is_deleted == 0)
        count_query = select(func.count(IotCardModel.id)).where(IotCardModel.is_deleted == 0)

        # 用户过滤 (数据隔离)
        if user_id is not None:
            query = query.where(IotCardModel.user_id == user_id)
            count_query = count_query.where(IotCardModel.user_id == user_id)

        # 关键词搜索 (ICCID/MSISDN/后6位)
        if keyword:
            keyword = keyword.strip()
            if len(keyword) <= 6:
                # 后6位模糊查询
                keyword_filter = or_(
                    IotCardModel.iccid.like(f"%{keyword}"),
                    IotCardModel.msisdn.like(f"%{keyword}")
                )
            else:
                # 完整匹配
                keyword_filter = or_(
                    IotCardModel.iccid == keyword,
                    IotCardModel.msisdn == keyword,
                    IotCardModel.imsi == keyword
                )
            query = query.where(keyword_filter)
            count_query = count_query.where(keyword_filter)

        # 状态过滤
        if status:
            query = query.where(IotCardModel.status == status)
            count_query = count_query.where(IotCardModel.status == status)

        # 运营商过滤
        if carrier:
            query = query.where(IotCardModel.carrier == carrier)
            count_query = count_query.where(IotCardModel.carrier == carrier)

        # 周期类型过滤
        if period_type:
            query = query.where(IotCardModel.period_type == period_type)
            count_query = count_query.where(IotCardModel.period_type == period_type)

        # 流量池过滤
        if pool_id is not None:
            query = query.where(IotCardModel.pool_id == pool_id)
            count_query = count_query.where(IotCardModel.pool_id == pool_id)

        # 是否加入流量池
        if is_pool_member is not None:
            member_value = 1 if is_pool_member else 0
            query = query.where(IotCardModel.is_pool_member == member_value)
            count_query = count_query.where(IotCardModel.is_pool_member == member_value)

        # 统计总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * page_size
        query = query.order_by(IotCardModel.id.desc()).offset(offset).limit(page_size)

        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def search(
        self,
        db: AsyncSession,
        keyword: str,
        user_id: Optional[int] = None,
        limit: int = 10
    ) -> List[IotCardModel]:
        """快速搜索 (支持后6位)"""
        keyword = keyword.strip()
        query = select(IotCardModel).where(IotCardModel.is_deleted == 0)

        if user_id is not None:
            query = query.where(IotCardModel.user_id == user_id)

        if len(keyword) <= 6:
            query = query.where(
                or_(
                    IotCardModel.iccid.like(f"%{keyword}"),
                    IotCardModel.msisdn.like(f"%{keyword}")
                )
            )
        else:
            query = query.where(
                or_(
                    IotCardModel.iccid == keyword,
                    IotCardModel.msisdn == keyword
                )
            )

        query = query.limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_stats(self, db: AsyncSession, user_id: Optional[int] = None) -> dict:
        """获取卡片统计"""
        query = select(
            IotCardModel.status,
            func.count(IotCardModel.id).label("count")
        ).where(IotCardModel.is_deleted == 0)

        if user_id is not None:
            query = query.where(IotCardModel.user_id == user_id)

        query = query.group_by(IotCardModel.status)
        result = await db.execute(query)
        rows = result.all()

        stats = {
            "total": 0,
            "stock": 0,
            "testing": 0,
            "silent": 0,
            "activated": 0,
            "expired": 0,
            "suspended": 0,
            "cancelled": 0
        }

        for row in rows:
            status_value = row[0].value if hasattr(row[0], 'value') else row[0]
            count = row[1]
            if status_value in stats:
                stats[status_value] = count
            stats["total"] += count

        return stats

    async def update_remark(
        self,
        db: AsyncSession,
        card_id: int,
        remark: str,
        user_id: Optional[int] = None
    ) -> Optional[IotCardModel]:
        """更新卡片备注"""
        card = await self.get_by_id(db, card_id, user_id)
        if not card:
            return None
        card.remark = remark
        await db.commit()
        await db.refresh(card)
        return card

    async def batch_update_remark(
        self,
        db: AsyncSession,
        card_ids: List[int],
        remark: str,
        user_id: Optional[int] = None
    ) -> int:
        """批量更新备注"""
        count = 0
        for card_id in card_ids:
            card = await self.get_by_id(db, card_id, user_id)
            if card:
                card.remark = remark
                count += 1
        await db.commit()
        return count

    async def transfer(
        self,
        db: AsyncSession,
        card_id: int,
        from_user_id: int,
        to_user_id: int,
        operator_id: int,
        remark: Optional[str] = None
    ) -> Optional[IotCardModel]:
        """划拨卡片"""
        card = await self.get_by_id(db, card_id, from_user_id)
        if not card:
            return None

        # 更新卡片归属
        old_user_id = card.user_id
        card.user_id = to_user_id

        # 记录划拨日志
        transfer_log = CardTransferModel(
            card_id=card_id,
            iccid=card.iccid,
            from_user_id=old_user_id,
            to_user_id=to_user_id,
            operator_id=operator_id,
            remark=remark
        )
        db.add(transfer_log)

        await db.commit()
        await db.refresh(card)
        return card

    async def batch_transfer(
        self,
        db: AsyncSession,
        card_ids: List[int],
        from_user_id: int,
        to_user_id: int,
        operator_id: int,
        remark: Optional[str] = None
    ) -> Tuple[int, int]:
        """批量划拨，返回 (成功数, 失败数)"""
        success = 0
        failed = 0

        for card_id in card_ids:
            card = await self.get_by_id(db, card_id, from_user_id)
            if card:
                card.user_id = to_user_id
                transfer_log = CardTransferModel(
                    card_id=card_id,
                    iccid=card.iccid,
                    from_user_id=from_user_id,
                    to_user_id=to_user_id,
                    operator_id=operator_id,
                    remark=remark
                )
                db.add(transfer_log)
                success += 1
            else:
                failed += 1

        await db.commit()
        return success, failed

    async def get_by_ids(
        self,
        db: AsyncSession,
        card_ids: List[int],
        user_id: Optional[int] = None
    ) -> List[IotCardModel]:
        """根据ID列表获取卡片"""
        query = select(IotCardModel).where(
            IotCardModel.id.in_(card_ids),
            IotCardModel.is_deleted == 0
        )
        if user_id is not None:
            query = query.where(IotCardModel.user_id == user_id)
        result = await db.execute(query)
        return list(result.scalars().all())


class CardTransferCRUD:
    """划拨记录 CRUD"""

    async def get_list(
        self,
        db: AsyncSession,
        card_id: Optional[int] = None,
        user_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[CardTransferModel], int]:
        """获取划拨记录"""
        query = select(CardTransferModel).where(CardTransferModel.is_deleted == 0)
        count_query = select(func.count(CardTransferModel.id)).where(CardTransferModel.is_deleted == 0)

        if card_id:
            query = query.where(CardTransferModel.card_id == card_id)
            count_query = count_query.where(CardTransferModel.card_id == card_id)

        if user_id:
            query = query.where(
                or_(
                    CardTransferModel.from_user_id == user_id,
                    CardTransferModel.to_user_id == user_id
                )
            )
            count_query = count_query.where(
                or_(
                    CardTransferModel.from_user_id == user_id,
                    CardTransferModel.to_user_id == user_id
                )
            )

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(CardTransferModel.id.desc()).offset(offset).limit(page_size)

        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total


iot_card_crud = IotCardCRUD()
card_transfer_crud = CardTransferCRUD()
