"""
系统菜单管理接口
"""
from typing import List
from fastapi import APIRouter, Depends, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.common import ResponseModel
from app.schemas.auth import CurrentUser
from app.crud.sys_menu_crud import sys_menu_crud, sys_user_menu_crud
from app.db.database import get_db
from app.utils.auth import get_current_user, require_super_admin

router = APIRouter()


@router.get("", summary="获取菜单列表", response_model=ResponseModel)
async def get_menu_list(db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(require_super_admin)):
    menus = await sys_menu_crud.get_all_menus(db)
    return ResponseModel(data=[{
        "id": m.id, "parent_id": m.parent_id, "user_level": m.user_level,
        "code": m.code, "name": m.name, "type": m.type.value if hasattr(m.type, 'value') else m.type,
        "icon": m.icon, "path": m.path, "permission": m.permission, "sort_order": m.sort_order
    } for m in menus])


@router.get("/user/{user_id}", summary="获取用户菜单权限", response_model=ResponseModel)
async def get_user_menus(user_id: int = Path(...), db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(require_super_admin)):
    menu_ids = await sys_user_menu_crud.get_user_menu_ids(db, user_id)
    return ResponseModel(data=menu_ids)


@router.put("/user/{user_id}", summary="设置用户菜单权限", response_model=ResponseModel)
async def set_user_menus(user_id: int = Path(...), menu_ids: List[int] = Body(...), db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(require_super_admin)):
    await sys_user_menu_crud.set_user_menus(db, user_id, menu_ids)
    return ResponseModel(msg="设置成功")

