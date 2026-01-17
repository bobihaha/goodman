"""
出入库管理 CRUD 操作
"""
from typing import Optional, List, Tuple
from datetime import datetime
import json
import uuid
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.stock import (
    PurchaseBatchModel, StockInRecordModel, StockOutRecordModel,
    BatchStatus, StockInStatus, StockOutStatus
)
from app.db.models.iot_card import IotCardModel, CardStatus
from app.db.models.package import SupplierPackageModel


def generate_batch_no() -> str:
    """生成批次号: B + 日期 + 4位随机"""
    return f"B{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:4].upper()}"


def generate_stock_in_no() -> str:
    """生成入库单号: IN + 日期 + 4位随机"""
    return f"IN{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:4].upper()}"


def generate_stock_out_no() -> str:
    """生成出库单号: OUT + 日期 + 4位随机"""
    return f"OUT{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:4].upper()}"


class PurchaseBatchCRUD:
    """采购批次 CRUD"""

    async def create(
        self,
        db: AsyncSession,
        supplier_id: int,
        package_id: int,
        carrier: str,
        flow_size: int,
        period_type: str,
        test_expire_date,
        silent_expire_date,
        purchase_date,
        created_by: int,
        remark: Optional[str] = None
    ) -> PurchaseBatchModel:
        """创建采购批次"""
        batch = PurchaseBatchModel(
            batch_no=generate_batch_no(),
            supplier_id=supplier_id,
            package_id=package_id,
            carrier=carrier,
            flow_size=flow_size,
            period_type=period_type,
            test_expire_date=test_expire_date,
            silent_expire_date=silent_expire_date,
            purchase_date=purchase_date,
            remark=remark,
            status=BatchStatus.pending,
            created_by=created_by
        )
        db.add(batch)
        await db.commit()
        await db.refresh(batch)
        return batch

    async def get_by_id(self, db: AsyncSession, batch_id: int) -> Optional[PurchaseBatchModel]:
        """根据ID获取批次"""
        query = select(PurchaseBatchModel).where(
            PurchaseBatchModel.id == batch_id,
            PurchaseBatchModel.is_deleted == 0
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        supplier_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[PurchaseBatchModel], int]:
        """获取批次列表"""
        query = select(PurchaseBatchModel).where(PurchaseBatchModel.is_deleted == 0)
        count_query = select(func.count(PurchaseBatchModel.id)).where(PurchaseBatchModel.is_deleted == 0)

        if supplier_id:
            query = query.where(PurchaseBatchModel.supplier_id == supplier_id)
            count_query = count_query.where(PurchaseBatchModel.supplier_id == supplier_id)

        if status:
            query = query.where(PurchaseBatchModel.status == status)
            count_query = count_query.where(PurchaseBatchModel.status == status)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(PurchaseBatchModel.id.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update_counts(self, db: AsyncSession, batch_id: int, stocked_delta: int = 0, out_delta: int = 0):
        """更新批次计数"""
        batch = await self.get_by_id(db, batch_id)
        if batch:
            if stocked_delta:
                batch.stocked_count += stocked_delta
                batch.card_count = batch.stocked_count
                if batch.status == BatchStatus.pending:
                    batch.status = BatchStatus.stocked
            if out_delta:
                batch.out_count += out_delta
                # 全部出库完成
                if batch.out_count >= batch.stocked_count:
                    batch.status = BatchStatus.completed
            await db.commit()


class StockInCRUD:
    """入库记录 CRUD"""

    async def create(
        self,
        db: AsyncSession,
        batch_id: int,
        cards: List[dict],
        created_by: int,
        remark: Optional[str] = None
    ) -> Tuple[StockInRecordModel, List[dict]]:
        """创建入库记录并导入卡片"""
        # 获取批次信息
        batch_query = select(PurchaseBatchModel).where(PurchaseBatchModel.id == batch_id)
        batch_result = await db.execute(batch_query)
        batch = batch_result.scalar_one_or_none()
        if not batch:
            raise ValueError("批次不存在")

        record = StockInRecordModel(
            record_no=generate_stock_in_no(),
            batch_id=batch_id,
            card_count=len(cards),
            import_data=json.dumps(cards, ensure_ascii=False),
            remark=remark,
            status=StockInStatus.confirmed,
            confirmed_at=datetime.now(),
            confirmed_by=created_by,
            created_by=created_by
        )

        success_count = 0
        fail_details = []

        for card_data in cards:
            iccid = card_data.get("iccid", "").strip()
            imsi = card_data.get("imsi", "").strip() if card_data.get("imsi") else None
            msisdn = card_data.get("msisdn", "").strip() if card_data.get("msisdn") else None

            # 检查ICCID是否已存在
            exist_query = select(IotCardModel).where(IotCardModel.iccid == iccid)
            exist_result = await db.execute(exist_query)
            if exist_result.scalar_one_or_none():
                fail_details.append({"iccid": iccid, "reason": "ICCID已存在"})
                continue

            # 创建卡片
            card = IotCardModel(
                iccid=iccid,
                imsi=imsi,
                msisdn=msisdn,
                supplier_id=batch.supplier_id,
                batch_id=batch_id,
                carrier=batch.carrier,
                flow_size=batch.flow_size,
                period_type=batch.period_type,
                test_expire_date=batch.test_expire_date,
                silent_expire_date=batch.silent_expire_date,
                data_used=0,
                data_total=batch.flow_size,
                status=CardStatus.stock,
                stock_in_at=datetime.now(),
                created_by=created_by
            )
            db.add(card)
            success_count += 1

        record.success_count = success_count
        record.fail_count = len(cards) - success_count
        record.fail_reason = json.dumps(fail_details, ensure_ascii=False) if fail_details else None

        db.add(record)
        await db.commit()
        await db.refresh(record)

        # 更新批次计数
        batch_crud = PurchaseBatchCRUD()
        await batch_crud.update_counts(db, batch_id, stocked_delta=success_count)

        return record, fail_details

    async def get_list(
        self,
        db: AsyncSession,
        batch_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[StockInRecordModel], int]:
        """获取入库记录列表"""
        query = select(StockInRecordModel).where(StockInRecordModel.is_deleted == 0)
        count_query = select(func.count(StockInRecordModel.id)).where(StockInRecordModel.is_deleted == 0)

        if batch_id:
            query = query.where(StockInRecordModel.batch_id == batch_id)
            count_query = count_query.where(StockInRecordModel.batch_id == batch_id)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(StockInRecordModel.id.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total


class StockOutCRUD:
    """出库记录 CRUD"""

    async def create(
        self,
        db: AsyncSession,
        card_ids: List[int],
        to_user_id: int,
        sale_package_id: int,
        created_by: int,
        remark: Optional[str] = None
    ) -> Tuple[StockOutRecordModel, int, int]:
        """创建出库记录"""
        record = StockOutRecordModel(
            record_no=generate_stock_out_no(),
            to_user_id=to_user_id,
            sale_package_id=sale_package_id,
            card_count=len(card_ids),
            card_ids=json.dumps(card_ids),
            remark=remark,
            status=StockOutStatus.confirmed,
            confirmed_at=datetime.now(),
            confirmed_by=created_by,
            created_by=created_by
        )

        success_count = 0
        batch_updates = {}

        for card_id in card_ids:
            # 获取卡片
            card_query = select(IotCardModel).where(
                IotCardModel.id == card_id,
                IotCardModel.status == CardStatus.stock,
                IotCardModel.user_id.is_(None),
                IotCardModel.is_deleted == 0
            )
            card_result = await db.execute(card_query)
            card = card_result.scalar_one_or_none()

            if card:
                card.user_id = to_user_id
                card.sale_package_id = sale_package_id
                card.status = CardStatus.silent  # 出库后进入沉默期
                card.stock_out_at = datetime.now()
                success_count += 1

                # 统计批次出库数
                if card.batch_id:
                    batch_updates[card.batch_id] = batch_updates.get(card.batch_id, 0) + 1

        db.add(record)
        await db.commit()
        await db.refresh(record)

        # 更新批次计数
        batch_crud = PurchaseBatchCRUD()
        for batch_id, count in batch_updates.items():
            await batch_crud.update_counts(db, batch_id, out_delta=count)

        return record, success_count, len(card_ids) - success_count

    async def get_list(
        self,
        db: AsyncSession,
        to_user_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[StockOutRecordModel], int]:
        """获取出库记录列表"""
        query = select(StockOutRecordModel).where(StockOutRecordModel.is_deleted == 0)
        count_query = select(func.count(StockOutRecordModel.id)).where(StockOutRecordModel.is_deleted == 0)

        if to_user_id:
            query = query.where(StockOutRecordModel.to_user_id == to_user_id)
            count_query = count_query.where(StockOutRecordModel.to_user_id == to_user_id)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(StockOutRecordModel.id.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total


class StockSummaryCRUD:
    """库存统计 CRUD"""

    async def get_summary(self, db: AsyncSession) -> dict:
        """获取库存统计"""
        # 总卡数 (库存中的)
        stock_query = select(func.count(IotCardModel.id)).where(
            IotCardModel.status == CardStatus.stock,
            IotCardModel.user_id.is_(None),
            IotCardModel.is_deleted == 0
        )
        stock_result = await db.execute(stock_query)
        stock_cards = stock_result.scalar() or 0

        # 已出库数
        out_query = select(func.count(IotCardModel.id)).where(
            IotCardModel.user_id.isnot(None),
            IotCardModel.is_deleted == 0
        )
        out_result = await db.execute(out_query)
        out_cards = out_result.scalar() or 0

        # 按运营商统计
        carrier_query = select(
            IotCardModel.carrier,
            func.count(IotCardModel.id)
        ).where(
            IotCardModel.status == CardStatus.stock,
            IotCardModel.is_deleted == 0
        ).group_by(IotCardModel.carrier)
        carrier_result = await db.execute(carrier_query)
        by_carrier = {row[0].value if hasattr(row[0], 'value') else row[0]: row[1] for row in carrier_result.all()}

        return {
            "total_cards": stock_cards + out_cards,
            "stock_cards": stock_cards,
            "out_cards": out_cards,
            "by_carrier": by_carrier
        }

    async def get_inventory(
        self,
        db: AsyncSession,
        supplier_id: Optional[int] = None,
        carrier: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[IotCardModel], int]:
        """获取库存卡片列表"""
        query = select(IotCardModel).where(
            IotCardModel.status == CardStatus.stock,
            IotCardModel.user_id.is_(None),
            IotCardModel.is_deleted == 0
        )
        count_query = select(func.count(IotCardModel.id)).where(
            IotCardModel.status == CardStatus.stock,
            IotCardModel.user_id.is_(None),
            IotCardModel.is_deleted == 0
        )

        if supplier_id:
            query = query.where(IotCardModel.supplier_id == supplier_id)
            count_query = count_query.where(IotCardModel.supplier_id == supplier_id)

        if carrier:
            query = query.where(IotCardModel.carrier == carrier)
            count_query = count_query.where(IotCardModel.carrier == carrier)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(IotCardModel.id.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total


batch_crud = PurchaseBatchCRUD()
stock_in_crud = StockInCRUD()
stock_out_crud = StockOutCRUD()
stock_summary_crud = StockSummaryCRUD()
