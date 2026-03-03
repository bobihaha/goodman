"""
系统菜单管理接口
"""
from typing import List
from fastapi import APIRouter, Depends, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.common import ResponseModel
from app.schemas.auth import CurrentUser
from app.crud.sys_menu_crud import sys_menu_crud, sys_user_menu_crud
from app.db.models.sys_user import SysUserModel
from app.db.database import get_db
from app.utils.auth import get_current_user, require_super_admin, require_user_level

router = APIRouter()


@router.get("", summary="获取菜单列表", response_model=ResponseModel)
async def get_menu_list(db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    """获取菜单列表（根据用户级别过滤）"""
    if current_user.user_level == 1:
        menus = await sys_menu_crud.get_all_menus(db)
    else:
        menus = await sys_menu_crud.get_menus_by_user_id(db, current_user.id, current_user.user_level)
    return ResponseModel(data=[{
        "id": m.id, "parent_id": m.parent_id, "user_level": m.user_level,
        "code": m.code, "name": m.name, "type": m.type.value if hasattr(m.type, 'value') else m.type,
        "icon": m.icon, "path": m.path, "permission": m.permission, "sort_order": m.sort_order
    } for m in menus])


@router.get("/user/{user_id}", summary="获取用户菜单权限", response_model=ResponseModel)
async def get_user_menus(user_id: int = Path(...), db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    """获取用户的菜单ID列表"""
    # 权限检查
    if current_user.user_level == 1:
        # 超级管理员可以查询任何用户
        pass
    elif current_user.id == user_id:
        # 可以查询自己
        pass
    elif current_user.user_level == 2:
        # 二级用户可以查询自己的子用户
        from sqlalchemy import select
        user_result = await db.execute(select(SysUserModel).where(SysUserModel.id == user_id))
        target_user = user_result.scalar_one_or_none()
        if not target_user or target_user.parent_id != current_user.id:
            return ResponseModel(code=403, msg="权限不足：只能查询自己或子用户的菜单")
    else:
        return ResponseModel(code=403, msg="权限不足：只能查询自己的菜单")

    # 先查自定义分配的菜单
    menu_ids = await sys_user_menu_crud.get_user_menu_ids(db, user_id)

    # 如果没有自定义菜单，查上级用户的菜单（三级账户继承二级账户）
    if not menu_ids:
        from sqlalchemy import select
        user_result = await db.execute(select(SysUserModel).where(SysUserModel.id == user_id))
        target_user = user_result.scalar_one_or_none()
        if target_user and target_user.user_level == 3 and target_user.parent_id:
            # 三级账户：继承上级二级用户的菜单，但排除 user_level=2 的菜单（仅限二级及以上）
            menu_ids = await sys_user_menu_crud.get_user_menu_ids(db, target_user.parent_id)
            if menu_ids:
                # 过滤掉 user_level=2 的菜单
                all_menus = await sys_menu_crud.get_all_menus(db)
                level2_only_ids = {m.id for m in all_menus if m.user_level == 2}
                menu_ids = [mid for mid in menu_ids if mid not in level2_only_ids]
            if not menu_ids:
                menus = await sys_menu_crud.get_menus_by_user_level(db, 3)
                menu_ids = [m.id for m in menus]
        elif target_user:
            # 其他级别：按 user_level 查默认菜单
            menus = await sys_menu_crud.get_menus_by_user_level(db, target_user.user_level)
            menu_ids = [m.id for m in menus]

    return ResponseModel(data=menu_ids)


@router.put("/user/{user_id}", summary="设置用户菜单权限", response_model=ResponseModel)
async def set_user_menus(user_id: int = Path(...), menu_ids: List[int] = Body(...), db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(require_user_level)):
    """设置用户的菜单权限（管理员及二级账户）"""
    # 权限验证
    if current_user.user_level == 2:
        # 二级用户只能为自己的直接子用户设置菜单
        from sqlalchemy import select
        user_result = await db.execute(select(SysUserModel).where(SysUserModel.id == user_id))
        target_user = user_result.scalar_one_or_none()
        if not target_user or target_user.user_level != 3 or target_user.parent_id != current_user.id:
            return ResponseModel(code=403, msg="权限不足：只能为自己的子用户设置菜单")

    await sys_user_menu_crud.set_user_menus(db, user_id, menu_ids)
    return ResponseModel(msg="设置成功")
