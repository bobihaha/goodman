"""
用户模块数据操作层
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from passlib.context import CryptContext

from app.db.models.user import UserModel, UserStatus
from app.schemas.user import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserCrud:

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[UserModel]:
        result = await db.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_phone_or_username(
        db: AsyncSession, phone: str, username: str
    ) -> Optional[UserModel]:
        result = await db.execute(
            select(UserModel).where(
                or_(UserModel.phone == phone, UserModel.username == username),
                UserModel.is_deleted == 0
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_account(db: AsyncSession, account: str) -> Optional[UserModel]:
        result = await db.execute(
            select(UserModel).where(
                or_(
                    UserModel.phone == account,
                    UserModel.username == account,
                    UserModel.email == account
                ),
                UserModel.is_deleted == 0
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> UserModel:
        hashed_password = pwd_context.hash(user_data.password)
        user = UserModel(
            username=user_data.username,
            phone=user_data.phone,
            email=user_data.email,
            password=hashed_password,
            status=UserStatus.enable,
            company=user_data.company
        )
        db.add(user)
        return user

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
