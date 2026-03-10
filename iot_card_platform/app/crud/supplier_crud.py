"""
供应商 CRUD 操作
"""
from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.supplier import SupplierModel, SupplierType, SupplierStatus
from app.db.models.package import SupplierPackageModel
from app.db.models.iot_card import IotCardModel
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierQuery


class SupplierCRUD:
    """供应商 CRUD"""

    async def create(self, db: AsyncSession, data: SupplierCreate, created_by: int = None) -> SupplierModel:
        """创建供应商"""
        from app.utils.const import encrypt_secret

        supplier = SupplierModel(
            name=data.name,
            code=data.code,
            type=data.type,
            contact_name=data.contact_name,
            contact_phone=data.contact_phone,
            contact_email=data.contact_email,
            api_url=data.api_url,
            api_key=encrypt_secret(data.api_key) if data.api_key else None,
            api_secret=encrypt_secret(data.api_secret) if data.api_secret else None,
            api_config=data.api_config,
            remark=data.remark,
            created_by=created_by,
        )
        db.add(supplier)
        await db.commit()
        await db.refresh(supplier)
        return supplier

    async def get_by_id(self, db: AsyncSession, supplier_id: int) -> Optional[SupplierModel]:
        """根据ID获取供应商"""
        stmt = select(SupplierModel).where(
            SupplierModel.id == supplier_id,
            SupplierModel.is_deleted == 0
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[SupplierModel]:
        """根据编码获取供应商"""
        stmt = select(SupplierModel).where(
            SupplierModel.code == code,
            SupplierModel.is_deleted == 0
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(self, db: AsyncSession, query: SupplierQuery) -> Tuple[List[SupplierModel], int]:
        """获取供应商列表"""
        conditions = [SupplierModel.is_deleted == 0]

        if query.keyword:
            conditions.append(or_(
                SupplierModel.name.like(f"%{query.keyword}%"),
                SupplierModel.code.like(f"%{query.keyword}%"),
                SupplierModel.contact_name.like(f"%{query.keyword}%"),
            ))
        if query.type:
            conditions.append(SupplierModel.type == query.type)
        if query.status:
            conditions.append(SupplierModel.status == query.status)

        # 总数
        count_stmt = select(func.count(SupplierModel.id)).where(*conditions)
        total = await db.execute(count_stmt)
        total = total.scalar()

        # 列表
        stmt = select(SupplierModel).where(*conditions).order_by(
            SupplierModel.created_at.desc()
        ).offset((query.page - 1) * query.page_size).limit(query.page_size)
        result = await db.execute(stmt)
        suppliers = result.scalars().all()

        return list(suppliers), total

    async def get_all_enabled(self, db: AsyncSession) -> List[SupplierModel]:
        """获取所有启用的供应商"""
        stmt = select(SupplierModel).where(
            SupplierModel.is_deleted == 0,
            SupplierModel.status == SupplierStatus.enable
        ).order_by(SupplierModel.name)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, db: AsyncSession, supplier_id: int, data: SupplierUpdate) -> Optional[SupplierModel]:
        """更新供应商"""
        from app.utils.const import encrypt_secret

        supplier = await self.get_by_id(db, supplier_id)
        if not supplier:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key in ('api_key', 'api_secret') and value:
                value = encrypt_secret(value)
            setattr(supplier, key, value)

        await db.commit()
        await db.refresh(supplier)
        return supplier

    async def count_packages(self, db: AsyncSession, supplier_id: int) -> int:
        """统计供应商关联的套餐数量"""
        stmt = select(func.count(SupplierPackageModel.id)).where(
            SupplierPackageModel.supplier_id == supplier_id,
            SupplierPackageModel.is_deleted == 0
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def count_cards(self, db: AsyncSession, supplier_id: int) -> int:
        """统计供应商关联的卡片数量"""
        stmt = select(func.count(IotCardModel.id)).where(
            IotCardModel.supplier_id == supplier_id,
            IotCardModel.is_deleted == 0
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def delete(self, db: AsyncSession, supplier_id: int) -> bool:
        """删除供应商(软删除)"""
        supplier = await self.get_by_id(db, supplier_id)
        if not supplier:
            return False

        supplier.is_deleted = 1
        await db.commit()
        return True


supplier_crud = SupplierCRUD()
