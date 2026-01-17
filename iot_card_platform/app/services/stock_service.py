"""
出入库管理服务层
"""
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.stock_crud import batch_crud, stock_in_crud, stock_out_crud, stock_summary_crud
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
            raise BusinessException(code=404, message="底层套餐不存在")

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
            raise BusinessException(code=404, message="批次不存在")
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
            raise BusinessException(code=400, message=str(e))

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
        created_by: int,
        remark: Optional[str] = None
    ) -> dict:
        """批量出库"""
        record, success, failed = await stock_out_crud.create(
            db=db,
            card_ids=card_ids,
            to_user_id=to_user_id,
            sale_package_id=sale_package_id,
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
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取库存卡片列表"""
        items, total = await stock_summary_crud.get_inventory(
            db=db,
            supplier_id=supplier_id,
            carrier=carrier,
            page=page,
            page_size=page_size
        )
        return [item.to_dict() for item in items], total


stock_service = StockService()
