"""
认证服务
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
import jwt
from jwt.exceptions import PyJWTError

from app.config import settings
from app.db.models.sys_user import SysUserModel, UserLevel, UserStatus
from app.db.models.sys_log import SysLoginLogModel, LoginType
from app.db.models.log import SuperLoginLogModel
from app.crud.sys_user_crud import sys_user_crud
from app.crud.sys_menu_crud import sys_menu_crud
from app.schemas.auth import LoginRequest, LoginResponse, CurrentUser, RefreshTokenRequest
from app.utils.exceptions import BusinessException, AuthException, PermissionDeniedException, UserNotFoundException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
            if payload.get("type") != token_type:
                raise AuthException()
            return payload
        except PyJWTError:
            raise AuthException()
    
    @classmethod
    async def login(cls, db: AsyncSession, request: LoginRequest, ip: Optional[str] = None, user_agent: Optional[str] = None) -> LoginResponse:
        user = await sys_user_crud.get_by_account(db, request.account)

        login_log = SysLoginLogModel(account=request.account, login_type=LoginType.normal, ip=ip, user_agent=user_agent)

        if not user:
            login_log.is_success = 0
            login_log.fail_reason = "账户不存在"
            db.add(login_log)
            await db.commit()
            raise BusinessException(code=400, msg="账号或密码错误")

        if not cls.verify_password(request.password, user.password):
            login_log.user_id = user.id
            login_log.is_success = 0
            login_log.fail_reason = "密码错误"
            db.add(login_log)
            await db.commit()
            raise BusinessException(code=400, msg="账号或密码错误")

        if user.status != UserStatus.enable:
            login_log.user_id = user.id
            login_log.is_success = 0
            login_log.fail_reason = "用户已禁用"
            db.add(login_log)
            await db.commit()
            raise BusinessException(code=403, msg="用户已被禁用")

        permissions = await cls._get_user_permissions(db, user)
        
        token_data = {"sub": str(user.id), "account": user.account, "user_level": user.user_level, "is_super_login": False}
        access_token = cls.create_access_token(token_data)
        refresh_token = cls.create_refresh_token(token_data)
        
        await sys_user_crud.update(db, id=user.id, obj_in={"last_login_at": datetime.now(), "last_login_ip": ip})
        
        login_log.user_id = user.id
        login_log.is_success = 1
        db.add(login_log)
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=CurrentUser(
                id=user.id, parent_id=user.parent_id, user_level=user.user_level,
                name=user.name, account=user.account, phone=user.phone, email=user.email,
                avatar=user.avatar, status=user.status.value, permissions=permissions, is_super_login=False
            )
        )
    
    @classmethod
    async def super_login(cls, db: AsyncSession, operator: CurrentUser, target_user_id: int, ip: Optional[str] = None, user_agent: Optional[str] = None) -> LoginResponse:
        target_user = await sys_user_crud.get_by_id(db, target_user_id)
        if not target_user:
            raise UserNotFoundException()
        
        can_super_login = False
        if operator.is_super_admin():
            can_super_login = target_user.user_level == UserLevel.USER.value
        elif operator.is_user():
            can_super_login = target_user.user_level == UserLevel.SUB_USER.value and target_user.parent_id == operator.id
        
        if not can_super_login:
            raise PermissionDeniedException()
        
        if target_user.status != UserStatus.enable:
            raise BusinessException(code=403, msg="目标用户已被禁用")
        
        permissions = await cls._get_user_permissions(db, target_user)
        
        token_data = {"sub": str(target_user.id), "account": target_user.account, "user_level": target_user.user_level, "is_super_login": True, "original_user_id": operator.id}
        access_token = cls.create_access_token(token_data, expires_delta=timedelta(minutes=settings.super_login_expire_minutes))
        refresh_token = cls.create_refresh_token(token_data)
        
        # 记录登录日志
        login_log = SysLoginLogModel(user_id=target_user.id, account=target_user.account, login_type=LoginType.super_, operator_id=operator.id, is_success=1, ip=ip, user_agent=user_agent)
        db.add(login_log)
        
        # 记录超级登录日志
        super_login_log = SuperLoginLogModel(
            original_user_id=operator.id,
            target_user_id=target_user.id,
            login_at=datetime.now(),
            ip=ip,
            user_agent=user_agent
        )
        db.add(super_login_log)
        await db.commit()
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.super_login_expire_minutes * 60,
            user=CurrentUser(
                id=target_user.id, parent_id=target_user.parent_id, user_level=target_user.user_level,
                name=target_user.name, account=target_user.account, phone=target_user.phone, email=target_user.email,
                avatar=target_user.avatar, status=target_user.status.value, permissions=permissions, is_super_login=True, original_user_id=operator.id
            )
        )
    
    @classmethod
    async def exit_super_login(cls, db: AsyncSession, current_user: CurrentUser) -> LoginResponse:
        """退出超级登录，恢复到原用户身份"""
        if not current_user.is_super_login or not current_user.original_user_id:
            raise BusinessException(code=400, msg="当前不在超级登录模式")
        
        # 获取原用户信息
        original_user = await sys_user_crud.get_by_id(db, current_user.original_user_id)
        if not original_user:
            raise UserNotFoundException()
        
        if original_user.status != UserStatus.enable:
            raise BusinessException(code=403, msg="原用户已被禁用")
        
        # 更新超级登录日志的退出时间
        from sqlalchemy import select, update
        stmt = (
            update(SuperLoginLogModel)
            .where(
                SuperLoginLogModel.original_user_id == current_user.original_user_id,
                SuperLoginLogModel.target_user_id == current_user.id,
                SuperLoginLogModel.logout_at.is_(None)
            )
            .values(logout_at=datetime.now())
        )
        await db.execute(stmt)
        await db.commit()
        
        # 获取原用户权限
        permissions = await cls._get_user_permissions(db, original_user)
        
        # 生成新的token（不再是超级登录模式）
        token_data = {"sub": str(original_user.id), "account": original_user.account, "user_level": original_user.user_level, "is_super_login": False}
        access_token = cls.create_access_token(token_data)
        refresh_token = cls.create_refresh_token(token_data)
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=CurrentUser(
                id=original_user.id, parent_id=original_user.parent_id, user_level=original_user.user_level,
                name=original_user.name, account=original_user.account, phone=original_user.phone, email=original_user.email,
                avatar=original_user.avatar, status=original_user.status.value, permissions=permissions, is_super_login=False
            )
        )
    
    @classmethod
    async def refresh_token(cls, db: AsyncSession, request: RefreshTokenRequest) -> Dict[str, Any]:
        payload = cls.verify_token(request.refresh_token, token_type="refresh")
        user_id = payload.get("sub")
        if not user_id:
            raise AuthException()
        user = await sys_user_crud.get_by_id(db, int(user_id))
        if not user or user.status != UserStatus.enable:
            raise AuthException()
        
        is_super_login = payload.get("is_super_login", False)
        original_user_id = payload.get("original_user_id")
        token_data = {"sub": str(user.id), "account": user.account, "user_level": user.user_level, "is_super_login": is_super_login}
        if original_user_id:
            token_data["original_user_id"] = original_user_id
        access_token = cls.create_access_token(token_data)
        return {"access_token": access_token, "token_type": "Bearer", "expires_in": settings.access_token_expire_minutes * 60}
    
    @classmethod
    async def get_current_user(cls, db: AsyncSession, token: str) -> CurrentUser:
        payload = cls.verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise AuthException()
        user = await sys_user_crud.get_by_id(db, int(user_id))
        if not user or user.is_deleted == 1:
            raise AuthException()
        if user.status != UserStatus.enable:
            raise BusinessException(code=403, msg="用户已被禁用")
        permissions = await cls._get_user_permissions(db, user)
        return CurrentUser(
            id=user.id, parent_id=user.parent_id, user_level=user.user_level,
            name=user.name, account=user.account, phone=user.phone, email=user.email,
            avatar=user.avatar, status=user.status.value, permissions=permissions,
            is_super_login=payload.get("is_super_login", False), original_user_id=payload.get("original_user_id")
        )
    
    @staticmethod
    async def _get_user_permissions(db: AsyncSession, user: SysUserModel) -> List[str]:
        menus = await sys_menu_crud.get_menus_by_user_id(db, user.id, user.user_level)
        return [m.permission for m in menus if m.permission]


auth_service = AuthService()

