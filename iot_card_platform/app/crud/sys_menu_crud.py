"""
系统菜单 CRUD
"""
from typing import Optional, List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.sys_menu import SysMenuModel, SysUserMenuModel, MenuStatus
from app.crud.base import CRUDBase


class SysMenuCRUD(CRUDBase[SysMenuModel]):
    def __init__(self):
        super().__init__(SysMenuModel)

    async def get_menus_by_user_level(self, db: AsyncSession, user_level: int) -> List[SysMenuModel]:
        # 三级账户(level=3)继承二级账户(level=2)的菜单
        levels = [0, user_level]
        if user_level == 3:
            levels.append(2)
        stmt = select(SysMenuModel).where(
            SysMenuModel.user_level.in_(levels),
            SysMenuModel.status == MenuStatus.enable,
            SysMenuModel.is_deleted == 0
        ).order_by(SysMenuModel.sort_order.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_menus_by_user_id(self, db: AsyncSession, user_id: int, user_level: int) -> List[SysMenuModel]:
        user_menu_stmt = select(SysUserMenuModel.menu_id).where(SysUserMenuModel.user_id == user_id, SysUserMenuModel.is_deleted == 0)
        user_menu_result = await db.execute(user_menu_stmt)
        custom_menu_ids = [row[0] for row in user_menu_result.fetchall()]
        
        if custom_menu_ids:
            stmt = select(SysMenuModel).where(SysMenuModel.id.in_(custom_menu_ids), SysMenuModel.status == MenuStatus.enable, SysMenuModel.is_deleted == 0).order_by(SysMenuModel.sort_order.asc())
        else:
            # 三级账户(level=3)继承二级账户(level=2)的菜单
            levels = [0, user_level]
            if user_level == 3:
                levels.append(2)
            stmt = select(SysMenuModel).where(SysMenuModel.user_level.in_(levels), SysMenuModel.status == MenuStatus.enable, SysMenuModel.is_deleted == 0).order_by(SysMenuModel.sort_order.asc())
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_all_menus(self, db: AsyncSession) -> List[SysMenuModel]:
        stmt = select(SysMenuModel).where(SysMenuModel.is_deleted == 0).order_by(SysMenuModel.sort_order.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())


class SysUserMenuCRUD(CRUDBase[SysUserMenuModel]):
    def __init__(self):
        super().__init__(SysUserMenuModel)

    async def get_user_menu_ids(self, db: AsyncSession, user_id: int) -> List[int]:
        stmt = select(SysUserMenuModel.menu_id).where(SysUserMenuModel.user_id == user_id, SysUserMenuModel.is_deleted == 0)
        result = await db.execute(stmt)
        return [row[0] for row in result.fetchall()]

    async def set_user_menus(self, db: AsyncSession, user_id: int, menu_ids: List[int]) -> bool:
        delete_stmt = delete(SysUserMenuModel).where(SysUserMenuModel.user_id == user_id)
        await db.execute(delete_stmt)
        for menu_id in menu_ids:
            user_menu = SysUserMenuModel(user_id=user_id, menu_id=menu_id)
            db.add(user_menu)
        await db.flush()
        return True


sys_menu_crud = SysMenuCRUD()
sys_user_menu_crud = SysUserMenuCRUD()
