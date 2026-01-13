"""
系统用户服务
"""
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.sys_user import SysUserModel, UserLevel, UserStatus
from app.crud.sys_user_crud import sys_user_crud
from app.schemas.sys_user import UserCreate, UserUpdate, UserInfo, UserQuery, UserPasswordUpdate, UserPasswordReset
from app.schemas.auth import CurrentUser
from app.services.auth_service import AuthService
from app.utils.exceptions import BusinessException, PermissionDeniedException, UserNotFoundException


class SysUserService:
    @classmethod
    async def create_user(cls, db: AsyncSession, operator: CurrentUser, user_data: UserCreate) -> UserInfo:
        if await sys_user_crud.check_account_exists(db, user_data.account):
            raise BusinessException(code=400, msg="账户已存在")
        
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
    
    @staticmethod
    def _check_manage_permission(operator: CurrentUser, target: SysUserModel):
        if operator.is_super_admin() and target.user_level == UserLevel.USER.value:
            return
        if operator.is_user() and target.user_level == UserLevel.SUB_USER.value and target.parent_id == operator.id:
            return
        raise PermissionDeniedException()
    
    @staticmethod
    async def _check_sub_user_quota(db: AsyncSession, operator: CurrentUser):
        if not operator.is_user():
            return
        user = await sys_user_crud.get_by_id(db, operator.id)
        if not user:
            return
        quota = user.quota or {}
        max_sub_users = quota.get("max_sub_users", 5)
        if max_sub_users == -1:
            return
        current_count = await sys_user_crud.count_children(db, operator.id)
        if current_count >= max_sub_users:
            raise BusinessException(code=400, msg=f"子用户数量已达上限({max_sub_users}个)")


sys_user_service = SysUserService()

