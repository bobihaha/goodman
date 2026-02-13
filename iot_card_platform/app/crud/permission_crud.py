"""
权限管理 CRUD 操作
"""
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from app.db.models.permission import PermissionModel, UserPermissionModel


class PermissionCRUD:
    """权限 CRUD"""

    async def create(self, db: AsyncSession, code: str, name: str, module: str, 
                    description: Optional[str] = None, sort_order: int = 0) -> PermissionModel:
        """创建权限"""
        permission = PermissionModel(
            code=code,
            name=name,
            module=module,
            description=description,
            sort_order=sort_order
        )
        db.add(permission)
        await db.commit()
        await db.refresh(permission)
        return permission

    async def get_by_id(self, db: AsyncSession, permission_id: int) -> Optional[PermissionModel]:
        """根据ID获取权限"""
        query = select(PermissionModel).where(
            PermissionModel.id == permission_id,
            PermissionModel.is_deleted == 0
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[PermissionModel]:
        """根据代码获取权限"""
        query = select(PermissionModel).where(
            PermissionModel.code == code,
            PermissionModel.is_deleted == 0
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_list(self, db: AsyncSession, module: Optional[str] = None, 
                      keyword: Optional[str] = None, page: int = 1, 
                      page_size: int = 20) -> Tuple[List[PermissionModel], int]:
        """获取权限列表"""
        query = select(PermissionModel).where(PermissionModel.is_deleted == 0)
        count_query = select(func.count(PermissionModel.id)).where(PermissionModel.is_deleted == 0)

        # 模块筛选
        if module:
            query = query.where(PermissionModel.module == module)
            count_query = count_query.where(PermissionModel.module == module)

        # 关键词搜索
        if keyword:
            search_filter = or_(
                PermissionModel.code.like(f'%{keyword}%'),
                PermissionModel.name.like(f'%{keyword}%'),
                PermissionModel.description.like(f'%{keyword}%')
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # 总数
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 分页
        query = query.order_by(PermissionModel.module, PermissionModel.sort_order, PermissionModel.id)
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = result.scalars().all()

        return list(items), total

    async def get_all(self, db: AsyncSession) -> List[PermissionModel]:
        """获取所有权限"""
        query = select(PermissionModel).where(
            PermissionModel.is_deleted == 0
        ).order_by(PermissionModel.module, PermissionModel.sort_order, PermissionModel.id)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_module(self, db: AsyncSession, module: str) -> List[PermissionModel]:
        """根据模块获取权限列表"""
        query = select(PermissionModel).where(
            PermissionModel.module == module,
            PermissionModel.is_deleted == 0
        ).order_by(PermissionModel.sort_order, PermissionModel.id)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_modules(self, db: AsyncSession) -> List[str]:
        """获取所有模块"""
        query = select(PermissionModel.module).where(
            PermissionModel.is_deleted == 0
        ).distinct()
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update(self, db: AsyncSession, permission_id: int, **kwargs) -> Optional[PermissionModel]:
        """更新权限"""
        permission = await self.get_by_id(db, permission_id)
        if not permission:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(permission, key):
                setattr(permission, key, value)

        await db.commit()
        await db.refresh(permission)
        return permission

    async def delete(self, db: AsyncSession, permission_id: int) -> bool:
        """软删除权限"""
        permission = await self.get_by_id(db, permission_id)
        if not permission:
            return False

        permission.is_deleted = 1
        await db.commit()
        return True


class UserPermissionCRUD:
    """用户权限关联 CRUD"""

    async def assign_permissions(self, db: AsyncSession, user_id: int, 
                                permission_ids: List[int]) -> int:
        """为用户分配权限（覆盖式）"""
        # 1. 删除用户现有权限
        await self.clear_user_permissions(db, user_id)

        # 2. 添加新权限
        count = 0
        for permission_id in permission_ids:
            user_permission = UserPermissionModel(
                user_id=user_id,
                permission_id=permission_id
            )
            db.add(user_permission)
            count += 1

        await db.commit()
        return count

    async def add_permissions(self, db: AsyncSession, user_id: int, 
                            permission_ids: List[int]) -> int:
        """为用户添加权限（追加式）"""
        # 获取用户已有权限
        existing_permissions = await self.get_user_permission_ids(db, user_id)
        
        # 只添加新权限
        count = 0
        for permission_id in permission_ids:
            if permission_id not in existing_permissions:
                user_permission = UserPermissionModel(
                    user_id=user_id,
                    permission_id=permission_id
                )
                db.add(user_permission)
                count += 1

        await db.commit()
        return count

    async def remove_permissions(self, db: AsyncSession, user_id: int, 
                                permission_ids: List[int]) -> int:
        """移除用户权限"""
        query = select(UserPermissionModel).where(
            UserPermissionModel.user_id == user_id,
            UserPermissionModel.permission_id.in_(permission_ids),
            UserPermissionModel.is_deleted == 0
        )
        result = await db.execute(query)
        user_permissions = result.scalars().all()

        count = 0
        for user_permission in user_permissions:
            user_permission.is_deleted = 1
            count += 1

        await db.commit()
        return count

    async def clear_user_permissions(self, db: AsyncSession, user_id: int) -> int:
        """清空用户所有权限"""
        query = select(UserPermissionModel).where(
            UserPermissionModel.user_id == user_id,
            UserPermissionModel.is_deleted == 0
        )
        result = await db.execute(query)
        user_permissions = result.scalars().all()

        count = 0
        for user_permission in user_permissions:
            user_permission.is_deleted = 1
            count += 1

        await db.commit()
        return count

    async def get_user_permissions(self, db: AsyncSession, user_id: int) -> List[PermissionModel]:
        """获取用户的所有权限"""
        query = select(PermissionModel).join(
            UserPermissionModel,
            and_(
                UserPermissionModel.permission_id == PermissionModel.id,
                UserPermissionModel.user_id == user_id,
                UserPermissionModel.is_deleted == 0
            )
        ).where(
            PermissionModel.is_deleted == 0
        ).order_by(PermissionModel.module, PermissionModel.sort_order)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_user_permission_ids(self, db: AsyncSession, user_id: int) -> List[int]:
        """获取用户的权限ID列表"""
        query = select(UserPermissionModel.permission_id).where(
            UserPermissionModel.user_id == user_id,
            UserPermissionModel.is_deleted == 0
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_user_permission_codes(self, db: AsyncSession, user_id: int) -> List[str]:
        """获取用户的权限代码列表"""
        query = select(PermissionModel.code).join(
            UserPermissionModel,
            and_(
                UserPermissionModel.permission_id == PermissionModel.id,
                UserPermissionModel.user_id == user_id,
                UserPermissionModel.is_deleted == 0
            )
        ).where(
            PermissionModel.is_deleted == 0
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def has_permission(self, db: AsyncSession, user_id: int, permission_code: str) -> bool:
        """检查用户是否拥有指定权限"""
        query = select(func.count(UserPermissionModel.id)).join(
            PermissionModel,
            and_(
                PermissionModel.id == UserPermissionModel.permission_id,
                PermissionModel.code == permission_code,
                PermissionModel.is_deleted == 0
            )
        ).where(
            UserPermissionModel.user_id == user_id,
            UserPermissionModel.is_deleted == 0
        )
        result = await db.execute(query)
        count = result.scalar()
        return count > 0


permission_crud = PermissionCRUD()
user_permission_crud = UserPermissionCRUD()





