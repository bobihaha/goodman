"""
用户模块业务逻辑
"""
from typing import List, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.db.models.user import UserModel, UserStatus
from app.schemas.user import UserCreate, UserLogin, UserInfo
from app.crud.user_crud import UserCrud
from app.utils.auth import create_access_token, create_refresh_token
from app.utils.exceptions import (
    UserNotFoundException, UserDisabledException, 
    PasswordErrorException, BusinessException
)
from app.config import settings


class UserService:

    @staticmethod
    async def register(db: AsyncSession, user_data: UserCreate) -> UserInfo:
        existing = await UserCrud.get_user_by_phone_or_username(
            db, user_data.phone, user_data.username
        )
        if existing:
            raise BusinessException(code=400, msg="手机号或用户名已被注册")
        
        new_user = await UserCrud.create_user(db, user_data)
        await db.flush()
        return UserInfo.model_validate(new_user)

    @staticmethod
    async def login(db: AsyncSession, login_data: UserLogin) -> Dict[str, Any]:
        user = await UserCrud.get_user_by_account(db, login_data.account)
        if not user:
            raise UserNotFoundException()
        
        if user.status == UserStatus.disable:
            raise UserDisabledException()
        
        if not UserCrud.verify_password(login_data.password, user.password):
            raise PasswordErrorException()
        
        access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expire_minutes": settings.access_token_expire_minutes
        }

    @staticmethod
    async def get_user_list(db: AsyncSession, page: int, page_size: int) -> Tuple[List[UserInfo], int]:
        offset = (page - 1) * page_size
        
        query = select(UserModel).where(UserModel.is_deleted == 0).offset(offset).limit(page_size)
        result = await db.execute(query)
        users = result.scalars().all()
        
        total_query = select(func.count(UserModel.id)).where(UserModel.is_deleted == 0)
        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0
        
        return [UserInfo.model_validate(u) for u in users], total

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> UserInfo:
        user = await UserCrud.get_user_by_id(db, user_id)
        if not user or user.is_deleted == 1:
            raise UserNotFoundException()
        return UserInfo.model_validate(user)
