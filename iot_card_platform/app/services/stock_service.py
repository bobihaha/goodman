"""
出入库管理服务层
"""
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.stock_crud import (
    batch_crud, stock_in_crud, stock_out_crud, stock_summary_crud,
    stock_in_record_crud, stock_out_record_crud, stock_recycle_crud
)
from app.db.models.stock import PurchaseBatchModel
from app.db.models.package import SupplierPackageModel
from app.db.models.supplier import SupplierModel
from app.db.models.sys_user import UserLevel
from app.utils.exceptions import BusinessException


class StockService:
    """出入库服务"""

    # ============ 采购批次 ============

    async def create_batch(
        self,
        db: AsyncSession,
        supplier_id: int,
        package_id: int,
        test_expire_date,
        silent_expire_date,
        purchase_date,
        created_by: int,
        remark: Optional[str] = None
    ) -> dict:
        """创建采购批次"""
        # 获取底层套餐信息
        pkg_query = select(SupplierPackageModel).where(
            SupplierPackageModel.id == package_id,
            SupplierPackageModel.is_deleted == 0
        )
        pkg_result = await db.execute(pkg_query)
        package = pkg_result.scalar_one_or_none()
        if not package:
            raise BusinessException(code=404, msg="底层套餐不存在")

        batch = await batch_crud.create(
            db=db,
            supplier_id=supplier_id,
            package_id=package_id,
            carrier=package.carrier.value,
            flow_size=package.flow_size,
            period_type=package.period_type.value,
            test_expire_date=test_expire_date,
            silent_expire_date=silent_expire_date,
            purchase_date=purchase_date,
            created_by=created_by,
            remark=remark
        )
        return batch.to_dict()

    async def get_batches(
        self,
        db: AsyncSession,
        supplier_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取批次列表"""
        items, total = await batch_crud.get_list(
            db=db,
            supplier_id=supplier_id,
            status=status,
            page=page,
            page_size=page_size
        )

        # 关联供应商和套餐名称
        result = []
        for item in items:
            data = item.to_dict()
            # 获取供应商名称
            supplier_query = select(SupplierModel.name).where(SupplierModel.id == item.supplier_id)
            supplier_result = await db.execute(supplier_query)
            supplier_name = supplier_result.scalar_one_or_none()
            data["supplier_name"] = supplier_name

            # 获取套餐名称
            pkg_query = select(SupplierPackageModel.name).where(SupplierPackageModel.id == item.package_id)
            pkg_result = await db.execute(pkg_query)
            pkg_name = pkg_result.scalar_one_or_none()
            data["package_name"] = pkg_name

            result.append(data)

        return result, total

    async def get_batch_detail(self, db: AsyncSession, batch_id: int) -> dict:
        """获取批次详情"""
        batch = await batch_crud.get_by_id(db, batch_id)
        if not batch:
            raise BusinessException(code=404, msg="批次不存在")
        return batch.to_dict()

    # ============ 入库 ============

    async def stock_in(
        self,
        db: AsyncSession,
        batch_id: int,
        cards: List[dict],
        created_by: int,
        remark: Optional[str] = None
    ) -> dict:
        """批量入库"""
        try:
            record, fail_details = await stock_in_crud.create(
                db=db,
                batch_id=batch_id,
                cards=cards,
                created_by=created_by,
                remark=remark
            )
            return {
                "record_no": record.record_no,
                "total": record.card_count,
                "success": record.success_count,
                "failed": record.fail_count,
                "fail_details": fail_details if fail_details else None
            }
        except ValueError as e:
            raise BusinessException(code=400, msg=str(e))

    async def get_stock_in_records(
        self,
        db: AsyncSession,
        batch_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取入库记录列表"""
        items, total = await stock_in_crud.get_list(
            db=db, batch_id=batch_id, page=page, page_size=page_size
        )
        return [item.to_dict() for item in items], total

    # ============ 出库 ============

    async def stock_out(
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
    ) -> dict:
        """批量出库"""
        record, success, failed = await stock_out_crud.create(
            db=db,
            card_ids=card_ids,
            to_user_id=to_user_id,
            sale_package_id=sale_package_id,
            period_count=period_count,
            card_type=card_type,
            stock_out_date=stock_out_date,
            test_expire_date=test_expire_date,
            silent_expire_date=silent_expire_date,
            created_by=created_by,
            remark=remark
        )
        return {
            "record_no": record.record_no,
            "total": record.card_count,
            "success": success,
            "failed": failed
        }

    async def get_stock_out_records(
        self,
        db: AsyncSession,
        to_user_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取出库记录列表"""
        items, total = await stock_out_crud.get_list(
            db=db, to_user_id=to_user_id, page=page, page_size=page_size
        )
        return [item.to_dict() for item in items], total

    # ============ 库存统计 ============

    async def get_summary(self, db: AsyncSession) -> dict:
        """获取库存统计"""
        return await stock_summary_crud.get_summary(db)

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
    ) -> Tuple[List[dict], int]:
        """获取库存卡片列表"""
        items, total = await stock_summary_crud.get_inventory(
            db=db,
            supplier_id=supplier_id,
            carrier=carrier,
            package_id=package_id,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size
        )
        
        # 关联供应商名称和批次号
        result = []
        for item in items:
            data = item.to_dict()
            
            # 获取供应商名称
            if item.supplier_id:
                supplier_query = select(SupplierModel.name).where(
                    SupplierModel.id == item.supplier_id,
                    SupplierModel.is_deleted == 0
                )
                supplier_result = await db.execute(supplier_query)
                data["supplier_name"] = supplier_result.scalar_one_or_none()
            else:
                data["supplier_name"] = None
            
            # 获取批次号
            if item.batch_id:
                batch_query = select(PurchaseBatchModel.batch_no).where(
                    PurchaseBatchModel.id == item.batch_id,
                    PurchaseBatchModel.is_deleted == 0
                )
                batch_result = await db.execute(batch_query)
                data["batch_no"] = batch_result.scalar_one_or_none()
            else:
                data["batch_no"] = None
            
            result.append(data)
        
        return result, total

    # ============ 入库记录 ============

    async def get_in_records_list(
        self,
        db: AsyncSession,
        supplier_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取入库记录列表"""
        items, total = await stock_in_record_crud.get_records_list(
            db=db,
            supplier_id=supplier_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )
        return items, total

    async def get_in_record_detail(self, db: AsyncSession, record_id: int) -> dict:
        """获取入库记录详情"""
        detail = await stock_in_record_crud.get_record_detail(db, record_id)
        if not detail:
            raise BusinessException(code=404, msg="入库记录不存在")
        return detail

    async def export_in_records(
        self,
        db: AsyncSession,
        supplier_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """导出入库记录"""
        return await stock_in_record_crud.export_records(
            db=db,
            supplier_id=supplier_id,
            start_date=start_date,
            end_date=end_date
        )

    # ============ 出库记录 ============

    async def get_out_records_list(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取出库记录列表"""
        items, total = await stock_out_record_crud.get_records_list(
            db=db,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )
        return items, total

    async def get_out_record_detail(self, db: AsyncSession, record_id: int) -> dict:
        """获取出库记录详情"""
        detail = await stock_out_record_crud.get_record_detail(db, record_id)
        if not detail:
            raise BusinessException(code=404, msg="出库记录不存在")
        return detail

    async def export_out_records(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """导出出库记录"""
        return await stock_out_record_crud.export_records(
            db=db,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )

    # ============ 卡片回收 ============

    async def recycle_cards(
        self,
        db: AsyncSession,
        card_ids: List[int],
        recycle_reason: str,
        operator_id: int,
        remark: Optional[str] = None
    ) -> dict:
        """卡片回收"""
        result = await stock_recycle_crud.recycle_cards(
            db=db,
            card_ids=card_ids,
            recycle_reason=recycle_reason,
            operator_id=operator_id,
            remark=remark
        )
        return result

    async def get_recycle_records(
        self,
        db: AsyncSession,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取回收记录列表"""
        items, total = await stock_recycle_crud.get_records_list(
            db=db,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )
        return items, total

    # ============ 批量查询 ============

    async def batch_query_cards(
        self,
        db: AsyncSession,
        iccids: List[str]
    ) -> dict:
        """批量查询卡片"""
        return await stock_summary_crud.batch_query_cards(db, iccids)

    async def export_inventory(
        self,
        db: AsyncSession,
        supplier_id: Optional[int] = None,
        carrier: Optional[str] = None,
        package_id: Optional[int] = None,
        sort_by: str = "stock_in_at",
        sort_order: str = "desc"
    ) -> List[dict]:
        """导出库存数据"""
        return await stock_summary_crud.export_inventory(
            db=db,
            supplier_id=supplier_id,
            carrier=carrier,
            package_id=package_id,
            sort_by=sort_by,
            sort_order=sort_order
        )

    # ============ Excel批量出库 ============

    async def batch_stock_out_import(
        self,
        db: AsyncSession,
        items: List,
        created_by: int
    ) -> dict:
        """Excel批量出库"""
        from app.db.models.iot_card import IotCardModel, CardStatus, CardType
        from app.db.models.package import SalePackageModel
        
        total = len(items)
        success = 0
        failed = 0
        fail_details = []
        
        for idx, item in enumerate(items):
            try:
                # 1. 根据ICCID查找卡片
                card_query = select(IotCardModel).where(
                    IotCardModel.iccid == item.iccid,
                    IotCardModel.status == CardStatus.stock,
                    IotCardModel.is_deleted == 0
                )
                card_result = await db.execute(card_query)
                card = card_result.scalar_one_or_none()
                
                if not card:
                    fail_details.append({
                        "row": idx + 2,  # Excel行号（从2开始，因为第1行是表头）
                        "iccid": item.iccid,
                        "reason": "卡片不存在或不在库存状态"
                    })
                    failed += 1
                    continue
                
                # 2. 验证销售套餐
                pkg_query = select(SalePackageModel).where(
                    SalePackageModel.id == item.sale_package_id,
                    SalePackageModel.is_deleted == 0
                )
                pkg_result = await db.execute(pkg_query)
                package = pkg_result.scalar_one_or_none()
                
                if not package:
                    fail_details.append({
                        "row": idx + 2,
                        "iccid": item.iccid,
                        "reason": f"销售套餐ID {item.sale_package_id} 不存在"
                    })
                    failed += 1
                    continue
                
                # 3. 更新卡片信息
                card.user_id = item.user_id
                card.sale_package_id = item.sale_package_id
                card.period_count = item.period_count
                
                # 设置卡类型（如果提供）
                if item.card_type:
                    card.card_type = CardType(item.card_type)
                
                # 设置日期
                card.stock_out_date = item.stock_out_date
                card.test_expire_date = item.test_expire_date
                card.silent_expire_date = item.silent_expire_date
                card.status = CardStatus.silent  # 出库后进入沉默期
                card.stock_out_at = datetime.now()
                
                success += 1
                
            except Exception as e:
                fail_details.append({
                    "row": idx + 2,
                    "iccid": item.iccid,
                    "reason": str(e)
                })
                failed += 1
        
        await db.commit()
        
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "fail_details": fail_details if fail_details else None
        }


stock_service = StockService()
