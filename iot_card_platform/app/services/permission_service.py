"""
权限管理服务层
"""
from typing import List, Tuple, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.permission_crud import permission_crud, user_permission_crud
from app.schemas.permission import PermissionCreate, PermissionUpdate, PermissionQuery
from app.utils.exceptions import BusinessException


# 模块名称映射
MODULE_NAMES = {
    "card": "卡片管理",
    "pool": "流量池管理",
    "user": "用户管理",
    "package": "套餐管理",
    "stock": "库存管理",
    "supplier": "供应商管理",
    "suspend": "停卡策略",
    "system": "系统管理",
    "dashboard": "仪表盘"
}


class PermissionService:
    """权限服务"""

    async def create_permission(self, db: AsyncSession, data: PermissionCreate) -> dict:
        """创建权限"""
        # 检查权限代码是否已存在
        existing = await permission_crud.get_by_code(db, data.code)
        if existing:
            raise BusinessException(code=400, msg=f"权限代码 {data.code} 已存在")

        permission = await permission_crud.create(
            db=db,
            code=data.code,
            name=data.name,
            module=data.module,
            description=data.description,
            sort_order=data.sort_order
        )
        return permission.to_dict()

    async def get_permission(self, db: AsyncSession, permission_id: int) -> dict:
        """获取权限详情"""
        permission = await permission_crud.get_by_id(db, permission_id)
        if not permission:
            raise BusinessException(code=404, msg="权限不存在")
        return permission.to_dict()

    async def get_permission_list(self, db: AsyncSession, query: PermissionQuery) -> Tuple[List[dict], int]:
        """获取权限列表"""
        items, total = await permission_crud.get_list(
            db=db,
            module=query.module,
            keyword=query.keyword,
            page=query.page,
            page_size=query.page_size
        )
        return [item.to_dict() for item in items], total

    async def get_all_permissions(self, db: AsyncSession) -> List[dict]:
        """获取所有权限"""
        permissions = await permission_crud.get_all(db)
        return [p.to_dict() for p in permissions]

    async def get_permissions_by_module(self, db: AsyncSession) -> List[Dict]:
        """按模块分组获取权限"""
        modules = await permission_crud.get_modules(db)
        result = []
        
        for module in sorted(modules):
            permissions = await permission_crud.get_by_module(db, module)
            result.append({
                "module": module,
                "module_name": MODULE_NAMES.get(module, module),
                "permissions": [p.to_dict() for p in permissions]
            })
        
        return result

    async def update_permission(self, db: AsyncSession, permission_id: int, 
                              data: PermissionUpdate) -> dict:
        """更新权限"""
        permission = await permission_crud.update(
            db=db,
            permission_id=permission_id,
            **data.model_dump(exclude_unset=True)
        )
        if not permission:
            raise BusinessException(code=404, msg="权限不存在")
        return permission.to_dict()

    async def delete_permission(self, db: AsyncSession, permission_id: int) -> bool:
        """删除权限"""
        # 检查是否有用户使用此权限
        user_count = await user_permission_crud.count_users_with_permission(db, permission_id)
        if user_count > 0:
            raise BusinessException(code=400, msg=f"该权限被{user_count}个用户使用，无法删除")

        success = await permission_crud.delete(db, permission_id)
        if not success:
            raise BusinessException(code=404, msg="权限不存在")
        return True

    async def assign_user_permissions(self, db: AsyncSession, user_id: int,
                                     permission_ids: List[int]) -> dict:
        """为用户分配权限"""
        # 批量验证所有权限ID是否有效
        from sqlalchemy import select
        from app.db.models.permission import PermissionModel

        stmt = select(PermissionModel.id).where(PermissionModel.id.in_(permission_ids))
        valid_ids = set((await db.execute(stmt)).scalars().all())
        invalid = set(permission_ids) - valid_ids
        if invalid:
            raise BusinessException(code=400, msg=f"权限ID不存在: {invalid}")

        count = await user_permission_crud.assign_permissions(db, user_id, permission_ids)
        return {
            "user_id": user_id,
            "assigned_count": count,
            "permission_ids": permission_ids
        }

    async def add_user_permissions(self, db: AsyncSession, user_id: int, 
                                  permission_ids: List[int]) -> dict:
        """为用户添加权限"""
        count = await user_permission_crud.add_permissions(db, user_id, permission_ids)
        return {
            "user_id": user_id,
            "added_count": count
        }

    async def remove_user_permissions(self, db: AsyncSession, user_id: int, 
                                     permission_ids: List[int]) -> dict:
        """移除用户权限"""
        count = await user_permission_crud.remove_permissions(db, user_id, permission_ids)
        return {
            "user_id": user_id,
            "removed_count": count
        }

    async def get_user_permissions(self, db: AsyncSession, user_id: int) -> List[dict]:
        """获取用户的所有权限"""
        permissions = await user_permission_crud.get_user_permissions(db, user_id)
        return [p.to_dict() for p in permissions]

    async def get_user_permission_ids(self, db: AsyncSession, user_id: int) -> List[int]:
        """获取用户的权限ID列表"""
        return await user_permission_crud.get_user_permission_ids(db, user_id)

    async def get_user_permission_codes(self, db: AsyncSession, user_id: int) -> List[str]:
        """获取用户的权限代码列表"""
        return await user_permission_crud.get_user_permission_codes(db, user_id)

    async def check_user_permission(self, db: AsyncSession, user_id: int, 
                                   permission_code: str) -> bool:
        """检查用户是否拥有指定权限"""
        return await user_permission_crud.has_permission(db, user_id, permission_code)


permission_service = PermissionService()





