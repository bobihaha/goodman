"""
通用 CRUD 基类
"""
from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class CRUDBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id, self.model.is_deleted == 0)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100, filters: Optional[List] = None) -> List[ModelType]:
        stmt = select(self.model).where(self.model.is_deleted == 0)
        if filters:
            for f in filters:
                stmt = stmt.where(f)
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count(self, db: AsyncSession, filters: Optional[List] = None) -> int:
        stmt = select(func.count(self.model.id)).where(self.model.is_deleted == 0)
        if filters:
            for f in filters:
                stmt = stmt.where(f)
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def create(self, db: AsyncSession, obj_in: Dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, id: int, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        stmt = update(self.model).where(self.model.id == id, self.model.is_deleted == 0).values(**obj_in)
        await db.execute(stmt)
        return await self.get_by_id(db, id)

    async def delete(self, db: AsyncSession, id: int) -> bool:
        stmt = update(self.model).where(self.model.id == id).values(is_deleted=1)
        result = await db.execute(stmt)
        return result.rowcount > 0
