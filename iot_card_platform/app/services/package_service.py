"""
套餐业务逻辑
"""
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.db.models.package import PackageModel
from app.schemas.package import PackageCreate, PackageUpdate, PackageInfo
from app.utils.exceptions import BusinessException


class PackageService:

    @staticmethod
    async def create_package(db: AsyncSession, data: PackageCreate) -> PackageInfo:
        # 检查编码是否已存在
        existing = await db.execute(
            select(PackageModel).where(PackageModel.code == data.code)
        )
        if existing.scalar_one_or_none():
            raise BusinessException(code=400, msg="套餐编码已存在")
        
        package = PackageModel(**data.model_dump())
        db.add(package)
        await db.flush()
        return PackageInfo.model_validate(package)

    @staticmethod
    async def get_package_list(db: AsyncSession, page: int, page_size: int) -> Tuple[List[PackageInfo], int]:
        offset = (page - 1) * page_size
        
        stmt = select(PackageModel).where(
            PackageModel.is_deleted == 0
        ).offset(offset).limit(page_size)
        result = await db.execute(stmt)
        packages = result.scalars().all()
        
        total_stmt = select(func.count(PackageModel.id)).where(PackageModel.is_deleted == 0)
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0
        
        return [PackageInfo.model_validate(p) for p in packages], total

    @staticmethod
    async def get_package_by_id(db: AsyncSession, package_id: int) -> PackageInfo:
        result = await db.execute(
            select(PackageModel).where(
                PackageModel.id == package_id,
                PackageModel.is_deleted == 0
            )
        )
        package = result.scalar_one_or_none()
        if not package:
            raise BusinessException(code=404, msg="套餐不存在")
        return PackageInfo.model_validate(package)

    @staticmethod
    async def update_package(db: AsyncSession, package_id: int, data: PackageUpdate) -> PackageInfo:
        result = await db.execute(
            select(PackageModel).where(
                PackageModel.id == package_id,
                PackageModel.is_deleted == 0
            )
        )
        package = result.scalar_one_or_none()
        if not package:
            raise BusinessException(code=404, msg="套餐不存在")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(package, key, value)
        
        await db.flush()
        return PackageInfo.model_validate(package)

    @staticmethod
    async def delete_package(db: AsyncSession, package_id: int):
        result = await db.execute(
            select(PackageModel).where(
                PackageModel.id == package_id,
                PackageModel.is_deleted == 0
            )
        )
        package = result.scalar_one_or_none()
        if not package:
            raise BusinessException(code=404, msg="套餐不存在")
        
        package.is_deleted = 1
        await db.flush()
