"""
增强的认证服务 - 登录/登出/超级登录
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from jose import JWTError, jwt
import asyncio
import secrets
import hashlib
import logging

from app.config_enhanced import settings
from app.db.models.sys_user import SysUserModel, UserLevel, UserStatus
from app.db.models.sys_log import SysLoginLogModel, LoginType
from app.crud.sys_user_crud import sys_user_crud
from app.crud.sys_menu_crud import sys_menu_crud
from app.schemas.auth import (
    LoginRequest, LoginResponse, CurrentUser, 
    RefreshTokenRequest, SuperLoginRequest, MenuInfo
)
from app.utils.exceptions import (
    BusinessException, AuthException, 
    PermissionDeniedException, UserNotFoundException
)

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = settings.algorithm

# 登录失败计数器（生产环境应使用Redis）
login_attempts = {}


class AuthServiceEnhanced:
    """增强的认证服务"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """密码加密"""
        if len(password) < settings.password_min_length:
            raise ValueError(f"密码长度不能少于{settings.password_min_length}位")
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + (
            expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
        )
        to_encode.update({"exp": expire, "type": "access", "jti": secrets.token_urlsafe(16)})
        return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh", "jti": secrets.token_urlsafe(16)})
        return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
            if payload.get("type") != token_type:
                raise AuthException()
            return payload
        except JWTError as e:
            logger.warning(f"Token验证失败: {str(e)}")
            raise AuthException()
    
    @classmethod
    def _check_login_attempts(cls, account: str, ip: str) -> bool:
        """检查登录尝试次数"""
        key = f"{account}:{ip}"
        attempts = login_attempts.get(key, {"count": 0, "last_attempt": None})
        
        # 如果超过最大尝试次数且在锁定时间内
        if (attempts["count"] >= settings.max_login_attempts and 
            attempts["last_attempt"] and 
            datetime.now() - attempts["last_attempt"] < timedelta(minutes=settings.login_lockout_minutes)):
            return False
        
        return True
    
    @classmethod
    def _record_login_attempt(cls, account: str, ip: str, success: bool):
        """记录登录尝试"""
        key = f"{account}:{ip}"
        if success:
            # 登录成功，清除计数
            login_attempts.pop(key, None)
        else:
            # 登录失败，增加计数
            attempts = login_attempts.get(key, {"count": 0, "last_attempt": None})
            attempts["count"] += 1
            attempts["last_attempt"] = datetime.now()
            login_attempts[key] = attempts
    
    @classmethod
    async def login(
        cls, 
        db: AsyncSession, 
        request: LoginRequest,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> LoginResponse:
        """用户登录 - 增强版本"""
        # 检查登录尝试次数
        if not cls._check_login_attempts(request.account, ip or "unknown"):
            raise BusinessException(code=429, msg="登录尝试次数过多，请稍后再试")
        
        # 查询用户
        user = await sys_user_crud.get_by_account(db, request.account)
        
        # 记录登录日志
        login_log = SysLoginLogModel(
            account=request.account,
            login_type=LoginType.normal,
            ip=ip,
            user_agent=user_agent
        )
        
        # 统一验证逻辑，防止时序攻击
        password_valid = False
        if user:
            password_valid = cls.verify_password(request.password, user.password)
        
        if not user or not password_valid:
            cls._record_login_attempt(request.account, ip or "unknown", False)
            login_log.is_success = 0
            login_log.fail_reason = "账号或密码错误"
            if user:
                login_log.user_id = user.id
            db.add(login_log)
            
            # 添加固定延迟防止暴力破解
            await asyncio.sleep(0.5)
            raise BusinessException(code=400, msg="账号或密码错误")
        
        if user.status != UserStatus.enable:
            cls._record_login_attempt(request.account, ip or "unknown", False)
            login_log.user_id = user.id
            login_log.is_success = 0
            login_log.fail_reason = "用户已禁用"
            db.add(login_log)
            raise BusinessException(code=403, msg="用户已被禁用")
        
        # 记录成功登录
        cls._record_login_attempt(request.account, ip or "unknown", True)
        
        # 获取用户权限
        permissions = await cls._get_user_permissions(db, user)
        
        # 生成令牌
        token_data = {
            "sub": str(user.id),
            "account": user.account,
            "user_level": user.user_level,
            "is_super_login": False
        }
        access_token = cls.create_access_token(token_data)
        refresh_token = cls.create_refresh_token(token_data)
        
        # 更新登录信息
        await sys_user_crud.update(db, id=user.id, obj_in={
            "last_login_at": datetime.now(),
            "last_login_ip": ip
        })
        
        # 记录成功日志
        login_log.user_id = user.id
        login_log.is_success = 1
        db.add(login_log)
        
        logger.info(f"用户登录成功: {user.account} from {ip}")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=CurrentUser(
                id=user.id,
                parent_id=user.parent_id,
                user_level=user.user_level,
                name=user.name,
                account=user.account,
                phone=user.phone,
                email=user.email,
                avatar=user.avatar,
                status=user.status.value,
                permissions=permissions,
                is_super_login=False
            )
        )
    
    @classmethod
    async def super_login(
        cls,
        db: AsyncSession,
        operator: CurrentUser,
        target_user_id: int,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> LoginResponse:
        """超级登录 - 增强版本"""
        # 获取目标用户
        target_user = await sys_user_crud.get_by_id(db, target_user_id)
        if not target_user:
            raise UserNotFoundException()
        
        # 权限检查
        can_super_login = False
        
        if operator.is_super_admin():
            # 超级管理员可以登录用户级别
            can_super_login = target_user.user_level == UserLevel.USER.value
        elif operator.is_user():
            # 用户只能登录其子用户
            can_super_login = (
                target_user.user_level == UserLevel.SUB_USER.value and
                target_user.parent_id == operator.id
            )
        
        if not can_super_login:
            logger.warning(f"超级登录权限不足: 操作者{operator.account} -> 目标{target_user_id}")
            raise PermissionDeniedException()
        
        if target_user.status != UserStatus.enable:
            raise BusinessException(code=403, msg="目标用户已被禁用")
        
        # 获取权限
        permissions = await cls._get_user_permissions(db, target_user)
        
        # 生成超级登录令牌(有效期较短)
        token_data = {
            "sub": str(target_user.id),
            "account": target_user.account,
            "user_level": target_user.user_level,
            "is_super_login": True,
            "original_user_id": operator.id
        }
        access_token = cls.create_access_token(
            token_data,
            expires_delta=timedelta(minutes=settings.super_login_expire_minutes)
        )
        refresh_token = cls.create_refresh_token(token_data)
        
        # 记录超级登录日志
        login_log = SysLoginLogModel(
            user_id=target_user.id,
            account=target_user.account,
            login_type=LoginType.super_,
            operator_id=operator.id,
            is_success=1,
            ip=ip,
            user_agent=user_agent
        )
        db.add(login_log)
        
        logger.info(f"超级登录成功: {operator.account} -> {target_user.account}")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.super_login_expire_minutes * 60,
            user=CurrentUser(
                id=target_user.id,
                parent_id=target_user.parent_id,
                user_level=target_user.user_level,
                name=target_user.name,
                account=target_user.account,
                phone=target_user.phone,
                email=target_user.email,
                avatar=target_user.avatar,
                status=target_user.status.value,
                permissions=permissions,
                is_super_login=True,
                original_user_id=operator.id
            )
        )
    
    @classmethod
    async def refresh_token(
        cls, 
        db: AsyncSession, 
        request: RefreshTokenRequest
    ) -> Dict[str, Any]:
        """刷新令牌 - 增强版本"""
        payload = cls.verify_token(request.refresh_token, token_type="refresh")
        user_id = payload.get("sub")
        
        if not user_id:
            raise AuthException()
        
        user = await sys_user_crud.get_by_id(db, int(user_id))
        if not user or user.is_deleted == 1 or user.status != UserStatus.enable:
            raise AuthException()
        
        # 生成新令牌
        is_super_login = payload.get("is_super_login", False)
        original_user_id = payload.get("original_user_id")
        
        token_data = {
            "sub": str(user.id),
            "account": user.account,
            "user_level": user.user_level,
            "is_super_login": is_super_login,
        }
        if original_user_id:
            token_data["original_user_id"] = original_user_id
        
        access_token = cls.create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": settings.access_token_expire_minutes * 60
        }
    
    @classmethod
    async def get_current_user(cls, db: AsyncSession, token: str) -> CurrentUser:
        """获取当前用户 - 增强版本"""
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
            id=user.id,
            parent_id=user.parent_id,
            user_level=user.user_level,
            name=user.name,
            account=user.account,
            phone=user.phone,
            email=user.email,
            avatar=user.avatar,
            status=user.status.value,
            permissions=permissions,
            is_super_login=payload.get("is_super_login", False),
            original_user_id=payload.get("original_user_id")
        )
    
    @classmethod
    async def get_user_menus(
        cls, 
        db: AsyncSession, 
        user: CurrentUser
    ) -> List[MenuInfo]:
        """获取用户菜单树"""
        menus = await sys_menu_crud.get_menus_by_user_id(
            db, user.id, user.user_level
        )
        return cls._build_menu_tree(menus)
    
    @classmethod
    async def _get_user_permissions(
        cls,
        db: AsyncSession, 
        user: SysUserModel
    ) -> List[str]:
        """获取用户权限列表 - 增强版本"""
        # 使用缓存减少数据库查询
        cache_key = f"user_permissions:{user.id}:{user.user_level}:{user.updated_at.timestamp()}"
        
        # 这里可以集成Redis缓存，暂时使用内存缓存
        if not hasattr(cls, '_permission_cache'):
            cls._permission_cache = {}
        
        # 清理过期缓存
        if hasattr(cls, '_cache_timestamp'):
            if datetime.now() - cls._cache_timestamp > timedelta(minutes=5):
                cls._permission_cache.clear()
                cls._cache_timestamp = datetime.now()
        else:
            cls._cache_timestamp = datetime.now()
        
        if cache_key in cls._permission_cache:
            return cls._permission_cache[cache_key]
        
        menus = await sys_menu_crud.get_menus_by_user_id(
            db, user.id, user.user_level
        )
        permissions = [m.permission for m in menus if m.permission]
        
        # 缓存权限列表
        cls._permission_cache[cache_key] = permissions
        
        return permissions
    
    @staticmethod
    def _build_menu_tree(menus: List) -> List[MenuInfo]:
        """构建菜单树"""
        menu_map = {}
        root_menus = []
        
        # 先创建所有菜单对象
        for menu in menus:
            menu_info = MenuInfo(
                id=menu.id,
                parent_id=menu.parent_id,
                code=menu.code,
                name=menu.name,
                type=menu.type.value if hasattr(menu.type, 'value') else menu.type,
                icon=menu.icon,
                path=menu.path,
                component=menu.component,
                permission=menu.permission,
                sort_order=menu.sort_order,
                is_visible=menu.is_visible,
                children=[]
            )
            menu_map[menu.id] = menu_info
        
        # 构建树形结构
        for menu in menus:
            menu_info = menu_map[menu.id]
            if menu.parent_id == 0 or menu.parent_id not in menu_map:
                root_menus.append(menu_info)
            else:
                parent = menu_map.get(menu.parent_id)
                if parent:
                    parent.children.append(menu_info)
        
        # 按sort_order排序
        def sort_menus(menu_list):
            menu_list.sort(key=lambda x: x.sort_order or 0)
            for menu in menu_list:
                if menu.children:
                    sort_menus(menu.children)
        
        sort_menus(root_menus)
        
        return root_menus


auth_service_enhanced = AuthServiceEnhanced()