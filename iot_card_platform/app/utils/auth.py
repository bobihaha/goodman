"""
JWT 认证工具
"""
from typing import List, Optional
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.auth import CurrentUser
from app.services.auth_service import AuthService
from app.utils.exceptions import AuthException, PermissionDeniedException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> CurrentUser:
    if not token:
        raise AuthException()
    return await AuthService.get_current_user(db, token)


async def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> Optional[CurrentUser]:
    if not token:
        return None
    try:
        return await AuthService.get_current_user(db, token)
    except Exception:
        return None


class RequireLevel:
    def __init__(self, allowed_levels: List[int]):
        self.allowed_levels = allowed_levels
    
    async def __call__(self, current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.user_level not in self.allowed_levels:
            raise PermissionDeniedException()
        return current_user


require_super_admin = RequireLevel([1])
require_user_level = RequireLevel([1, 2])
require_any_level = RequireLevel([1, 2, 3])
