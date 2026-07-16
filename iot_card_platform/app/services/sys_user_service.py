"""
系统用户服务
"""
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple, Optional
import secrets
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.db.models.sys_user import SysUserModel, UserLevel, UserStatus
from app.crud.sys_user_crud import sys_user_crud
from app.schemas.sys_user import (
    UserCreate, UserUpdate, UserInfo, UserQuery, UserPasswordUpdate,
    UserPasswordReset, UserH5Config, UserH5ConfigUpdate,
    UserOpenApiCredential, UserOpenApiCredentialResetResponse
)
from app.schemas.auth import CurrentUser
from app.services.auth_service import AuthService
from app.services.account_balance_service import account_balance_service
from app.utils.exceptions import BusinessException, PermissionDeniedException, UserNotFoundException
from app.utils.const import validate_account, validate_password, validate_phone, validate_email, encrypt_secret

# 常量定义
UNLIMITED_QUOTA = -1


class SysUserService:
    DEFAULT_USER_PERMISSION_MODULES = ["dashboard", "user", "card", "renewal", "pool", "system"]
    DEFAULT_USER_MENU_CODES = [
        "dashboard",
        "card_manage",
        "card_list",
        "user_manage",
        "user_list",
        "renewal_manage",
        "pool_manage",
        "pool_list",
        "system_manage",
    ]

    @staticmethod
    def _mask_open_api_secret(secret: Optional[str]) -> Optional[str]:
        if not secret:
            return None
        if len(secret) <= 8:
            return "*" * len(secret)
        return f"{secret[:4]}{'*' * (len(secret) - 8)}{secret[-4:]}"

    @classmethod
    def _build_open_api_config(cls, user: SysUserModel) -> UserOpenApiCredential:
        secret_value = None
        if user.open_api_app_secret:
            from app.utils.const import decrypt_secret
            secret_value = decrypt_secret(user.open_api_app_secret)
        return UserOpenApiCredential(
            enabled=bool(user.open_api_enabled),
            app_id=user.open_api_app_id,
            app_secret_masked=cls._mask_open_api_secret(secret_value),
            has_app_secret=bool(secret_value),
            last_reset_at=user.open_api_last_reset_at
        )

    @staticmethod
    def _build_h5_config(user: SysUserModel) -> UserH5Config:
        return UserH5Config(
            enabled=bool(user.h5_enabled),
            slug=user.h5_slug,
            title=user.h5_title,
            logo=user.h5_logo,
            banner=user.h5_banner,
            notice=user.h5_notice,
            contact_phone=user.h5_contact_phone,
            contact_wechat=user.h5_contact_wechat,
            theme=user.h5_theme,
            allow_suspend=bool(user.h5_allow_suspend),
            allow_resume=bool(user.h5_allow_resume),
            allow_remark=bool(user.h5_allow_remark),
            require_verify=bool(user.h5_require_verify),
            status=user.h5_status or "enabled",
            last_reset_at=user.h5_last_reset_at
        )

    @classmethod
    def _build_user_info(cls, user: SysUserModel, recommended_channel_name: Optional[str] = None) -> UserInfo:
        payload = {
            "id": user.id,
            "parent_id": user.parent_id,
            "user_level": user.user_level,
            "name": user.name,
            "account": user.account,
            "phone": user.phone,
            "email": user.email,
            "avatar": user.avatar,
            "alert_notify": user.alert_notify,
            "quota": user.quota,
            "remark": user.remark,
            "recommended_channel_name": recommended_channel_name,
            "status": user.status.value if hasattr(user.status, "value") else user.status,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
            "h5": cls._build_h5_config(user),
            "open_api": cls._build_open_api_config(user)
        }
        return UserInfo.model_validate(payload)

    @staticmethod
    async def _generate_unique_h5_slug(db: AsyncSession, exclude_id: Optional[int] = None) -> str:
        for _ in range(10):
            slug = secrets.token_urlsafe(6).replace("-", "").replace("_", "")[:8]
            if slug and not await sys_user_crud.check_h5_slug_exists(db, slug, exclude_id=exclude_id):
                return slug
        raise BusinessException(code=500, msg="生成H5地址失败，请重试")

    @staticmethod
    async def _generate_unique_open_api_app_id(db: AsyncSession, exclude_id: Optional[int] = None) -> str:
        for _ in range(10):
            app_id = f"APP{secrets.token_hex(8).upper()}"
            if not await sys_user_crud.check_open_api_app_id_exists(db, app_id, exclude_id=exclude_id):
                return app_id
        raise BusinessException(code=500, msg="生成APPID失败，请重试")

    @staticmethod
    def _generate_open_api_secret() -> str:
        return secrets.token_urlsafe(24).replace("-", "").replace("_", "")

    @classmethod
    async def _ensure_open_api_credentials(
        cls,
        db: AsyncSession,
        user: SysUserModel
    ) -> tuple[SysUserModel, Optional[str]]:
        if user.user_level != UserLevel.USER.value:
            return user, None
        if user.open_api_app_id and user.open_api_app_secret:
            return user, None

        secret = cls._generate_open_api_secret()
        update_data = {
            "open_api_app_id": user.open_api_app_id or await cls._generate_unique_open_api_app_id(db, exclude_id=user.id),
            "open_api_app_secret": encrypt_secret(secret),
            "open_api_enabled": 1,
            "open_api_last_reset_at": datetime.now()
        }
        updated_user = await sys_user_crud.update(db, id=user.id, obj_in=update_data)
        return updated_user, secret

    @staticmethod
    def _check_open_api_manage_permission(operator: CurrentUser, target: SysUserModel):
        if target.user_level != UserLevel.USER.value:
            raise BusinessException(code=400, msg="仅一级用户支持开放API凭证")
        if operator.id == target.id:
            return
        if operator.is_super_admin():
            return
        raise PermissionDeniedException()

    @classmethod
    async def create_user(cls, db: AsyncSession, operator: CurrentUser, user_data: UserCreate) -> UserInfo:
        if await sys_user_crud.check_account_exists(db, user_data.account):
            raise BusinessException(code=400, msg="账户已存在")

        # 验证账户名格式
        if not validate_account(user_data.account):
            raise BusinessException(code=400, msg="账户名格式错误：4-20位字母数字下划线")

        # 验证密码强度
        if not validate_password(user_data.password):
            raise BusinessException(code=400, msg="密码必须包含大小写字母和数字，长度8-20位")

        # 验证手机号格式
        if user_data.phone and not validate_phone(user_data.phone):
            raise BusinessException(code=400, msg="手机号格式错误")

        # 验证邮箱格式
        if user_data.email and not validate_email(user_data.email):
            raise BusinessException(code=400, msg="邮箱格式错误")

        if operator.is_super_admin():
            new_level = UserLevel.USER.value
            parent_id = operator.id
        elif operator.is_user():
            new_level = UserLevel.SUB_USER.value
            parent_id = operator.id
            await cls._check_sub_user_quota(db, operator)
        else:
            raise PermissionDeniedException()

        user_dict = user_data.model_dump()
        user_dict["password"] = AuthService.hash_password(user_data.password)
        user_dict["user_level"] = new_level
        user_dict["parent_id"] = parent_id
        user_dict["created_by"] = operator.id

        user = await sys_user_crud.create(db, user_dict)

        # 如果是二级用户，分配默认权限和菜单
        if new_level == UserLevel.USER.value:
            await cls._assign_default_permissions_for_user(db, user.id)
            await cls._assign_default_menus_for_user(db, user.id)
            user, _ = await cls._ensure_open_api_credentials(db, user)
        # 如果是三级用户，自动继承父用户菜单并添加项目管理菜单
        elif new_level == UserLevel.SUB_USER.value:
            await cls._assign_default_menus_for_sub_user(db, user.id, parent_id)

        return cls._build_user_info(user)
    
    @classmethod
    async def update_user(cls, db: AsyncSession, operator: CurrentUser, user_id: int, user_data: UserUpdate) -> UserInfo:
        target_user = await sys_user_crud.get_by_id(db, user_id)
        if not target_user:
            raise UserNotFoundException()
        cls._check_manage_permission(operator, target_user)
        
        update_dict = user_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise BusinessException(code=400, msg="没有需要更新的字段")
        
        user = await sys_user_crud.update(db, id=user_id, obj_in=update_dict)
        return cls._build_user_info(user)
    
    @classmethod
    async def delete_user(cls, db: AsyncSession, operator: CurrentUser, user_id: int) -> bool:
        target_user = await sys_user_crud.get_by_id(db, user_id)
        if not target_user:
            raise UserNotFoundException()
        cls._check_manage_permission(operator, target_user)

        child_count = await sys_user_crud.count_children(db, user_id)
        if child_count > 0:
            raise BusinessException(code=400, msg="该用户下有子用户，无法删除")

        # 检查卡片
        from app.crud.iot_card_crud import iot_card_crud
        from sqlalchemy import select, func
        from app.db.models.iot_card import IotCardModel
        card_count_stmt = select(func.count(IotCardModel.id)).where(IotCardModel.user_id == user_id, IotCardModel.is_deleted == 0)
        card_count = (await db.execute(card_count_stmt)).scalar() or 0
        if card_count > 0:
            raise BusinessException(code=400, msg=f"该用户下有{card_count}张卡片，无法删除")

        return await sys_user_crud.delete(db, user_id)
    
    @classmethod
    async def get_user_detail(cls, db: AsyncSession, operator: CurrentUser, user_id: int) -> UserInfo:
        user = await sys_user_crud.get_by_id(db, user_id)
        if not user:
            raise UserNotFoundException()
        if user.id != operator.id:
            cls._check_manage_permission(operator, user)
        return cls._build_user_info(user)
    
    @classmethod
    async def get_user_list(cls, db: AsyncSession, operator: CurrentUser, query: UserQuery) -> Tuple[List[UserInfo], int]:
        if operator.is_super_admin():
            users, total = await sys_user_crud.get_all_users(db, query)
            channel_map = {}
            if users:
                from app.db.models.channel import ChannelCustomerRelationModel, ChannelPartnerModel
                rows = await db.execute(
                    select(ChannelCustomerRelationModel.user_id, ChannelPartnerModel.name)
                    .join(ChannelPartnerModel, ChannelPartnerModel.id == ChannelCustomerRelationModel.channel_id)
                    .where(
                        ChannelCustomerRelationModel.user_id.in_([user.id for user in users]),
                        ChannelCustomerRelationModel.is_deleted == 0,
                    )
                )
                channel_map = dict(rows.all())
            return [cls._build_user_info(user, channel_map.get(user.id)) for user in users], total
        elif operator.is_user():
            users, total = await sys_user_crud.get_users_by_parent(db, operator.id, query)
        else:
            return [], 0
        return [cls._build_user_info(u) for u in users], total
    
    @classmethod
    async def change_password(cls, db: AsyncSession, operator: CurrentUser, password_data: UserPasswordUpdate) -> bool:
        if not validate_password(password_data.new_password):
            raise BusinessException(code=400, msg="密码必须包含大小写字母和数字，长度8-20位")
        user = await sys_user_crud.get_by_id(db, operator.id)
        if not user:
            raise UserNotFoundException()
        if not AuthService.verify_password(password_data.old_password, user.password):
            raise BusinessException(code=400, msg="旧密码错误")
        new_password_hash = AuthService.hash_password(password_data.new_password)
        await sys_user_crud.update(db, id=operator.id, obj_in={"password": new_password_hash})
        return True

    @classmethod
    async def reset_password(cls, db: AsyncSession, operator: CurrentUser, user_id: int, password_data: UserPasswordReset) -> bool:
        if not validate_password(password_data.new_password):
            raise BusinessException(code=400, msg="密码必须包含大小写字母和数字，长度8-20位")
        target_user = await sys_user_crud.get_by_id(db, user_id)
        if not target_user:
            raise UserNotFoundException()
        cls._check_manage_permission(operator, target_user)
        new_password_hash = AuthService.hash_password(password_data.new_password)
        await sys_user_crud.update(db, id=user_id, obj_in={"password": new_password_hash})
        return True
    
    @classmethod
    async def change_status(cls, db: AsyncSession, operator: CurrentUser, user_id: int, status: UserStatus) -> UserInfo:
        target_user = await sys_user_crud.get_by_id(db, user_id)
        if not target_user:
            raise UserNotFoundException()
        cls._check_manage_permission(operator, target_user)
        user = await sys_user_crud.update(db, id=user_id, obj_in={"status": status})
        return cls._build_user_info(user)

    @classmethod
    async def get_h5_detail(cls, db: AsyncSession, operator: CurrentUser, user_id: int) -> UserH5Config:
        target_user = await sys_user_crud.get_by_id(db, user_id)
        if not target_user:
            raise UserNotFoundException()
        cls._check_manage_permission(operator, target_user)
        return cls._build_h5_config(target_user)

    @classmethod
    async def generate_h5(cls, db: AsyncSession, operator: CurrentUser, user_id: int) -> UserH5Config:
        target_user = await sys_user_crud.get_by_id(db, user_id)
        if not target_user:
            raise UserNotFoundException()
        cls._check_manage_permission(operator, target_user)
        if target_user.user_level == UserLevel.SUPER_ADMIN.value:
            raise BusinessException(code=400, msg="超级管理员不支持生成H5")

        slug = target_user.h5_slug or await cls._generate_unique_h5_slug(db, exclude_id=target_user.id)
        update_data = {
            "h5_enabled": 1,
            "h5_slug": slug,
            "h5_title": target_user.h5_title or f"{target_user.name}自助服务",
            "h5_status": "enabled",
            "h5_allow_suspend": target_user.h5_allow_suspend if target_user.h5_allow_suspend is not None else 1,
            "h5_allow_resume": target_user.h5_allow_resume if target_user.h5_allow_resume is not None else 1,
            "h5_allow_remark": target_user.h5_allow_remark if target_user.h5_allow_remark is not None else 1,
            "h5_require_verify": target_user.h5_require_verify if target_user.h5_require_verify is not None else 0,
            "h5_last_reset_at": datetime.now()
        }
        user = await sys_user_crud.update(db, id=user_id, obj_in=update_data)
        return cls._build_h5_config(user)

    @classmethod
    async def update_h5_config(
        cls,
        db: AsyncSession,
        operator: CurrentUser,
        user_id: int,
        config: UserH5ConfigUpdate
    ) -> UserH5Config:
        target_user = await sys_user_crud.get_by_id(db, user_id)
        if not target_user:
            raise UserNotFoundException()
        cls._check_manage_permission(operator, target_user)
        if target_user.user_level == UserLevel.SUPER_ADMIN.value:
            raise BusinessException(code=400, msg="超级管理员不支持配置H5")

        update_dict = config.model_dump(exclude_unset=True)
        mapped = {}
        field_mapping = {
            "title": "h5_title",
            "logo": "h5_logo",
            "banner": "h5_banner",
            "notice": "h5_notice",
            "contact_phone": "h5_contact_phone",
            "contact_wechat": "h5_contact_wechat",
            "theme": "h5_theme",
            "allow_suspend": "h5_allow_suspend",
            "allow_resume": "h5_allow_resume",
            "allow_remark": "h5_allow_remark",
            "require_verify": "h5_require_verify",
            "status": "h5_status"
        }
        for key, value in update_dict.items():
            mapped[field_mapping[key]] = int(value) if isinstance(value, bool) else value

        if not mapped:
            raise BusinessException(code=400, msg="没有需要更新的H5配置")

        user = await sys_user_crud.update(db, id=user_id, obj_in=mapped)
        return cls._build_h5_config(user)

    @classmethod
    async def reset_h5(cls, db: AsyncSession, operator: CurrentUser, user_id: int) -> UserH5Config:
        target_user = await sys_user_crud.get_by_id(db, user_id)
        if not target_user:
            raise UserNotFoundException()
        cls._check_manage_permission(operator, target_user)
        if target_user.user_level == UserLevel.SUPER_ADMIN.value:
            raise BusinessException(code=400, msg="超级管理员不支持重置H5地址")

        slug = await cls._generate_unique_h5_slug(db, exclude_id=user_id)
        user = await sys_user_crud.update(
            db,
            id=user_id,
            obj_in={
                "h5_enabled": 1,
                "h5_slug": slug,
                "h5_status": "enabled",
                "h5_last_reset_at": datetime.now()
            }
        )
        return cls._build_h5_config(user)

    @classmethod
    async def change_h5_status(cls, db: AsyncSession, operator: CurrentUser, user_id: int, status: str) -> UserH5Config:
        target_user = await sys_user_crud.get_by_id(db, user_id)
        if not target_user:
            raise UserNotFoundException()
        cls._check_manage_permission(operator, target_user)
        if target_user.user_level == UserLevel.SUPER_ADMIN.value:
            raise BusinessException(code=400, msg="超级管理员不支持设置H5状态")
        user = await sys_user_crud.update(
            db,
            id=user_id,
            obj_in={"h5_status": status, "h5_enabled": 1 if status == "enabled" else 0}
        )
        return cls._build_h5_config(user)

    @classmethod
    async def get_open_api_credentials(
        cls,
        db: AsyncSession,
        operator: CurrentUser,
        user_id: int
    ) -> UserOpenApiCredential:
        target_user = await sys_user_crud.get_by_id(db, user_id)
        if not target_user:
            raise UserNotFoundException()
        cls._check_open_api_manage_permission(operator, target_user)
        target_user, _ = await cls._ensure_open_api_credentials(db, target_user)
        return cls._build_open_api_config(target_user)

    @classmethod
    async def reset_open_api_credentials(
        cls,
        db: AsyncSession,
        operator: CurrentUser,
        user_id: int
    ) -> UserOpenApiCredentialResetResponse:
        target_user = await sys_user_crud.get_by_id(db, user_id)
        if not target_user:
            raise UserNotFoundException()
        cls._check_open_api_manage_permission(operator, target_user)

        app_id = target_user.open_api_app_id or await cls._generate_unique_open_api_app_id(db, exclude_id=target_user.id)
        secret = cls._generate_open_api_secret()
        reset_at = datetime.now()
        await sys_user_crud.update(
            db,
            id=user_id,
            obj_in={
                "open_api_app_id": app_id,
                "open_api_app_secret": encrypt_secret(secret),
                "open_api_enabled": 1,
                "open_api_last_reset_at": reset_at
            }
        )
        return UserOpenApiCredentialResetResponse(
            enabled=True,
            app_id=app_id,
            app_secret=secret,
            last_reset_at=reset_at
        )

    @classmethod
    async def grant_balance(
        cls,
        db: AsyncSession,
        operator: CurrentUser,
        user_id: int,
        amount: float,
        remark: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> dict:
        normalized_amount = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return await account_balance_service.grant_balance(
            db=db,
            operator=operator,
            target_user_id=user_id,
            amount=normalized_amount,
            remark=remark,
            request_id=request_id
        )
    
    @staticmethod
    def _check_manage_permission(operator: CurrentUser, target: SysUserModel):
        # 允许用户编辑自己的信息
        if operator.id == target.id:
            return
        if operator.is_super_admin() and target.user_level == UserLevel.USER.value:
            return
        if operator.is_user() and target.user_level == UserLevel.SUB_USER.value and target.parent_id == operator.id:
            return
        raise PermissionDeniedException()
    
    @staticmethod
    async def _check_sub_user_quota(db: AsyncSession, operator: CurrentUser):
        if not operator.is_user():
            return
        from sqlalchemy import select, func
        from app.db.models.sys_user import SysUserModel

        # 使用 SELECT FOR UPDATE 锁定父用户记录，防止并发创建
        stmt = select(SysUserModel).where(
            SysUserModel.id == operator.id,
            SysUserModel.is_deleted == 0
        ).with_for_update()
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return
        quota = user.quota or {}
        max_sub_users = quota.get("max_sub_users", 5)
        if max_sub_users == UNLIMITED_QUOTA:
            return
        current_count = await sys_user_crud.count_children(db, operator.id)
        if current_count >= max_sub_users:
            raise BusinessException(code=400, msg=f"子用户数量已达上限({max_sub_users}个)")

    @staticmethod
    async def _assign_default_permissions_for_user(db: AsyncSession, user_id: int):
        """为二级用户分配默认权限"""
        try:
            from app.crud.permission_crud import user_permission_crud
            from sqlalchemy import select
            from app.db.models.permission import PermissionModel

            # 获取这些模块的所有权限ID
            stmt = select(PermissionModel.id).where(
                PermissionModel.module.in_(SysUserService.DEFAULT_USER_PERMISSION_MODULES),
                PermissionModel.is_deleted == 0
            )
            result = await db.execute(stmt)
            permission_ids = list(result.scalars().all())

            # 批量分配权限（如果有权限数据）
            if permission_ids:
                await user_permission_crud.assign_permissions(db, user_id, permission_ids)
        except SQLAlchemyError as e:
            logging.error(f"为用户 {user_id} 分配默认权限失败: {str(e)}")

    @staticmethod
    async def _assign_default_menus_for_user(db: AsyncSession, user_id: int):
        """为二级用户分配默认菜单"""
        try:
            from sqlalchemy import select, insert
            from app.db.models.sys_menu import SysUserMenuModel, SysMenuModel

            # 获取这些菜单的ID
            stmt = select(SysMenuModel.id).where(
                SysMenuModel.code.in_(SysUserService.DEFAULT_USER_MENU_CODES),
                SysMenuModel.is_deleted == 0
            )
            result = await db.execute(stmt)
            menu_ids = list(result.scalars().all())

            # 批量插入
            if menu_ids:
                await db.execute(
                    insert(SysUserMenuModel),
                    [{"user_id": user_id, "menu_id": mid} for mid in menu_ids]
                )
                await db.commit()
        except SQLAlchemyError as e:
            logging.error(f"为用户 {user_id} 分配默认菜单失败: {str(e)}")

    @staticmethod
    async def _assign_default_menus_for_sub_user(db: AsyncSession, user_id: int, parent_id: int):
        """为三级用户自动分配菜单：继承父用户菜单 + 项目管理菜单"""
        from app.crud.sys_menu_crud import sys_user_menu_crud, sys_menu_crud
        from sqlalchemy import select, insert
        from app.db.models.sys_menu import SysUserMenuModel

        # 获取父用户的所有菜单
        parent_menu_ids = await sys_user_menu_crud.get_user_menu_ids(db, parent_id)

        # 获取项目管理菜单ID
        project_menu = await db.execute(select(sys_menu_crud.model).where(sys_menu_crud.model.code == 'projects'))
        project_menu_obj = project_menu.scalar_one_or_none()

        # 合并菜单ID（去重）
        menu_ids = set(parent_menu_ids)
        if project_menu_obj:
            menu_ids.add(project_menu_obj.id)

        # 批量插入
        if menu_ids:
            await db.execute(
                insert(SysUserMenuModel),
                [{"user_id": user_id, "menu_id": mid} for mid in menu_ids]
            )
            await db.commit()


sys_user_service = SysUserService()
