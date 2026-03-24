"""
系统用户服务
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.db.models.sys_user import SysUserModel, UserLevel, UserStatus
from app.crud.sys_user_crud import sys_user_crud
from app.schemas.sys_user import UserCreate, UserUpdate, UserInfo, UserQuery, UserPasswordUpdate, UserPasswordReset
from app.schemas.auth import CurrentUser
from app.services.auth_service import AuthService
from app.services.account_balance_service import account_balance_service
from app.utils.exceptions import BusinessException, PermissionDeniedException, UserNotFoundException
from app.utils.const import validate_account, validate_password, validate_phone, validate_email

# 常量定义
UNLIMITED_QUOTA = -1


class SysUserService:
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
        # 如果是三级用户，自动继承父用户菜单并添加项目管理菜单
        elif new_level == UserLevel.SUB_USER.value:
            await cls._assign_default_menus_for_sub_user(db, user.id, parent_id)

        return UserInfo.model_validate(user)
    
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
        return UserInfo.model_validate(user)
    
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
        return UserInfo.model_validate(user)
    
    @classmethod
    async def get_user_list(cls, db: AsyncSession, operator: CurrentUser, query: UserQuery) -> Tuple[List[UserInfo], int]:
        if operator.is_super_admin():
            users, total = await sys_user_crud.get_all_users(db, query)
        elif operator.is_user():
            users, total = await sys_user_crud.get_users_by_parent(db, operator.id, query)
        else:
            return [], 0
        return [UserInfo.model_validate(u) for u in users], total
    
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
        return UserInfo.model_validate(user)

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

            # 默认模块：仪表盘、客户管理、卡片管理、续费管理、流量池管理、设置
            default_modules = ["dashboard", "user", "card", "package", "pool", "system"]

            # 获取这些模块的所有权限ID
            stmt = select(PermissionModel.id).where(
                PermissionModel.module.in_(default_modules),
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

            # 默认菜单code：仪表盘、客户管理、卡片管理、续费管理、流量池管理、系统配置
            default_menu_codes = ["dashboard", "users", "cards", "renewal", "pools", "system_config"]

            # 获取这些菜单的ID
            stmt = select(SysMenuModel.id).where(
                SysMenuModel.code.in_(default_menu_codes),
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
