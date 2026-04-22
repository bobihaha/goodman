"""
套餐 CRUD 操作
"""
from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.package import (
    SupplierPackageModel, SalePackageModel,
    CarrierType, PeriodType, PackageStatus, PERIOD_CONFIG
)
from app.schemas.package import (
    SupplierPackageCreate, SupplierPackageUpdate, SupplierPackageQuery,
    SalePackageCreate, SalePackageUpdate, SalePackageQuery
)


def get_default_effective_days(period_type: str) -> int:
    """获取默认有效天数: 月包30天, 年包360天"""
    config = PERIOD_CONFIG.get(period_type, {})
    return config.get("default_days", 30)


class SupplierPackageCRUD:
    """底层套餐 CRUD"""

    async def create(self, db: AsyncSession, data: SupplierPackageCreate, created_by: int = None) -> SupplierPackageModel:
        """创建底层套餐"""
        # 如果未指定有效天数，使用默认值
        effective_days = data.effective_days
        if effective_days is None:
            effective_days = get_default_effective_days(data.period_type.value)
        
        package = SupplierPackageModel(
            supplier_id=data.supplier_id,
            name=data.name,
            code=data.code,
            carrier=data.carrier,
            flow_size=data.flow_size,
            period_type=data.period_type,
            effective_days=effective_days,
            period_months=data.period_months,
            period_days=data.period_days,
            price_cost=data.price_cost,
            remark=data.remark,
            created_by=created_by,
        )
        db.add(package)
        await db.commit()
        await db.refresh(package)
        return package

    async def get_by_id(self, db: AsyncSession, package_id: int) -> Optional[SupplierPackageModel]:
        """根据ID获取套餐"""
        stmt = select(SupplierPackageModel).where(
            SupplierPackageModel.id == package_id,
            SupplierPackageModel.is_deleted == 0
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[SupplierPackageModel]:
        """根据编码获取套餐"""
        stmt = select(SupplierPackageModel).where(
            SupplierPackageModel.code == code,
            SupplierPackageModel.is_deleted == 0
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(self, db: AsyncSession, query: SupplierPackageQuery) -> Tuple[List[SupplierPackageModel], int]:
        """获取套餐列表"""
        conditions = [SupplierPackageModel.is_deleted == 0]

        if query.keyword:
            conditions.append(or_(
                SupplierPackageModel.name.like(f"%{query.keyword}%"),
                SupplierPackageModel.code.like(f"%{query.keyword}%"),
            ))
        if query.supplier_id:
            conditions.append(SupplierPackageModel.supplier_id == query.supplier_id)
        if query.carrier:
            conditions.append(SupplierPackageModel.carrier == query.carrier)
        if query.period_type:
            conditions.append(SupplierPackageModel.period_type == query.period_type)
        if query.status:
            conditions.append(SupplierPackageModel.status == query.status)

        # 总数
        count_stmt = select(func.count(SupplierPackageModel.id)).where(*conditions)
        total = await db.execute(count_stmt)
        total = total.scalar()

        # 列表
        stmt = select(SupplierPackageModel).where(*conditions).order_by(
            SupplierPackageModel.created_at.desc()
        ).offset((query.page - 1) * query.page_size).limit(query.page_size)
        result = await db.execute(stmt)
        packages = result.scalars().all()

        return list(packages), total

    async def get_by_supplier(self, db: AsyncSession, supplier_id: int) -> List[SupplierPackageModel]:
        """获取供应商的所有套餐"""
        stmt = select(SupplierPackageModel).where(
            SupplierPackageModel.supplier_id == supplier_id,
            SupplierPackageModel.is_deleted == 0,
            SupplierPackageModel.status == PackageStatus.enable
        ).order_by(SupplierPackageModel.name)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, db: AsyncSession, package_id: int, data: SupplierPackageUpdate) -> Optional[SupplierPackageModel]:
        """更新套餐"""
        package = await self.get_by_id(db, package_id)
        if not package:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(package, key, value)

        await db.commit()
        await db.refresh(package)
        return package

    async def delete(self, db: AsyncSession, package_id: int) -> bool:
        """删除套餐(软删除)"""
        package = await self.get_by_id(db, package_id)
        if not package:
            return False

        package.is_deleted = 1
        await db.commit()
        return True


class SalePackageCRUD:
    """销售套餐 CRUD"""

    async def create(self, db: AsyncSession, data: SalePackageCreate, user_id: int = None, created_by: int = None) -> SalePackageModel:
        """创建销售套餐"""
        # 如果未指定有效天数，使用默认值
        effective_days = data.effective_days
        if effective_days is None:
            effective_days = get_default_effective_days(data.period_type.value)
        
        package = SalePackageModel(
            user_id=user_id,
            base_package_id=data.base_package_id,
            name=data.name,
            code=data.code,
            carrier=data.carrier,
            flow_size=data.flow_size,
            period_type=data.period_type,
            effective_days=effective_days,
            period_months=data.period_months,
            period_days=data.period_days,
            price_cost=data.price_cost,
            price_sale=data.price_sale,
            is_public=1 if data.is_public else 0,
            sort_order=data.sort_order,
            remark=data.remark,
            created_by=created_by,
        )
        db.add(package)
        await db.commit()
        await db.refresh(package)
        return package

    async def get_by_id(self, db: AsyncSession, package_id: int) -> Optional[SalePackageModel]:
        """根据ID获取套餐"""
        stmt = select(SalePackageModel).where(
            SalePackageModel.id == package_id,
            SalePackageModel.is_deleted == 0
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[SalePackageModel]:
        """根据编码获取套餐"""
        stmt = select(SalePackageModel).where(
            SalePackageModel.code == code,
            SalePackageModel.is_deleted == 0
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(self, db: AsyncSession, query: SalePackageQuery, user_id: int = None) -> Tuple[List[SalePackageModel], int]:
        """获取套餐列表"""
        conditions = [SalePackageModel.is_deleted == 0]

        # 数据隔离: 只能看自己的套餐或平台公开套餐
        if user_id:
            conditions.append(or_(
                SalePackageModel.user_id == user_id,
                and_(SalePackageModel.user_id.is_(None), SalePackageModel.is_public == 1)
            ))

        if query.keyword:
            conditions.append(or_(
                SalePackageModel.name.like(f"%{query.keyword}%"),
                SalePackageModel.code.like(f"%{query.keyword}%"),
            ))
        if query.user_id:
            conditions.append(SalePackageModel.user_id == query.user_id)
        if query.carrier:
            conditions.append(SalePackageModel.carrier == query.carrier)
        if query.period_type:
            conditions.append(SalePackageModel.period_type == query.period_type)
        if query.is_public is not None:
            conditions.append(SalePackageModel.is_public == (1 if query.is_public else 0))
        if query.status:
            conditions.append(SalePackageModel.status == query.status)

        # 总数
        count_stmt = select(func.count(SalePackageModel.id)).where(*conditions)
        total = await db.execute(count_stmt)
        total = total.scalar()

        # 列表
        stmt = select(SalePackageModel).where(*conditions).order_by(
            SalePackageModel.sort_order,
            SalePackageModel.created_at.desc()
        ).offset((query.page - 1) * query.page_size).limit(query.page_size)
        result = await db.execute(stmt)
        packages = result.scalars().all()

        return list(packages), total

    async def get_user_packages(self, db: AsyncSession, user_id: int) -> List[SalePackageModel]:
        """获取用户的所有套餐"""
        stmt = select(SalePackageModel).where(
            or_(
                SalePackageModel.user_id == user_id,
                and_(SalePackageModel.user_id.is_(None), SalePackageModel.is_public == 1)
            ),
            SalePackageModel.is_deleted == 0,
            SalePackageModel.status == PackageStatus.enable
        ).order_by(SalePackageModel.sort_order, SalePackageModel.name)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, db: AsyncSession, package_id: int, data: SalePackageUpdate) -> Optional[SalePackageModel]:
        """更新套餐"""
        package = await self.get_by_id(db, package_id)
        if not package:
            return None

        update_data = data.model_dump(exclude_unset=True)
        # 处理 is_public 字段
        if 'is_public' in update_data:
            update_data['is_public'] = 1 if update_data['is_public'] else 0

        for key, value in update_data.items():
            setattr(package, key, value)

        await db.commit()
        await db.refresh(package)
        return package

    async def delete(self, db: AsyncSession, package_id: int) -> bool:
        """删除套餐(软删除)"""
        package = await self.get_by_id(db, package_id)
        if not package:
            return False

        package.is_deleted = 1
        await db.commit()
        return True


supplier_package_crud = SupplierPackageCRUD()
sale_package_crud = SalePackageCRUD()
