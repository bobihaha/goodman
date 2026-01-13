"""
增强的系统用户 CRUD 操作
"""
from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.db.models.sys_user import SysUserModel, UserLevel, UserStatus
from app.schemas.sys_user import UserQuery
from app.crud.base_enhanced import CRUDBaseEnhanced


class SysUserCRUDEnhanced(CRUDBaseEnhanced[SysUserModel]):
    """增强的系统用户 CRUD"""
    
    def __init__(self):
        super().__init__(SysUserModel)

    async def get_by_account(self, db: AsyncSession, account: str) -> Optional[SysUserModel]:
        """根据账户获取用户"""
        try:
            stmt = select(SysUserModel).where(
                SysUserModel.account == account.lower(),  # 统一转为小写查询
                SysUserModel.is_deleted == 0
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise Exception(f"根据账户查询用户失败: {str(e)}")

    async def get_by_phone(self, db: AsyncSession, phone: str) -> Optional[SysUserModel]:
        """根据手机号获取用户"""
        try:
            stmt = select(SysUserModel).where(
                SysUserModel.phone == phone,
                SysUserModel.is_deleted == 0
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise Exception(f"根据手机号查询用户失败: {str(e)}")

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[SysUserModel]:
        """根据邮箱获取用户"""
        try:
            stmt = select(SysUserModel).where(
                SysUserModel.email == email.lower(),  # 统一转为小写查询
                SysUserModel.is_deleted == 0
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise Exception(f"根据邮箱查询用户失败: {str(e)}")

    async def get_users_by_parent(
        self, 
        db: AsyncSession, 
        parent_id: int,
        query: UserQuery
    ) -> Tuple[List[SysUserModel], int]:
        """获取下级用户列表 - 增强版本"""
        try:
            # 构建查询条件
            conditions = [
                SysUserModel.parent_id == parent_id,
                SysUserModel.is_deleted == 0
            ]
            
            # 关键词搜索
            if query.keyword:
                keyword = f"%{query.keyword}%"
                search_conditions = [
                    SysUserModel.name.like(keyword),
                    SysUserModel.account.like(keyword),
                    SysUserModel.phone.like(keyword),
                    SysUserModel.email.like(keyword)
                ]
                conditions.append(or_(*search_conditions))
            
            # 状态过滤
            if query.status:
                conditions.append(SysUserModel.status == query.status)
                
            # 用户层级过滤
            if query.user_level:
                conditions.append(SysUserModel.user_level == query.user_level)
            
            # 创建时间范围过滤
            if query.created_start:
                conditions.append(SysUserModel.created_at >= query.created_start)
            if query.created_end:
                conditions.append(SysUserModel.created_at <= query.created_end)
            
            # 使用增强的分页查询
            search_fields = ['name', 'account', 'phone', 'email']
            users, total = await self.get_with_pagination(
                db,
                page=query.page,
                page_size=query.page_size,
                filters=conditions,
                order_by=SysUserModel.created_at.desc(),
                search_fields=search_fields,
                search_keyword=query.keyword
            )
            
            return users, total
        except Exception as e:
            raise Exception(f"获取下级用户列表失败: {str(e)}")

    async def get_all_users(
        self, 
        db: AsyncSession, 
        query: UserQuery
    ) -> Tuple[List[SysUserModel], int]:
        """获取所有用户列表(超级管理员) - 增强版本"""
        try:
            conditions = [SysUserModel.is_deleted == 0]
            
            # 关键词搜索
            if query.keyword:
                keyword = f"%{query.keyword}%"
                search_conditions = [
                    SysUserModel.name.like(keyword),
                    SysUserModel.account.like(keyword),
                    SysUserModel.phone.like(keyword),
                    SysUserModel.email.like(keyword)
                ]
                conditions.append(or_(*search_conditions))
            
            # 状态过滤
            if query.status:
                conditions.append(SysUserModel.status == query.status)
                
            # 用户层级过滤
            if query.user_level:
                conditions.append(SysUserModel.user_level == query.user_level)
            
            # 创建时间范围过滤
            if query.created_start:
                conditions.append(SysUserModel.created_at >= query.created_start)
            if query.created_end:
                conditions.append(SysUserModel.created_at <= query.created_end)
            
            # 使用增强的分页查询
            search_fields = ['name', 'account', 'phone', 'email']
            users, total = await self.get_with_pagination(
                db,
                page=query.page,
                page_size=query.page_size,
                filters=conditions,
                order_by=(SysUserModel.user_level.asc(), SysUserModel.created_at.desc()),
                search_fields=search_fields,
                search_keyword=query.keyword
            )
            
            return users, total
        except Exception as e:
            raise Exception(f"获取所有用户列表失败: {str(e)}")

    async def count_children(self, db: AsyncSession, parent_id: int) -> int:
        """统计下级用户数量"""
        try:
            stmt = select(func.count(SysUserModel.id)).where(
                SysUserModel.parent_id == parent_id,
                SysUserModel.is_deleted == 0
            )
            result = await db.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            raise Exception(f"统计下级用户数量失败: {str(e)}")

    async def get_children_ids(self, db: AsyncSession, parent_id: int, max_depth: int = 10) -> List[int]:
        """获取所有下级用户ID (迭代方式，防止栈溢出)"""
        try:
            all_ids = []
            current_level = [parent_id]
            depth = 0
            
            while current_level and depth < max_depth:
                next_level = []
                for pid in current_level:
                    stmt = select(SysUserModel.id).where(
                        SysUserModel.parent_id == pid,
                        SysUserModel.is_deleted == 0
                    )
                    result = await db.execute(stmt)
                    child_ids = [row[0] for row in result.fetchall()]
                    all_ids.extend(child_ids)
                    next_level.extend(child_ids)
                
                current_level = next_level
                depth += 1
            
            return all_ids
        except Exception as e:
            raise Exception(f"获取下级用户ID失败: {str(e)}")

    async def check_account_exists(
        self, 
        db: AsyncSession, 
        account: str, 
        exclude_id: Optional[int] = None
    ) -> bool:
        """检查账户是否存在"""
        try:
            conditions = [
                SysUserModel.account == account.lower(),
                SysUserModel.is_deleted == 0
            ]
            if exclude_id:
                conditions.append(SysUserModel.id != exclude_id)
            
            stmt = select(func.count(SysUserModel.id)).where(*conditions)
            result = await db.execute(stmt)
            return (result.scalar() or 0) > 0
        except Exception as e:
            raise Exception(f"检查账户存在性失败: {str(e)}")

    async def check_phone_exists(
        self, 
        db: AsyncSession, 
        phone: str, 
        exclude_id: Optional[int] = None
    ) -> bool:
        """检查手机号是否存在"""
        try:
            conditions = [
                SysUserModel.phone == phone,
                SysUserModel.is_deleted == 0
            ]
            if exclude_id:
                conditions.append(SysUserModel.id != exclude_id)
            
            stmt = select(func.count(SysUserModel.id)).where(*conditions)
            result = await db.execute(stmt)
            return (result.scalar() or 0) > 0
        except Exception as e:
            raise Exception(f"检查手机号存在性失败: {str(e)}")

    async def check_email_exists(
        self, 
        db: AsyncSession, 
        email: str, 
        exclude_id: Optional[int] = None
    ) -> bool:
        """检查邮箱是否存在"""
        try:
            conditions = [
                SysUserModel.email == email.lower(),
                SysUserModel.is_deleted == 0
            ]
            if exclude_id:
                conditions.append(SysUserModel.id != exclude_id)
            
            stmt = select(func.count(SysUserModel.id)).where(*conditions)
            result = await db.execute(stmt)
            return (result.scalar() or 0) > 0
        except Exception as e:
            raise Exception(f"检查邮箱存在性失败: {str(e)}")

    async def get_user_statistics(self, db: AsyncSession, parent_id: Optional[int] = None) -> dict:
        """获取用户统计信息"""
        try:
            conditions = [SysUserModel.is_deleted == 0]
            
            if parent_id is not None:
                conditions.append(SysUserModel.parent_id == parent_id)
            
            # 总用户数
            total_stmt = select(func.count(SysUserModel.id)).where(*conditions)
            total_result = await db.execute(total_stmt)
            total = total_result.scalar() or 0
            
            # 按层级统计
            level_stats = {}
            for level in UserLevel:
                level_conditions = conditions + [SysUserModel.user_level == level.value]
                level_stmt = select(func.count(SysUserModel.id)).where(*level_conditions)
                level_result = await db.execute(level_stmt)
                level_stats[level.name] = level_result.scalar() or 0
            
            # 按状态统计
            status_stats = {}
            for status in UserStatus:
                status_conditions = conditions + [SysUserModel.status == status]
                status_stmt = select(func.count(SysUserModel.id)).where(*status_conditions)
                status_result = await db.execute(status_stmt)
                status_stats[status.value] = status_result.scalar() or 0
            
            # 最近30天注册用户
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_conditions = conditions + [SysUserModel.created_at >= thirty_days_ago]
            recent_stmt = select(func.count(SysUserModel.id)).where(*recent_conditions)
            recent_result = await db.execute(recent_stmt)
            recent_count = recent_result.scalar() or 0
            
            return {
                "total": total,
                "by_level": level_stats,
                "by_status": status_stats,
                "recent_30_days": recent_count
            }
        except Exception as e:
            raise Exception(f"获取用户统计信息失败: {str(e)}")

    async def update_last_login(
        self, 
        db: AsyncSession, 
        user_id: int, 
        ip: Optional[str] = None
    ) -> bool:
        """更新最后登录信息"""
        try:
            update_data = {
                "last_login_at": datetime.now(),
                "updated_at": datetime.now()
            }
            if ip:
                update_data["last_login_ip"] = ip
            
            stmt = (
                update(SysUserModel)
                .where(SysUserModel.id == user_id, SysUserModel.is_deleted == 0)
                .values(**update_data)
            )
            result = await db.execute(stmt)
            return result.rowcount > 0
        except Exception as e:
            raise Exception(f"更新最后登录信息失败: {str(e)}")

    async def batch_update_status(
        self, 
        db: AsyncSession, 
        user_ids: List[int], 
        status: UserStatus
    ) -> int:
        """批量更新用户状态"""
        try:
            conditions = [
                SysUserModel.id.in_(user_ids),
                SysUserModel.is_deleted == 0
            ]
            
            update_data = {
                "status": status,
                "updated_at": datetime.now()
            }
            
            return await self.update_by_filter(db, filters=conditions, obj_in=update_data)
        except Exception as e:
            raise Exception(f"批量更新用户状态失败: {str(e)}")


sys_user_crud_enhanced = SysUserCRUDEnhanced()