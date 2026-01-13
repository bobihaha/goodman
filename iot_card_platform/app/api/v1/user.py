"""
用户模块接口
"""
from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate, UserLogin, UserInfo
from app.schemas.common import ResponseModel
from app.services.user_service import UserService
from app.db.database import get_db
from app.utils.auth import get_current_user, RoleChecker

router = APIRouter()
admin_checker = RoleChecker(["admin"])


@router.post("/register", summary="用户注册", response_model=ResponseModel)
async def user_register(
    user_data: UserCreate = Body(...),
    db: AsyncSession = Depends(get_db)
):
    user_info = await UserService.register(db, user_data)
    return ResponseModel(data=user_info.model_dump())


@router.post("/login", summary="用户登录", response_model=ResponseModel)
async def user_login(
    login_data: UserLogin = Body(...),
    db: AsyncSession = Depends(get_db)
):
    token_data = await UserService.login(db, login_data)
    return ResponseModel(data=token_data)


@router.get("/info", summary="获取当前用户信息", response_model=ResponseModel)
async def get_user_info(current_user: UserInfo = Depends(get_current_user)):
    return ResponseModel(data=current_user.model_dump())


@router.get("/list", summary="用户列表（管理员）", response_model=ResponseModel)
async def get_user_list(
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(admin_checker)
):
    user_list, total = await UserService.get_user_list(db, page, page_size)
    return ResponseModel(data={
        "list": [user.model_dump() for user in user_list],
        "total": total,
        "page": page,
        "page_size": page_size
    })
