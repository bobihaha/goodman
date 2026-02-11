"""
认证模块接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import LoginRequest, LoginResponse, RefreshTokenRequest, SuperLoginRequest, CurrentUser
from app.schemas.common import ResponseModel
from app.services.auth_service import auth_service
from app.db.database import get_db
from app.utils.auth import get_current_user

router = APIRouter()


def get_client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post("/login", summary="用户登录", response_model=ResponseModel)
async def login(request: Request, login_data: LoginRequest = Body(...), db: AsyncSession = Depends(get_db)):
    ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    result = await auth_service.login(db, login_data, ip, user_agent)
    return ResponseModel(data=result.model_dump())


@router.post("/logout", summary="退出登录", response_model=ResponseModel)
async def logout(current_user: CurrentUser = Depends(get_current_user)):
    return ResponseModel(msg="退出成功")


@router.post("/refresh", summary="刷新令牌", response_model=ResponseModel)
async def refresh_token(data: RefreshTokenRequest = Body(...), db: AsyncSession = Depends(get_db)):
    result = await auth_service.refresh_token(db, data)
    return ResponseModel(data=result)


@router.post("/super-login", summary="超级登录", response_model=ResponseModel)
async def super_login(request: Request, data: SuperLoginRequest = Body(...), db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    result = await auth_service.super_login(db, current_user, data.target_user_id, ip, user_agent)
    return ResponseModel(data=result.model_dump())


@router.post("/exit-super-login", summary="退出超级登录", response_model=ResponseModel)
async def exit_super_login(db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    """退出超级登录，恢复到原用户身份"""
    result = await auth_service.exit_super_login(db, current_user)
    return ResponseModel(data=result.model_dump(), msg="已退出超级登录")


@router.get("/profile", summary="获取当前用户信息", response_model=ResponseModel)
async def get_profile(current_user: CurrentUser = Depends(get_current_user)):
    return ResponseModel(data=current_user.model_dump())


@router.get("/permissions", summary="获取用户权限", response_model=ResponseModel)
async def get_permissions(current_user: CurrentUser = Depends(get_current_user)):
    return ResponseModel(data=current_user.permissions)

