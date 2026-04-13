"""
开放 API 认证工具
"""
import secrets
from typing import Optional
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models.sys_user import UserLevel, UserStatus
from app.crud.sys_user_crud import sys_user_crud
from app.schemas.auth import CurrentUser
from app.services.auth_service import AuthService
from app.utils.const import decrypt_secret
from app.utils.exceptions import AuthException, BusinessException


async def get_open_api_current_user(
    x_app_id: Optional[str] = Header(None, alias="X-APP-ID"),
    x_app_secret: Optional[str] = Header(None, alias="X-APP-SECRET"),
    db: AsyncSession = Depends(get_db)
) -> CurrentUser:
    if not x_app_id or not x_app_secret:
        raise AuthException()
    user = await sys_user_crud.get_by_open_api_app_id(db, x_app_id.strip())
    if not user or user.user_level != UserLevel.USER.value:
        raise AuthException()
    if user.status != UserStatus.enable:
        raise BusinessException(code=403, msg="用户已被禁用")
    if not user.open_api_enabled or not user.open_api_app_secret:
        raise AuthException()

    actual_secret = decrypt_secret(user.open_api_app_secret)
    if not secrets.compare_digest(actual_secret, x_app_secret.strip()):
        raise AuthException()

    permissions = await AuthService._get_user_permissions(db, user)
    return CurrentUser(
        id=user.id,
        parent_id=user.parent_id,
        user_level=user.user_level,
        name=user.name,
        account=user.account,
        phone=user.phone,
        email=user.email,
        avatar=user.avatar,
        status=user.status.value if hasattr(user.status, "value") else str(user.status),
        permissions=permissions,
        is_super_login=False,
        original_user_id=None
    )
