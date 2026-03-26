"""
系统用户 CRUD
"""
from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.sys_user import SysUserModel, UserLevel
from app.schemas.sys_user import UserQuery
from app.crud.base import CRUDBase


class SysUserCRUD(CRUDBase[SysUserModel]):
    def __init__(self):
        super().__init__(SysUserModel)

    async def get_by_account(self, db: AsyncSession, account: str) -> Optional[SysUserModel]:
        stmt = select(SysUserModel).where(SysUserModel.account == account, SysUserModel.is_deleted == 0)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_h5_slug(self, db: AsyncSession, slug: str) -> Optional[SysUserModel]:
        stmt = select(SysUserModel).where(
            SysUserModel.h5_slug == slug,
            SysUserModel.is_deleted == 0
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_users_by_parent(self, db: AsyncSession, parent_id: int, query: UserQuery) -> Tuple[List[SysUserModel], int]:
        conditions = [SysUserModel.parent_id == parent_id, SysUserModel.is_deleted == 0]
        if query.keyword:
            keyword = f"%{query.keyword}%"
            conditions.append(or_(SysUserModel.name.like(keyword), SysUserModel.account.like(keyword), SysUserModel.phone.like(keyword)))
        if query.status:
            conditions.append(SysUserModel.status == query.status)
        
        count_stmt = select(func.count(SysUserModel.id)).where(*conditions)
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        offset = (query.page - 1) * query.page_size
        list_stmt = select(SysUserModel).where(*conditions).order_by(SysUserModel.created_at.desc()).offset(offset).limit(query.page_size)
        list_result = await db.execute(list_stmt)
        users = list(list_result.scalars().all())
        
        return users, total

    async def get_all_users(self, db: AsyncSession, query: UserQuery) -> Tuple[List[SysUserModel], int]:
        # 超级管理员用户列表只展示其直接创建的二级用户；
        # 三级子用户应由对应二级用户在自己的列表中管理。
        conditions = [
            SysUserModel.is_deleted == 0,
            SysUserModel.user_level == UserLevel.USER.value,
        ]
        if query.keyword:
            keyword = f"%{query.keyword}%"
            conditions.append(or_(SysUserModel.name.like(keyword), SysUserModel.account.like(keyword)))
        if query.status:
            conditions.append(SysUserModel.status == query.status)
        
        count_stmt = select(func.count(SysUserModel.id)).where(*conditions)
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        offset = (query.page - 1) * query.page_size
        list_stmt = select(SysUserModel).where(*conditions).order_by(SysUserModel.user_level.asc(), SysUserModel.created_at.desc()).offset(offset).limit(query.page_size)
        list_result = await db.execute(list_stmt)
        users = list(list_result.scalars().all())
        
        return users, total

    async def count_children(self, db: AsyncSession, parent_id: int) -> int:
        stmt = select(func.count(SysUserModel.id)).where(SysUserModel.parent_id == parent_id, SysUserModel.is_deleted == 0)
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def check_account_exists(self, db: AsyncSession, account: str, exclude_id: Optional[int] = None) -> bool:
        conditions = [SysUserModel.account == account, SysUserModel.is_deleted == 0]
        if exclude_id:
            conditions.append(SysUserModel.id != exclude_id)
        stmt = select(func.count(SysUserModel.id)).where(*conditions)
        result = await db.execute(stmt)
        return (result.scalar() or 0) > 0

    async def check_h5_slug_exists(self, db: AsyncSession, slug: str, exclude_id: Optional[int] = None) -> bool:
        conditions = [SysUserModel.h5_slug == slug, SysUserModel.is_deleted == 0]
        if exclude_id:
            conditions.append(SysUserModel.id != exclude_id)
        stmt = select(func.count(SysUserModel.id)).where(*conditions)
        result = await db.execute(stmt)
        return (result.scalar() or 0) > 0


sys_user_crud = SysUserCRUD()
