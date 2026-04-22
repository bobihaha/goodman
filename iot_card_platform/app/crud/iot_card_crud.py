"""
物联网卡 CRUD 操作
"""
from typing import Optional, List, Tuple, Dict
from sqlalchemy import select, func, or_, and_, delete, exists, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.iot_card import IotCardModel, CardTransferModel, CardStatus, CardUserRemarkModel
from app.db.models.package import CarrierType, PeriodType
from app.db.models.stock import StockOutRecordCardModel, StockOutRecordModel


class IotCardCRUD:
    """物联网卡 CRUD"""

    SORT_FIELD_MAP = {
        "iccid": IotCardModel.iccid,
        "imsi": IotCardModel.imsi,
        "msisdn": IotCardModel.msisdn,
        "card_type": IotCardModel.card_type,
        "carrier": IotCardModel.carrier,
        "status": IotCardModel.status,
        "data_used_month": IotCardModel.data_used_month,
        "data_total": IotCardModel.data_total,
        "data_used": IotCardModel.data_used,
        "flow_size": IotCardModel.flow_size,
        "test_expire_date": IotCardModel.test_expire_date,
        "silent_expire_date": IotCardModel.silent_expire_date,
        "activated_at": IotCardModel.activated_at,
        "stock_out_date": IotCardModel.stock_out_date,
        "expired_at": IotCardModel.expired_at,
        "is_pool_member": IotCardModel.is_pool_member,
        "remark": IotCardModel.remark,
        "created_at": IotCardModel.created_at,
        "updated_at": IotCardModel.updated_at,
    }

    @staticmethod
    def _build_short_iccid_keyword_filter(keyword: str):
        """短关键字查询:
        1. 移动卡按 ICCID 后6位查询
        2. 联通/电信卡按 ICCID 倒数第2位到倒数第7位的连续6位数字查询
        3. 号码保持后缀模糊匹配
        """
        ctcc_cucc_mid6 = func.substr(IotCardModel.iccid, func.length(IotCardModel.iccid) - 6, 6)
        return or_(
            and_(
                IotCardModel.carrier == CarrierType.cmcc,
                or_(
                    IotCardModel.iccid_suffix == keyword,
                    func.right(IotCardModel.iccid, 6) == keyword
                )
            ),
            and_(
                IotCardModel.carrier.in_([CarrierType.cucc, CarrierType.ctcc]),
                ctcc_cucc_mid6 == keyword
            ),
            IotCardModel.msisdn.like(f"%{keyword}")
        )

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

    async def get_by_id_in_scope(
        self,
        db: AsyncSession,
        card_id: int,
        user_ids: Optional[List[int]] = None
    ) -> Optional[IotCardModel]:
        """根据ID获取卡片（支持用户可见范围）"""
        query = select(IotCardModel).where(
            IotCardModel.id == card_id,
            IotCardModel.is_deleted == 0
        )
        if user_ids is not None:
            query = query.where(IotCardModel.user_id.in_(user_ids))
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
        user_ids: Optional[List[int]] = None,
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
        remark_user_id: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> Tuple[List[IotCardModel], int]:
        """获取卡片列表"""
        query = select(IotCardModel).where(IotCardModel.is_deleted == 0)
        count_query = select(func.count(IotCardModel.id)).where(IotCardModel.is_deleted == 0)

        # 用户过滤 (数据隔离)
        if user_ids is not None:
            query = query.where(IotCardModel.user_id.in_(user_ids))
            count_query = count_query.where(IotCardModel.user_id.in_(user_ids))
        elif user_id is not None:
            query = query.where(IotCardModel.user_id == user_id)
            count_query = count_query.where(IotCardModel.user_id == user_id)

        # 关键词搜索 (ICCID/MSISDN/短码)
        if keyword:
            keyword = keyword.strip().replace('%', '\\%').replace('_', '\\_')
            if len(keyword) <= 6:
                keyword_filter = self._build_short_iccid_keyword_filter(keyword)
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

        # 流量大小过滤
        if flow_size is not None:
            query = query.where(IotCardModel.flow_size == flow_size)
            count_query = count_query.where(IotCardModel.flow_size == flow_size)

        # 周期类型过滤
        if period_type:
            query = query.where(IotCardModel.period_type == period_type)
            count_query = count_query.where(IotCardModel.period_type == period_type)

        # 卡片类型过滤
        if card_type:
            query = query.where(IotCardModel.card_type == card_type)
            count_query = count_query.where(IotCardModel.card_type == card_type)

        # 流量池过滤
        if pool_id is not None:
            query = query.where(IotCardModel.pool_id == pool_id)
            count_query = count_query.where(IotCardModel.pool_id == pool_id)

        # 是否加入流量池
        if is_pool_member is not None:
            member_value = 1 if is_pool_member else 0
            query = query.where(IotCardModel.is_pool_member == member_value)
            count_query = count_query.where(IotCardModel.is_pool_member == member_value)

        # 超量卡过滤
        if over_usage is not None and over_usage:
            over_usage_filter = and_(
                IotCardModel.status.in_([CardStatus.activated, CardStatus.suspended]),
                IotCardModel.data_total > 0,
                IotCardModel.data_used > IotCardModel.data_total
            )
            query = query.where(over_usage_filter)
            count_query = count_query.where(over_usage_filter)

        # 备注模糊搜索
        if remark:
            if remark_user_id is not None:
                user_remark_filter = exists(
                    select(CardUserRemarkModel.id).where(
                        CardUserRemarkModel.card_id == IotCardModel.id,
                        CardUserRemarkModel.user_id == remark_user_id,
                        CardUserRemarkModel.is_deleted == 0,
                        CardUserRemarkModel.remark.like(f"%{remark}%")
                    )
                )
                remark_filter = user_remark_filter
            else:
                remark_filter = IotCardModel.remark.like(f"%{remark}%")
            query = query.where(remark_filter)
            count_query = count_query.where(remark_filter)

        # 关联客户过滤
        if customer_id is not None:
            query = query.where(IotCardModel.user_id == customer_id)
            count_query = count_query.where(IotCardModel.user_id == customer_id)

        # 出库单号/批次过滤
        if batch_id:
            batch_keyword = str(batch_id).strip()
            stock_out_no_filter = text("""
                EXISTS (
                    SELECT 1
                    FROM stock_out_record_cards sorc
                    INNER JOIN stock_out_records sor ON sorc.record_id = sor.id
                    WHERE sorc.card_id = iot_cards.id
                      AND sorc.is_deleted = 0
                      AND sor.is_deleted = 0
                      AND sor.record_no = :stock_out_record_no
                )
            """)
            if batch_keyword.isdigit():
                batch_filter = or_(IotCardModel.batch_id == int(batch_keyword), stock_out_no_filter)
            else:
                batch_filter = stock_out_no_filter
            query = query.where(batch_filter).params(stock_out_record_no=batch_keyword)
            count_query = count_query.where(batch_filter).params(stock_out_record_no=batch_keyword)

        # 项目过滤
        if project_id is not None:
            query = query.where(IotCardModel.project_id == project_id)
            count_query = count_query.where(IotCardModel.project_id == project_id)

        # 出库时间范围
        if stock_out_start:
            query = query.where(IotCardModel.stock_out_date >= stock_out_start)
            count_query = count_query.where(IotCardModel.stock_out_date >= stock_out_start)
        if stock_out_end:
            query = query.where(IotCardModel.stock_out_date <= stock_out_end)
            count_query = count_query.where(IotCardModel.stock_out_date <= stock_out_end)

        # 激活时间范围
        if activated_start:
            query = query.where(IotCardModel.activated_at >= activated_start)
            count_query = count_query.where(IotCardModel.activated_at >= activated_start)
        if activated_end:
            query = query.where(IotCardModel.activated_at <= activated_end)
            count_query = count_query.where(IotCardModel.activated_at <= activated_end)

        # 到期时间范围
        if expired_start:
            expiring_status_filter = IotCardModel.status.in_([
                CardStatus.activated,
                CardStatus.testing,
                CardStatus.silent,
            ])
            query = query.where(expiring_status_filter)
            count_query = count_query.where(expiring_status_filter)
            query = query.where(IotCardModel.expired_at >= expired_start)
            count_query = count_query.where(IotCardModel.expired_at >= expired_start)
        if expired_end:
            query = query.where(IotCardModel.expired_at <= expired_end)
            count_query = count_query.where(IotCardModel.expired_at <= expired_end)

        # 统计总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        sort_column = self.SORT_FIELD_MAP.get(sort_by or "", IotCardModel.id)
        sort_direction = (sort_order or "desc").lower()
        sort_expression = sort_column.asc() if sort_direction == "asc" else sort_column.desc()

        # 分页
        offset = (page - 1) * page_size
        query = query.order_by(
            sort_column.is_(None).asc(),
            sort_expression,
            IotCardModel.id.desc()
        ).offset(offset).limit(page_size)

        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def search(
        self,
        db: AsyncSession,
        keyword: str,
        user_id: Optional[int] = None,
        user_ids: Optional[List[int]] = None,
        limit: int = 10
    ) -> List[IotCardModel]:
        """快速搜索 (支持移动后6位、联通/电信后2位至后7位)"""
        keyword = keyword.strip()
        query = select(IotCardModel).where(IotCardModel.is_deleted == 0)

        if user_ids is not None:
            query = query.where(IotCardModel.user_id.in_(user_ids))
        elif user_id is not None:
            query = query.where(IotCardModel.user_id == user_id)

        if len(keyword) <= 6:
            query = query.where(self._build_short_iccid_keyword_filter(keyword))
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

    async def get_stats_in_scope(self, db: AsyncSession, user_ids: Optional[List[int]] = None) -> dict:
        """获取卡片统计（支持用户可见范围）"""
        query = select(
            IotCardModel.status,
            func.count(IotCardModel.id).label("count")
        ).where(IotCardModel.is_deleted == 0)

        if user_ids is not None:
            query = query.where(IotCardModel.user_id.in_(user_ids))

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
        user_id: Optional[int] = None,
        user_ids: Optional[List[int]] = None
    ) -> Optional[IotCardModel]:
        """更新卡片备注"""
        card = await self.get_by_id_in_scope(db, card_id, user_ids) if user_ids is not None else await self.get_by_id(db, card_id, user_id)
        if not card:
            return None
        card.remark = remark
        await db.commit()
        await db.refresh(card)
        return card

    async def get_user_remark_map(
        self,
        db: AsyncSession,
        card_ids: List[int],
        user_id: int
    ) -> Dict[int, str]:
        """获取指定用户在一组卡片上的备注"""
        if not card_ids:
            return {}

        result = await db.execute(
            select(CardUserRemarkModel.card_id, CardUserRemarkModel.remark).where(
                CardUserRemarkModel.card_id.in_(card_ids),
                CardUserRemarkModel.user_id == user_id,
                CardUserRemarkModel.is_deleted == 0
            )
        )
        return {
            card_id: remark
            for card_id, remark in result.all()
        }

    async def upsert_user_remark(
        self,
        db: AsyncSession,
        card_id: int,
        user_id: int,
        remark: str,
        source: str = "system"
    ) -> CardUserRemarkModel:
        """新增或更新用户侧卡片备注"""
        result = await db.execute(
            select(CardUserRemarkModel).where(
                CardUserRemarkModel.card_id == card_id,
                CardUserRemarkModel.user_id == user_id,
                CardUserRemarkModel.is_deleted == 0
            )
        )
        item = result.scalar_one_or_none()
        if item:
            item.remark = remark
            item.source = source
        else:
            item = CardUserRemarkModel(
                card_id=card_id,
                user_id=user_id,
                remark=remark,
                source=source
            )
            db.add(item)

        await db.flush()
        return item

    async def batch_update_remark(
        self,
        db: AsyncSession,
        card_ids: List[int],
        remark: str,
        user_id: Optional[int] = None,
        user_ids: Optional[List[int]] = None
    ) -> int:
        """批量更新备注"""
        count = 0
        for card_id in card_ids:
            card = await self.get_by_id_in_scope(db, card_id, user_ids) if user_ids is not None else await self.get_by_id(db, card_id, user_id)
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
        user_id: Optional[int] = None,
        user_ids: Optional[List[int]] = None
    ) -> List[IotCardModel]:
        """根据ID列表获取卡片"""
        query = select(IotCardModel).where(
            IotCardModel.id.in_(card_ids),
            IotCardModel.is_deleted == 0
        )
        if user_ids is not None:
            query = query.where(IotCardModel.user_id.in_(user_ids))
        elif user_id is not None:
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
        from_user_ids: Optional[List[int]] = None,
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

        if from_user_ids is not None:
            query = query.where(CardTransferModel.from_user_id.in_(from_user_ids))
            count_query = count_query.where(CardTransferModel.from_user_id.in_(from_user_ids))

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(CardTransferModel.id.desc()).offset(offset).limit(page_size)

        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total


class CardUsageHistoryCRUD:
    """卡片用量历史 CRUD"""

    async def create_snapshot(
        self,
        db: AsyncSession,
        card_id: int,
        iccid: str,
        data_used: int,
        data_total: int,
        period_type: str,
        snapshot_date,
        snapshot_type: str,
        snapshot_month: Optional[str] = None
    ):
        """创建或更新用量快照"""
        from app.db.models.iot_card import CardUsageHistoryModel
        existing_query = select(CardUsageHistoryModel).where(
            CardUsageHistoryModel.card_id == card_id,
            CardUsageHistoryModel.snapshot_type == snapshot_type,
            CardUsageHistoryModel.snapshot_date == snapshot_date
        )
        existing_result = await db.execute(existing_query)
        snapshot = existing_result.scalar_one_or_none()

        if snapshot:
            snapshot.iccid = iccid
            snapshot.data_used = data_used
            snapshot.data_total = data_total
            snapshot.period_type = period_type
            snapshot.snapshot_month = snapshot_month
        else:
            snapshot = CardUsageHistoryModel(
                card_id=card_id,
                iccid=iccid,
                data_used=data_used,
                data_total=data_total,
                period_type=period_type,
                snapshot_date=snapshot_date,
                snapshot_type=snapshot_type,
                snapshot_month=snapshot_month
            )
            db.add(snapshot)

        await db.flush()
        return snapshot

    async def get_card_history(
        self,
        db: AsyncSession,
        card_id: int,
        start_date=None,
        end_date=None
    ):
        """获取卡片历史记录"""
        from app.db.models.iot_card import CardUsageHistoryModel
        query = select(CardUsageHistoryModel).where(CardUsageHistoryModel.card_id == card_id)
        if start_date:
            query = query.where(CardUsageHistoryModel.snapshot_date >= start_date)
        if end_date:
            query = query.where(CardUsageHistoryModel.snapshot_date <= end_date)
        query = query.order_by(CardUsageHistoryModel.snapshot_date.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_cards_history(
        self,
        db: AsyncSession,
        card_ids: List[int],
        start_date=None,
        end_date=None
    ):
        """批量获取卡片历史记录"""
        from app.db.models.iot_card import CardUsageHistoryModel
        query = select(CardUsageHistoryModel).where(CardUsageHistoryModel.card_id.in_(card_ids))
        if start_date:
            query = query.where(CardUsageHistoryModel.snapshot_date >= start_date)
        if end_date:
            query = query.where(CardUsageHistoryModel.snapshot_date <= end_date)
        query = query.order_by(CardUsageHistoryModel.card_id, CardUsageHistoryModel.snapshot_date.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def prune_old_snapshots(
        self,
        db: AsyncSession,
        *,
        snapshot_type: str,
        before_date
    ) -> int:
        """删除指定日期之前的历史快照"""
        from app.db.models.iot_card import CardUsageHistoryModel

        result = await db.execute(
            delete(CardUsageHistoryModel).where(
                CardUsageHistoryModel.snapshot_type == snapshot_type,
                CardUsageHistoryModel.snapshot_date < before_date
            )
        )
        return result.rowcount or 0


iot_card_crud = IotCardCRUD()
card_transfer_crud = CardTransferCRUD()
card_usage_history_crud = CardUsageHistoryCRUD()
