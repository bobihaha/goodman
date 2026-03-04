"""
调试接口 - 查看当前用户的菜单数据
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.common import ResponseModel
from app.schemas.auth import CurrentUser
from app.crud.sys_menu_crud import sys_menu_crud, sys_user_menu_crud
from app.db.database import get_db
from app.utils.auth import get_current_user

router = APIRouter()


@router.get("/debug/my-menus", summary="调试：查看我的菜单", response_model=ResponseModel)
async def debug_my_menus(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """调试接口：查看当前用户的菜单权限"""
    # 获取用户的菜单ID列表
    menu_ids = await sys_user_menu_crud.get_user_menu_ids(db, current_user.id)

    # 获取所有菜单
    all_menus = await sys_menu_crud.get_all_menus(db)

    # 获取用户有权限的菜单详情
    user_menus = [m for m in all_menus if m.id in menu_ids]

    return ResponseModel(data={
        "user_id": current_user.id,
        "user_name": current_user.name,
        "user_level": current_user.user_level,
        "menu_ids": menu_ids,
        "menu_count": len(menu_ids),
        "menus": [{
            "id": m.id,
            "code": m.code,
            "name": m.name,
            "path": m.path,
            "sort_order": m.sort_order
        } for m in user_menus]
    })
