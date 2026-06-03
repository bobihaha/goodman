"""
出入库管理 CRUD 操作
"""
from typing import Optional, List, Tuple, Set
from datetime import datetime
import json
import uuid
import logging
from sqlalchemy import select, func, update, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.stock import (
    PurchaseBatchModel, StockInRecordModel, StockOutRecordModel,
    BatchStatus, StockInStatus, StockOutStatus
)
from app.db.models.iot_card import IotCardModel, CardStatus, SuspendType
from app.db.models.package import SupplierPackageModel

logger = logging.getLogger(__name__)


def generate_batch_no() -> str:
    """生成批次号: B + 日期 + 8位随机"""
    return f"B{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"


def generate_stock_in_no() -> str:
    """生成入库单号: IN + 日期 + 8位随机"""
    return f"IN{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"


def generate_stock_out_no() -> str:
    """生成出库单号: OUT + 日期 + 8位随机"""
    return f"OUT{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"


def _format_package_period(period_type: Optional[str], period_months: Optional[int] = None, period_days: Optional[int] = None) -> Optional[str]:
    """格式化套餐定义周期展示。"""
    if period_type == "monthly":
        if period_months:
            return f"{int(period_months)}个月"
        return "月包"
    if period_type == "yearly":
        if period_days and int(period_days) % 360 == 0:
            years = int(period_days) // 360
            return f"{years}年"
        if period_days:
            return f"{int(period_days)}天"
        return "年包"
    return None


def _format_period_count(period_type: Optional[str], period_count: Optional[int]) -> Optional[str]:
    """格式化按周期类型记录的周期数量展示。"""
    if not period_count:
        return None
    if period_type == "yearly":
        return f"{int(period_count)}年"
    return f"{int(period_count)}个月"


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
        package_period_count: Optional[int],
        material: Optional[str],
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
            package_period_count=package_period_count,
            material=material,
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

    async def update_counts(
        self,
        db: AsyncSession,
        batch_id: int,
        stocked_delta: int = 0,
        out_delta: int = 0,
        commit: bool = True
    ):
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
            if commit:
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
        from app.db.models.stock import StockInRecordCardModel
        from sqlalchemy import text
        from app.utils.const import validate_iccid

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
        created_card_ids = []
        valid_cards = []
        seen_iccids = set()

        # 预验证所有卡片，允许部分成功并记录失败明细
        for card_data in cards:
            iccid = card_data.get("iccid", "").strip()
            imsi = card_data.get("imsi", "").strip() if card_data.get("imsi") else None
            msisdn = card_data.get("msisdn", "").strip() if card_data.get("msisdn") else None

            if not iccid:
                fail_details.append({"iccid": iccid, "reason": "ICCID不能为空"})
                continue

            if iccid in seen_iccids:
                fail_details.append({"iccid": iccid, "reason": "导入列表中存在重复ICCID"})
                continue
            seen_iccids.add(iccid)

            if not validate_iccid(iccid):
                fail_details.append({"iccid": iccid, "reason": "ICCID格式错误(需19-20位字母或数字)"})
                continue

            exist_query = select(IotCardModel.id).where(IotCardModel.iccid == iccid)
            exist_result = await db.execute(exist_query)
            if exist_result.scalar_one_or_none():
                fail_details.append({"iccid": iccid, "reason": "ICCID已存在"})
                continue

            valid_cards.append({
                "iccid": iccid,
                "imsi": imsi,
                "msisdn": msisdn
            })

        # 批量创建有效卡片
        for card_data in valid_cards:
            iccid = card_data["iccid"]
            imsi = card_data["imsi"]
            msisdn = card_data["msisdn"]

            # 创建卡片
            card = IotCardModel(
                iccid=iccid,
                iccid_suffix=iccid[-6:] if len(iccid) >= 6 else iccid,
                imsi=imsi,
                msisdn=msisdn,
                supplier_id=batch.supplier_id,
                batch_id=batch_id,
                carrier=batch.carrier,
                flow_size=batch.flow_size,
                period_type=batch.period_type,
                material=batch.material,
                test_expire_date=batch.test_expire_date,
                silent_expire_date=batch.silent_expire_date,
                data_used=0,
                data_total=batch.flow_size,
                status=CardStatus.stock,
                stock_in_at=datetime.now(),
                created_by=created_by
            )
            db.add(card)
            await db.flush()  # 获取card.id
            created_card_ids.append({"card_id": card.id, "iccid": card.iccid})
            success_count += 1

        record.success_count = success_count
        record.fail_count = len(fail_details)
        record.fail_reason = json.dumps(fail_details, ensure_ascii=False) if fail_details else None

        db.add(record)
        await db.flush()  # 获取record.id
        
        # 创建新表记录（stock_in_records）
        new_record_sql = """
            INSERT INTO stock_in_records 
            (supplier_id, package_id, test_expire_date, silent_expire_date,
             package_period_count,
             record_no, batch_id, card_count, success_count, failed_count,
             remark, operator_id, created_at, updated_at)
            VALUES 
            (:supplier_id, :package_id, :test_expire_date, :silent_expire_date,
             :package_period_count,
             :record_no, :batch_id, :card_count, :success_count, :failed_count,
             :remark, :operator_id, NOW(), NOW())
        """
        new_record_result = await db.execute(text(new_record_sql), {
            "supplier_id": batch.supplier_id,
            "package_id": batch.package_id,
            "test_expire_date": batch.test_expire_date,
            "silent_expire_date": batch.silent_expire_date,
            "package_period_count": batch.package_period_count,
            "record_no": record.record_no,
            "batch_id": batch_id,
            "card_count": len(cards),
            "success_count": success_count,
            "failed_count": len(fail_details),
            "remark": remark,
            "operator_id": created_by
        })
        new_record_id = new_record_result.lastrowid

        # 获取供应商和套餐信息
        from app.db.models.supplier import SupplierModel
        supplier_query = select(SupplierModel).where(SupplierModel.id == batch.supplier_id)
        supplier_result = await db.execute(supplier_query)
        supplier = supplier_result.scalar_one_or_none()

        package_query = select(SupplierPackageModel).where(SupplierPackageModel.id == batch.package_id)
        package_result = await db.execute(package_query)
        package = package_result.scalar_one_or_none()

        # 创建卡片关联记录
        for card_info in created_card_ids:
            relation = StockInRecordCardModel(
                record_id=new_record_id,
                card_id=card_info["card_id"],
                iccid=card_info["iccid"],
                test_expire_date=batch.test_expire_date,
                silent_expire_date=batch.silent_expire_date,
                supplier_id=batch.supplier_id,
                supplier_name=supplier.name if supplier else None,
                base_package_id=batch.package_id,
                base_package_name=package.name if package else None
            )
            db.add(relation)

        # 更新批次计数（在同一事务内）
        if success_count > 0:
            await batch_crud.update_counts(db, batch_id, stocked_delta=success_count, commit=False)

        await db.commit()
        await db.refresh(record)

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
        period_count: int,
        card_type: Optional[str],
        stock_out_date,
        test_expire_date,
        silent_expire_date,
        created_by: int,
        remark: Optional[str] = None
    ) -> Tuple[StockOutRecordModel, int, int]:
        """创建出库记录"""
        from app.db.models.stock import StockOutRecordCardModel
        from app.db.models.package import SalePackageModel
        from sqlalchemy import text

        sale_pkg_query = select(SalePackageModel).where(SalePackageModel.id == sale_package_id)
        sale_pkg_result = await db.execute(sale_pkg_query)
        sale_pkg = sale_pkg_result.scalar_one_or_none()
        if not sale_pkg:
            raise ValueError("销售套餐不存在")
        
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
        out_card_infos = []  # 记录成功出库的卡片信息
        first_card_spec = {
            "carrier": sale_pkg.carrier.value if sale_pkg.carrier else None,
            "flow_size": sale_pkg.flow_size,
            "period_type": sale_pkg.period_type.value if sale_pkg.period_type else None,
        }

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
                card.period_count = period_count
                # 重新出库时重置上一轮生命周期，避免沿用历史激活/到期状态
                card.activated_at = None
                card.expired_at = None
                card.suspend_type = SuspendType.none
                card.suspend_at = None
                card.suspend_reason = None
                # 出库后规格以销售套餐为准，而不是采购入库规格
                card.carrier = sale_pkg.carrier
                card.flow_size = sale_pkg.flow_size
                card.period_type = sale_pkg.period_type
                card.data_total = sale_pkg.flow_size
                # 设置卡类型（如果提供）
                if card_type:
                    from app.db.models.iot_card import CardType
                    card.card_type = CardType(card_type)
                # 设置日期
                card.stock_out_date = stock_out_date
                card.test_expire_date = test_expire_date
                card.silent_expire_date = silent_expire_date

                # 根据运营商类型设置初始状态
                from app.db.models.package import CarrierType
                if sale_pkg.carrier == CarrierType.cmcc and test_expire_date:
                    card.status = CardStatus.testing
                else:
                    card.status = CardStatus.silent

                card.stock_out_at = datetime.now()
                success_count += 1
                out_card_infos.append({"card_id": card.id, "iccid": card.iccid})

                # 统计批次出库数
                if card.batch_id:
                    batch_updates[card.batch_id] = batch_updates.get(card.batch_id, 0) + 1

        db.add(record)
        await db.flush()  # 获取record.id

        # 获取销售套餐价格信息（价格单位：元，需要转换为分）
        sale_package_query = text("SELECT price_sale FROM sale_packages WHERE id = :package_id")
        sale_package_result = await db.execute(sale_package_query, {"package_id": sale_package_id})
        sale_package_row = sale_package_result.fetchone()
        unit_price = int(sale_package_row.price_sale * 100) if sale_package_row and sale_package_row.price_sale else 0
        total_amount = unit_price * success_count

        # 记录套餐单价到已出库的卡片（用于续费价格锁定）
        if sale_package_row and sale_package_row.price_sale:
            sale_price_decimal = sale_package_row.price_sale
            for card_id in card_ids:
                await db.execute(
                    text("UPDATE iot_cards SET sale_price = :sale_price WHERE id = :card_id"),
                    {"sale_price": sale_price_decimal, "card_id": card_id}
                )
        
        # 创建新表记录（stock_out_records）
        new_record_sql = """
            INSERT INTO stock_out_records 
            (user_id, to_user_id, record_no, sale_package_id, card_count, success_count, failed_count,
             unit_price, total_amount, remark, operator_id, created_at, updated_at)
            VALUES 
            (:user_id, :to_user_id, :record_no, :sale_package_id, :card_count, :success_count, :failed_count,
             :unit_price, :total_amount, :remark, :operator_id, NOW(), NOW())
        """
        new_record_result = await db.execute(text(new_record_sql), {
            "user_id": to_user_id,
            "to_user_id": to_user_id,
            "record_no": record.record_no,
            "sale_package_id": sale_package_id,
            "card_count": len(card_ids),
            "success_count": success_count,
            "failed_count": len(card_ids) - success_count,
            "unit_price": unit_price,
            "total_amount": total_amount,
            "remark": remark,
            "operator_id": created_by
        })
        new_record_id = new_record_result.lastrowid

        # 获取用户、销售套餐、供应商、底层套餐信息
        from app.db.models.sys_user import SysUserModel
        from app.db.models.package import SalePackageModel
        from app.db.models.supplier import SupplierModel

        user_query = select(SysUserModel).where(SysUserModel.id == to_user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        # 创建卡片关联记录
        for card_info in out_card_infos:
            # 获取卡片详细信息
            card_query = select(IotCardModel).where(IotCardModel.id == card_info["card_id"])
            card_result = await db.execute(card_query)
            card = card_result.scalar_one_or_none()

            if card:
                # 获取供应商和底层套餐
                supplier_query = select(SupplierModel).where(SupplierModel.id == card.supplier_id)
                supplier_result = await db.execute(supplier_query)
                supplier = supplier_result.scalar_one_or_none()

                base_pkg_query = select(SupplierPackageModel).where(SupplierPackageModel.id == card.batch_id)
                base_pkg_result = await db.execute(base_pkg_query)
                base_pkg = base_pkg_result.scalar_one_or_none()

                # 如果找不到底层套餐，尝试从批次获取
                if not base_pkg and card.batch_id:
                    batch_query = select(PurchaseBatchModel).where(PurchaseBatchModel.id == card.batch_id)
                    batch_result = await db.execute(batch_query)
                    batch = batch_result.scalar_one_or_none()
                    if batch:
                        base_pkg_query = select(SupplierPackageModel).where(SupplierPackageModel.id == batch.package_id)
                        base_pkg_result = await db.execute(base_pkg_query)
                        base_pkg = base_pkg_result.scalar_one_or_none()

                relation = StockOutRecordCardModel(
                    record_id=new_record_id,
                    card_id=card_info["card_id"],
                    iccid=card_info["iccid"],
                    test_expire_date=card.test_expire_date,
                    silent_expire_date=card.silent_expire_date,
                    supplier_id=card.supplier_id,
                    supplier_name=supplier.name if supplier else None,
                    base_package_id=base_pkg.id if base_pkg else None,
                    base_package_name=base_pkg.name if base_pkg else None,
                    sale_package_id=sale_package_id,
                    sale_package_name=sale_pkg.name if sale_pkg else None,
                    target_user_id=to_user_id,
                    target_user_name=user.name if user else None
                )
                db.add(relation)
        
        await db.commit()
        await db.refresh(record)

        # 更新批次计数
        for batch_id, count in batch_updates.items():
            await batch_crud.update_counts(db, batch_id, out_delta=count)

        # 如果是流量池卡，预创建流量池并将卡片加入
        if card_type == "pool" and success_count > 0 and first_card_spec:
            try:
                from app.crud.pool_crud import pool_crud
                pool = await pool_crud.find_or_create_pool(
                    db=db,
                    user_id=to_user_id,
                    carrier=first_card_spec["carrier"],
                    flow_size=first_card_spec["flow_size"],
                    period_type=first_card_spec["period_type"],
                    created_by=created_by,
                    sale_package_id=sale_package_id
                )
                # 将出库的卡片加入流量池
                if pool:
                    out_card_ids = [info["card_id"] for info in out_card_infos]
                    await db.execute(
                        IotCardModel.__table__.update()
                        .where(IotCardModel.id.in_(out_card_ids))
                        .values(pool_id=pool.id, is_pool_member=1)
                    )
                    await db.commit()
                    await pool_crud.update_stats(db, pool.id)
            except Exception as e:
                await db.rollback()
                import traceback
                print(f"出库预创建流量池失败: {str(e)}")
                traceback.print_exc()

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

    @staticmethod
    def _parse_iccid_query(iccids: List[str]) -> Tuple[List[str], List[str]]:
        normalized = []
        seen = set()
        duplicates = []
        for item in iccids:
            iccid = (item or "").strip()
            if not iccid:
                continue
            if iccid in seen:
                duplicates.append(iccid)
                continue
            seen.add(iccid)
            normalized.append(iccid)
        return normalized, duplicates

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
        package_id: Optional[int] = None,
        sort_by: str = "stock_in_at",
        sort_order: str = "desc",
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

        if package_id:
            # 通过批次关联套餐
            query = query.join(PurchaseBatchModel, IotCardModel.batch_id == PurchaseBatchModel.id)
            query = query.where(PurchaseBatchModel.package_id == package_id)
            count_query = count_query.join(PurchaseBatchModel, IotCardModel.batch_id == PurchaseBatchModel.id)
            count_query = count_query.where(PurchaseBatchModel.package_id == package_id)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 排序
        if sort_by == "stock_in_at":
            order_col = IotCardModel.stock_in_at
        elif sort_by == "test_expire_date":
            order_col = IotCardModel.test_expire_date
        elif sort_by == "silent_expire_date":
            order_col = IotCardModel.silent_expire_date
        else:
            order_col = IotCardModel.stock_in_at

        if sort_order == "asc":
            query = query.order_by(order_col.asc())
        else:
            query = query.order_by(order_col.desc())

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def batch_query_cards(self, db: AsyncSession, iccids: List[str]) -> dict:
        """批量查询库存卡片"""
        normalized_iccids, duplicate_iccids = self._parse_iccid_query(iccids)

        query = select(IotCardModel).where(
            IotCardModel.iccid.in_(normalized_iccids),
            IotCardModel.status == CardStatus.stock,
            IotCardModel.user_id.is_(None),
            IotCardModel.is_deleted == 0
        )
        result = await db.execute(query)
        found_cards = list(result.scalars().all())
        
        found_iccids = {card.iccid for card in found_cards}
        not_found = [iccid for iccid in normalized_iccids if iccid not in found_iccids]
        found_data = [card.to_dict() for card in found_cards]
        
        return {
            "found": found_data,
            "not_found": not_found,
            "duplicate_iccids": duplicate_iccids
        }

    async def export_inventory(
        self,
        db: AsyncSession,
        supplier_id: Optional[int] = None,
        carrier: Optional[str] = None,
        package_id: Optional[int] = None,
        iccids: Optional[List[str]] = None,
        sort_by: str = "stock_in_at",
        sort_order: str = "desc"
    ) -> List[dict]:
        """导出库存数据（不分页）"""
        query = select(IotCardModel).where(
            IotCardModel.status == CardStatus.stock,
            IotCardModel.user_id.is_(None),
            IotCardModel.is_deleted == 0
        )

        if supplier_id:
            query = query.where(IotCardModel.supplier_id == supplier_id)
        if carrier:
            query = query.where(IotCardModel.carrier == carrier)
        if package_id:
            query = query.join(PurchaseBatchModel, IotCardModel.batch_id == PurchaseBatchModel.id)
            query = query.where(PurchaseBatchModel.package_id == package_id)
        if iccids:
            query = query.where(IotCardModel.iccid.in_(iccids))

        # 排序
        if sort_by == "stock_in_at":
            order_col = IotCardModel.stock_in_at
        elif sort_by == "test_expire_date":
            order_col = IotCardModel.test_expire_date
        elif sort_by == "silent_expire_date":
            order_col = IotCardModel.silent_expire_date
        else:
            order_col = IotCardModel.stock_in_at

        if sort_order == "asc":
            query = query.order_by(order_col.asc())
        else:
            query = query.order_by(order_col.desc())

        result = await db.execute(query)
        items = list(result.scalars().all())
        
        return [item.to_dict() for item in items]


# ============ 新增：入库记录扩展 CRUD ============

class StockInRecordCRUD:
    """入库记录扩展 CRUD"""

    async def get_records_list(
        self,
        db: AsyncSession,
        supplier_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取入库记录列表（带关联信息）"""
        from sqlalchemy import text
        
        # 构建WHERE条件
        where_conditions = ["sir.is_deleted = 0"]
        params = {}
        
        if supplier_id:
            where_conditions.append("sir.supplier_id = :supplier_id")
            params["supplier_id"] = supplier_id
        
        if start_date:
            where_conditions.append("sir.created_at >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            where_conditions.append("sir.created_at <= :end_date")
            params["end_date"] = f"{end_date} 23:59:59"
        
        where_clause = " AND ".join(where_conditions)
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) FROM stock_in_records sir WHERE {where_clause}"
        count_result = await db.execute(text(count_sql), params)
        total = count_result.scalar() or 0
        
        # 查询数据
        offset = (page - 1) * page_size
        params["offset"] = offset
        params["limit"] = page_size
        
        query_sql = f"""
            SELECT 
                sir.id, sir.supplier_id, sir.package_id,
                sir.test_expire_date, sir.silent_expire_date,
                sir.package_period_count,
                sir.card_count, sir.success_count, sir.failed_count,
                sir.remark, sir.operator_id, sir.created_at,
                s.name as supplier_name,
                sp.name as package_name,
                sp.period_type,
                u.name as operator_name
            FROM stock_in_records sir
            LEFT JOIN suppliers s ON sir.supplier_id = s.id
            LEFT JOIN supplier_packages sp ON sir.package_id = sp.id
            LEFT JOIN sys_users u ON sir.operator_id = u.id
            WHERE {where_clause}
            ORDER BY sir.id DESC
            LIMIT :limit OFFSET :offset
        """
        
        result = await db.execute(text(query_sql), params)
        rows = result.fetchall()
        
        items = []
        for row in rows:
            items.append({
                "id": row.id,
                "supplier_id": row.supplier_id,
                "supplier_name": row.supplier_name,
                "package_id": row.package_id,
                "package_name": row.package_name,
                "package_period_count": row.package_period_count,
                "package_period": _format_period_count(row.period_type, row.package_period_count),
                "test_expire_date": row.test_expire_date.strftime("%Y-%m-%d") if row.test_expire_date else None,
                "silent_expire_date": row.silent_expire_date.strftime("%Y-%m-%d") if row.silent_expire_date else None,
                "card_count": row.card_count,
                "success_count": row.success_count,
                "failed_count": row.failed_count,
                "remark": row.remark,
                "operator_id": row.operator_id,
                "operator_name": row.operator_name,
                "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else None,
            })
        
        return items, total

    async def get_record_detail(self, db: AsyncSession, record_id: int) -> Optional[dict]:
        """获取入库记录详情"""
        from sqlalchemy import text
        from app.db.models.iot_card import CARD_STATUS_NAMES
        
        query_sql = """
            SELECT 
                sir.id, sir.supplier_id, sir.package_id,
                sir.test_expire_date, sir.silent_expire_date,
                sir.package_period_count,
                sir.card_count, sir.success_count, sir.failed_count,
                sir.remark, sir.operator_id, sir.created_at,
                s.name as supplier_name,
                sp.name as package_name,
                sp.period_type,
                u.name as operator_name
            FROM stock_in_records sir
            LEFT JOIN suppliers s ON sir.supplier_id = s.id
            LEFT JOIN supplier_packages sp ON sir.package_id = sp.id
            LEFT JOIN sys_users u ON sir.operator_id = u.id
            WHERE sir.id = :record_id AND sir.is_deleted = 0
        """
        
        result = await db.execute(text(query_sql), {"record_id": record_id})
        row = result.fetchone()
        
        if not row:
            return None
        
        # 查询关联的卡片列表
        cards_sql = """
            SELECT c.id, c.iccid, c.imsi, c.msisdn, c.status
            FROM stock_in_record_cards rc
            LEFT JOIN iot_cards c ON rc.card_id = c.id
            WHERE rc.record_id = :record_id
            ORDER BY rc.id ASC
        """
        cards_result = await db.execute(text(cards_sql), {"record_id": record_id})
        cards_rows = cards_result.fetchall()
        
        cards = []
        for card_row in cards_rows:
            cards.append({
                "id": card_row.id,
                "iccid": card_row.iccid,
                "imsi": card_row.imsi,
                "msisdn": card_row.msisdn,
                "status": card_row.status,
                "status_name": CARD_STATUS_NAMES.get(card_row.status, card_row.status)
            })
        
        data = {
            "id": row.id,
            "supplier_id": row.supplier_id,
            "supplier_name": row.supplier_name,
            "package_id": row.package_id,
            "package_name": row.package_name,
            "package_period_count": row.package_period_count,
            "package_period": _format_period_count(row.period_type, row.package_period_count),
            "test_expire_date": row.test_expire_date.strftime("%Y-%m-%d") if row.test_expire_date else None,
            "silent_expire_date": row.silent_expire_date.strftime("%Y-%m-%d") if row.silent_expire_date else None,
            "card_count": row.card_count,
            "success_count": row.success_count,
            "failed_count": row.failed_count,
            "remark": row.remark,
            "operator_id": row.operator_id,
            "operator_name": row.operator_name,
            "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else None,
            "cards": cards
        }
        
        return data

    async def export_records(
        self,
        db: AsyncSession,
        supplier_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """导出入库记录"""
        items, _ = await self.get_records_list(
            db=db,
            supplier_id=supplier_id,
            start_date=start_date,
            end_date=end_date,
            page=1,
            page_size=10000  # 导出时获取所有数据
        )
        return items


# ============ 新增：出库记录扩展 CRUD ============

class StockOutRecordCRUD:
    """出库记录扩展 CRUD"""

    async def get_records_list(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取出库记录列表（带关联信息）"""
        from sqlalchemy import text
        
        # 构建WHERE条件
        where_conditions = ["sor.is_deleted = 0"]
        params = {}
        
        if user_id:
            where_conditions.append("sor.user_id = :user_id")
            params["user_id"] = user_id
        
        if start_date:
            where_conditions.append("sor.created_at >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            where_conditions.append("sor.created_at <= :end_date")
            params["end_date"] = f"{end_date} 23:59:59"
        
        where_clause = " AND ".join(where_conditions)
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) FROM stock_out_records sor WHERE {where_clause}"
        count_result = await db.execute(text(count_sql), params)
        total = count_result.scalar() or 0
        
        # 查询数据
        offset = (page - 1) * page_size
        params["offset"] = offset
        params["limit"] = page_size
        
        query_sql = f"""
            SELECT 
                sor.id, sor.user_id, sor.to_user_id, sor.record_no, sor.sale_package_id,
                sor.card_count, sor.success_count, sor.failed_count,
                sor.unit_price, sor.total_amount,
                sor.remark, sor.operator_id, sor.created_at,
                u.name as user_name,
                sp.name as sale_package_name,
                sp.period_type,
                period_stats.period_count,
                op.name as operator_name
            FROM stock_out_records sor
            LEFT JOIN sys_users u ON sor.user_id = u.id
            LEFT JOIN sale_packages sp ON sor.sale_package_id = sp.id
            LEFT JOIN (
                SELECT rc.record_id, MIN(c.period_count) AS period_count
                FROM stock_out_record_cards rc
                LEFT JOIN iot_cards c ON rc.card_id = c.id
                WHERE rc.is_deleted = 0
                GROUP BY rc.record_id
            ) period_stats ON period_stats.record_id = sor.id
            LEFT JOIN sys_users op ON sor.operator_id = op.id
            WHERE {where_clause}
            ORDER BY sor.id DESC
            LIMIT :limit OFFSET :offset
        """
        
        result = await db.execute(text(query_sql), params)
        rows = result.fetchall()
        
        items = []
        for row in rows:
            items.append({
                "id": row.id,
                "user_id": row.user_id,
                "to_user_id": row.to_user_id,
                "record_no": row.record_no,
                "user_name": row.user_name,
                "sale_package_id": row.sale_package_id,
                "sale_package_name": row.sale_package_name,
                "package_period": _format_package_period(row.period_type),
                "actual_period": _format_period_count(row.period_type, row.period_count),
                "card_count": row.card_count,
                "success_count": row.success_count,
                "failed_count": row.failed_count,
                "unit_price": row.unit_price / 100 if row.unit_price else 0,
                "total_amount": row.total_amount / 100 if row.total_amount else 0,
                "remark": row.remark,
                "operator_id": row.operator_id,
                "operator_name": row.operator_name,
                "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else None,
            })
        
        return items, total

    async def get_record_detail(self, db: AsyncSession, record_id: int) -> Optional[dict]:
        """获取出库记录详情"""
        from sqlalchemy import text
        from app.db.models.iot_card import CARD_STATUS_NAMES
        
        query_sql = """
            SELECT 
                sor.id, sor.user_id, sor.to_user_id, sor.record_no, sor.sale_package_id,
                sor.card_count, sor.success_count, sor.failed_count,
                sor.unit_price, sor.total_amount,
                sor.remark, sor.operator_id, sor.created_at,
                u.name as user_name,
                sp.name as sale_package_name,
                sp.period_type,
                period_stats.period_count,
                op.name as operator_name
            FROM stock_out_records sor
            LEFT JOIN sys_users u ON sor.user_id = u.id
            LEFT JOIN sale_packages sp ON sor.sale_package_id = sp.id
            LEFT JOIN (
                SELECT rc.record_id, MIN(c.period_count) AS period_count
                FROM stock_out_record_cards rc
                LEFT JOIN iot_cards c ON rc.card_id = c.id
                WHERE rc.is_deleted = 0
                GROUP BY rc.record_id
            ) period_stats ON period_stats.record_id = sor.id
            LEFT JOIN sys_users op ON sor.operator_id = op.id
            WHERE sor.id = :record_id AND sor.is_deleted = 0
        """
        
        result = await db.execute(text(query_sql), {"record_id": record_id})
        row = result.fetchone()
        
        if not row:
            return None
        
        # 查询关联的卡片列表
        cards_sql = """
            SELECT c.id, c.iccid, c.imsi, c.msisdn, c.status
            FROM stock_out_record_cards rc
            LEFT JOIN iot_cards c ON rc.card_id = c.id
            WHERE rc.record_id = :record_id
            ORDER BY rc.id ASC
        """
        cards_result = await db.execute(text(cards_sql), {"record_id": record_id})
        cards_rows = cards_result.fetchall()
        
        cards = []
        for card_row in cards_rows:
            cards.append({
                "id": card_row.id,
                "iccid": card_row.iccid,
                "imsi": card_row.imsi,
                "msisdn": card_row.msisdn,
                "status": card_row.status,
                "status_name": CARD_STATUS_NAMES.get(card_row.status, card_row.status)
            })
        
        data = {
            "id": row.id,
            "user_id": row.user_id,
            "to_user_id": row.to_user_id,
            "record_no": row.record_no,
            "user_name": row.user_name,
            "sale_package_id": row.sale_package_id,
            "sale_package_name": row.sale_package_name,
            "package_period": _format_package_period(row.period_type),
            "actual_period": _format_period_count(row.period_type, row.period_count),
            "card_count": row.card_count,
            "success_count": row.success_count,
            "failed_count": row.failed_count,
            "unit_price": row.unit_price / 100 if row.unit_price else 0,
            "total_amount": row.total_amount / 100 if row.total_amount else 0,
            "remark": row.remark,
            "operator_id": row.operator_id,
            "operator_name": row.operator_name,
            "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else None,
            "cards": cards
        }
        
        return data

    async def export_records(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """导出出库记录"""
        items, _ = await self.get_records_list(
            db=db,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            page=1,
            page_size=10000
        )
        return items


# ============ 新增：卡片回收 CRUD ============

class StockRecycleCRUD:
    """卡片回收 CRUD"""

    async def _get_recycle_relation_columns(self, db: AsyncSession) -> set[str]:
        """读取回收关联表当前实际列，兼容未跑完整迁移的库。"""
        result = await db.execute(text("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'stock_recycle_record_cards'
        """))
        return {row[0] for row in result.fetchall()}

    async def _insert_recycle_relations(
        self,
        db: AsyncSession,
        record_id: int,
        recycled_cards: List[dict]
    ) -> None:
        """按数据库实际列插入回收关联记录，避免旧表结构导致 500。"""
        if not recycled_cards:
            return

        available_columns = await self._get_recycle_relation_columns(db)
        insert_columns = ["record_id", "card_id", "iccid"]

        optional_columns = [
            "original_user_id",
            "original_status",
            "original_sale_package_id"
        ]
        insert_columns.extend(
            column for column in optional_columns if column in available_columns
        )

        column_sql = ", ".join(insert_columns)
        value_sql = ", ".join(f":{column}" for column in insert_columns)
        insert_sql = text(
            f"INSERT INTO stock_recycle_record_cards ({column_sql}) VALUES ({value_sql})"
        )

        rows = []
        for card_info in recycled_cards:
            row = {column: card_info.get(column) for column in insert_columns}
            row["record_id"] = record_id
            rows.append(row)

        await db.execute(insert_sql, rows)

    async def _refresh_recycled_pool_stats(self, db: AsyncSession, pool_ids: Set[int]) -> None:
        """回收后刷新旧流量池统计，避免空自动池继续显示旧卡数。"""
        if not pool_ids:
            return

        from app.crud.pool_crud import pool_crud

        for pool_id in pool_ids:
            if not pool_id:
                continue
            try:
                await pool_crud.update_stats(db, pool_id)
            except Exception as exc:
                await db.rollback()
                logger.warning("回收后刷新流量池统计失败 pool_id=%s error=%s", pool_id, exc)

    async def recycle_cards(
        self,
        db: AsyncSession,
        card_ids: List[int],
        recycle_reason: str,
        operator_id: int,
        remark: Optional[str] = None
    ) -> dict:
        """回收卡片"""
        from app.db.models.stock import StockRecycleRecordModel

        try:
            success_count = 0
            failed_count = 0
            recycled_cards = []
            affected_pool_ids: Set[int] = set()

            for card_id in card_ids:
                card_query = select(IotCardModel).where(
                    IotCardModel.id == card_id,
                    IotCardModel.user_id.isnot(None),  # 只能回收已出库的卡
                    IotCardModel.is_deleted == 0
                )
                card_result = await db.execute(card_query)
                card = card_result.scalar_one_or_none()

                if card:
                    original_user_id = card.user_id
                    original_status = card.status.value if hasattr(card.status, 'value') else card.status
                    original_sale_package_id = card.sale_package_id
                    original_pool_id = card.pool_id
                    if original_pool_id:
                        affected_pool_ids.add(original_pool_id)

                    card.user_id = None
                    card.sale_package_id = None
                    card.pool_id = None
                    card.is_pool_member = 0
                    card.status = CardStatus.stock
                    card.stock_out_at = None
                    card.stock_out_date = None
                    card.activated_at = None
                    card.expired_at = None
                    card.suspend_type = SuspendType.none
                    card.suspend_at = None
                    card.suspend_reason = None
                    success_count += 1
                    recycled_cards.append({
                        "card_id": card.id,
                        "iccid": card.iccid,
                        "original_user_id": original_user_id,
                        "original_status": original_status,
                        "original_sale_package_id": original_sale_package_id
                    })
                else:
                    failed_count += 1

            record = StockRecycleRecordModel(
                card_count=len(card_ids),
                success_count=success_count,
                failed_count=failed_count,
                recycle_reason=recycle_reason,
                remark=remark,
                operator_id=operator_id
            )
            db.add(record)
            await db.flush()

            await self._insert_recycle_relations(
                db=db,
                record_id=record.id,
                recycled_cards=recycled_cards
            )

            await db.commit()
            await self._refresh_recycled_pool_stats(db, affected_pool_ids)

            return {
                "success": success_count,
                "failed": failed_count,
                "record_id": record.id
            }
        except Exception:
            await db.rollback()
            raise

    async def recycle_by_iccids(
        self,
        db: AsyncSession,
        iccids: List[str],
        recycle_reason: str,
        operator_id: int,
        remark: Optional[str] = None
    ) -> dict:
        """通过ICCID批量回收卡片"""
        from app.db.models.stock import StockRecycleRecordModel

        try:
            success_count = 0
            failed_count = 0
            not_found = []
            recycled_cards = []
            affected_pool_ids: Set[int] = set()

            for iccid in iccids:
                iccid = iccid.strip()
                if not iccid:
                    continue
                card_query = select(IotCardModel).where(
                    IotCardModel.iccid == iccid,
                    IotCardModel.user_id.isnot(None),
                    IotCardModel.is_deleted == 0
                )
                card_result = await db.execute(card_query)
                card = card_result.scalar_one_or_none()

                if card:
                    original_user_id = card.user_id
                    original_status = card.status.value if hasattr(card.status, 'value') else card.status
                    original_sale_package_id = card.sale_package_id
                    original_pool_id = card.pool_id
                    if original_pool_id:
                        affected_pool_ids.add(original_pool_id)

                    card.user_id = None
                    card.sale_package_id = None
                    card.pool_id = None
                    card.is_pool_member = 0
                    card.status = CardStatus.stock
                    card.stock_out_at = None
                    card.stock_out_date = None
                    card.activated_at = None
                    card.expired_at = None
                    card.suspend_type = SuspendType.none
                    card.suspend_at = None
                    card.suspend_reason = None
                    success_count += 1
                    recycled_cards.append({
                        "card_id": card.id,
                        "iccid": card.iccid,
                        "original_user_id": original_user_id,
                        "original_status": original_status,
                        "original_sale_package_id": original_sale_package_id
                    })
                else:
                    failed_count += 1
                    not_found.append(iccid)

            record = StockRecycleRecordModel(
                card_count=len(iccids),
                success_count=success_count,
                failed_count=failed_count,
                recycle_reason=recycle_reason,
                remark=remark,
                operator_id=operator_id
            )
            db.add(record)
            await db.flush()

            await self._insert_recycle_relations(
                db=db,
                record_id=record.id,
                recycled_cards=recycled_cards
            )

            await db.commit()
            await self._refresh_recycled_pool_stats(db, affected_pool_ids)

            return {
                "success": success_count,
                "failed": failed_count,
                "record_id": record.id,
                "not_found": not_found
            }
        except Exception:
            await db.rollback()
            raise

    async def get_records_list(
        self,
        db: AsyncSession,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取回收记录列表"""
        from sqlalchemy import text
        
        # 构建WHERE条件
        where_conditions = ["srr.is_deleted = 0"]
        params = {}
        
        if start_date:
            where_conditions.append("srr.created_at >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            where_conditions.append("srr.created_at <= :end_date")
            params["end_date"] = f"{end_date} 23:59:59"
        
        where_clause = " AND ".join(where_conditions)
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) FROM stock_recycle_records srr WHERE {where_clause}"
        count_result = await db.execute(text(count_sql), params)
        total = count_result.scalar() or 0
        
        # 查询数据
        offset = (page - 1) * page_size
        params["offset"] = offset
        params["limit"] = page_size
        
        query_sql = f"""
            SELECT 
                srr.id, srr.card_count, srr.success_count, srr.failed_count,
                srr.recycle_reason, srr.remark, srr.operator_id, srr.created_at,
                u.name as operator_name
            FROM stock_recycle_records srr
            LEFT JOIN sys_users u ON srr.operator_id = u.id
            WHERE {where_clause}
            ORDER BY srr.id DESC
            LIMIT :limit OFFSET :offset
        """
        
        result = await db.execute(text(query_sql), params)
        rows = result.fetchall()
        
        items = []
        for row in rows:
            items.append({
                "id": row.id,
                "card_count": row.card_count,
                "success_count": row.success_count,
                "failed_count": row.failed_count,
                "recycle_reason": row.recycle_reason,
                "remark": row.remark,
                "operator_id": row.operator_id,
                "operator_name": row.operator_name,
                "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else None,
            })
        
        return items, total


batch_crud = PurchaseBatchCRUD()
stock_in_crud = StockInCRUD()
stock_out_crud = StockOutCRUD()
stock_summary_crud = StockSummaryCRUD()
stock_in_record_crud = StockInRecordCRUD()
stock_out_record_crud = StockOutRecordCRUD()


class CardStockRecordCRUD:
    """按卡号查询出入库记录 CRUD"""

    async def get_card_records(self, db: AsyncSession, iccid: str) -> List[dict]:
        """查询指定卡号的所有出入库记录"""
        from app.db.models.stock import StockInRecordCardModel, StockOutRecordCardModel
        from sqlalchemy import text

        # 查询入库记录
        in_query = text("""
            SELECT 'in' as record_type, sirc.record_id, sirc.iccid, sirc.created_at,
                   sirc.test_expire_date, sirc.silent_expire_date,
                   sirc.supplier_name, sirc.base_package_name,
                   sp.period_type, sir.package_period_count,
                   u.name as operator_name
            FROM stock_in_record_cards sirc
            LEFT JOIN stock_in_records sir ON sirc.record_id = sir.id
            LEFT JOIN supplier_packages sp ON sir.package_id = sp.id
            LEFT JOIN sys_users u ON sir.operator_id = u.id
            WHERE sirc.iccid = :iccid
        """)
        in_result = await db.execute(in_query, {"iccid": iccid})
        in_records = in_result.fetchall()

        # 查询出库记录
        out_query = text("""
            SELECT 'out' as record_type, sorc.record_id, sorc.iccid, sorc.created_at,
                   sorc.test_expire_date, sorc.silent_expire_date,
                   sorc.supplier_name, sorc.base_package_name,
                   sorc.sale_package_name, sorc.target_user_name,
                   sp.period_type, c.period_count,
                   u.name as operator_name
            FROM stock_out_record_cards sorc
            LEFT JOIN stock_out_records sor ON sorc.record_id = sor.id
            LEFT JOIN sale_packages sp ON sor.sale_package_id = sp.id
            LEFT JOIN iot_cards c ON sorc.card_id = c.id
            LEFT JOIN sys_users u ON sor.operator_id = u.id
            WHERE sorc.iccid = :iccid
        """)
        out_result = await db.execute(out_query, {"iccid": iccid})
        out_records = out_result.fetchall()

        # 合并记录
        records = []
        for row in in_records:
            records.append({
                "record_type": "in",
                "record_id": row.record_id,
                "iccid": row.iccid,
                "operator": row.operator_name,
                "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else None,
                "test_expire_date": row.test_expire_date.strftime("%Y-%m-%d") if row.test_expire_date else None,
                "silent_expire_date": row.silent_expire_date.strftime("%Y-%m-%d") if row.silent_expire_date else None,
                "supplier_name": row.supplier_name,
                "base_package_name": row.base_package_name,
                "package_period": _format_period_count(row.period_type, row.package_period_count),
                "sale_package_name": None,
                "target_user_name": None
            })

        for row in out_records:
            records.append({
                "record_type": "out",
                "record_id": row.record_id,
                "iccid": row.iccid,
                "operator": row.operator_name,
                "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else None,
                "test_expire_date": row.test_expire_date.strftime("%Y-%m-%d") if row.test_expire_date else None,
                "silent_expire_date": row.silent_expire_date.strftime("%Y-%m-%d") if row.silent_expire_date else None,
                "supplier_name": row.supplier_name,
                "base_package_name": row.base_package_name,
                "sale_package_name": row.sale_package_name,
                "package_period": _format_period_count(row.period_type, row.period_count),
                "target_user_name": row.target_user_name
            })

        # 按时间倒序排序
        records.sort(key=lambda x: x["created_at"] or "", reverse=True)
        return records


card_stock_record_crud = CardStockRecordCRUD()
stock_recycle_crud = StockRecycleCRUD()
