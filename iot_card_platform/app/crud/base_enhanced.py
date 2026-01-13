"""
增强的通用 CRUD 基类
"""
from typing import TypeVar, Generic, Type, Optional, List, Any, Dict, Tuple
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
import logging

from app.db.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)

logger = logging.getLogger(__name__)


class CRUDBaseEnhanced(Generic[ModelType]):
    """增强的通用 CRUD 操作基类"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        """根据ID获取"""
        try:
            stmt = select(self.model).where(
                self.model.id == id,
                self.model.is_deleted == 0
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"查询记录失败 ID={id}: {str(e)}")
            raise

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[List] = None,
        order_by: Optional = None
    ) -> List[ModelType]:
        """获取多条记录"""
        try:
            stmt = select(self.model).where(self.model.is_deleted == 0)
            if filters:
                for f in filters:
                    stmt = stmt.where(f)
            if order_by:
                stmt = stmt.order_by(order_by)
            stmt = stmt.offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"查询多条记录失败: {str(e)}")
            raise

    async def get_with_pagination(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[List] = None,
        order_by: Optional = None,
        search_fields: Optional[List[str]] = None,
        search_keyword: Optional[str] = None
    ) -> Tuple[List[ModelType], int]:
        """
        分页查询
        Returns: (记录列表, 总数)
        """
        try:
            conditions = [self.model.is_deleted == 0]
            
            # 添加过滤条件
            if filters:
                conditions.extend(filters)
            
            # 添加搜索条件
            if search_keyword and search_fields:
                search_conditions = []
                for field in search_fields:
                    if hasattr(self.model, field):
                        field_attr = getattr(self.model, field)
                        search_conditions.append(field_attr.like(f"%{search_keyword}%"))
                if search_conditions:
                    conditions.append(or_(*search_conditions))
            
            # 查询总数
            count_stmt = select(func.count(self.model.id)).where(*conditions)
            total_result = await db.execute(count_stmt)
            total = total_result.scalar() or 0
            
            # 查询列表
            offset = (page - 1) * page_size
            list_stmt = select(self.model).where(*conditions)
            
            if order_by is not None:
                if isinstance(order_by, (list, tuple)):
                    list_stmt = list_stmt.order_by(*order_by)
                else:
                    list_stmt = list_stmt.order_by(order_by)
            
            list_stmt = list_stmt.offset(offset).limit(page_size)
            list_result = await db.execute(list_stmt)
            items = list(list_result.scalars().all())
            
            return items, total
        except Exception as e:
            logger.error(f"分页查询失败: {str(e)}")
            raise

    async def count(
        self, 
        db: AsyncSession, 
        filters: Optional[List] = None
    ) -> int:
        """统计数量"""
        try:
            stmt = select(func.count(self.model.id)).where(self.model.is_deleted == 0)
            if filters:
                for f in filters:
                    stmt = stmt.where(f)
            result = await db.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"统计数量失败: {str(e)}")
            raise

    async def create(self, db: AsyncSession, obj_in: Dict[str, Any]) -> ModelType:
        """创建记录"""
        try:
            # 添加创建时间等默认值
            if 'created_at' not in obj_in:
                obj_in['created_at'] = func.now()
            if 'updated_at' not in obj_in:
                obj_in['updated_at'] = func.now()
            
            db_obj = self.model(**obj_in)
            db.add(db_obj)
            await db.flush()
            await db.refresh(db_obj)
            
            logger.info(f"创建记录成功: {self.model.__tablename__} ID={db_obj.id}")
            return db_obj
        except Exception as e:
            logger.error(f"创建记录失败: {str(e)}")
            await db.rollback()
            raise

    async def create_batch(
        self, 
        db: AsyncSession, 
        obj_list: List[Dict[str, Any]]
    ) -> List[ModelType]:
        """批量创建记录"""
        try:
            db_objects = []
            for obj_in in obj_list:
                if 'created_at' not in obj_in:
                    obj_in['created_at'] = func.now()
                if 'updated_at' not in obj_in:
                    obj_in['updated_at'] = func.now()
                db_objects.append(self.model(**obj_in))
            
            db.add_all(db_objects)
            await db.flush()
            
            # 刷新所有对象以获取ID
            for obj in db_objects:
                await db.refresh(obj)
            
            logger.info(f"批量创建记录成功: {self.model.__tablename__} 数量={len(db_objects)}")
            return db_objects
        except Exception as e:
            logger.error(f"批量创建记录失败: {str(e)}")
            await db.rollback()
            raise

    async def update(
        self, 
        db: AsyncSession, 
        *, 
        id: int, 
        obj_in: Dict[str, Any]
    ) -> Optional[ModelType]:
        """更新记录"""
        try:
            # 添加更新时间
            obj_in['updated_at'] = func.now()
            
            stmt = (
                update(self.model)
                .where(self.model.id == id, self.model.is_deleted == 0)
                .values(**obj_in)
            )
            result = await db.execute(stmt)
            
            if result.rowcount == 0:
                logger.warning(f"更新记录失败，记录不存在或已删除: {self.model.__tablename__} ID={id}")
                return None
            
            updated_obj = await self.get_by_id(db, id)
            logger.info(f"更新记录成功: {self.model.__tablename__} ID={id}")
            return updated_obj
        except Exception as e:
            logger.error(f"更新记录失败 ID={id}: {str(e)}")
            await db.rollback()
            raise

    async def update_by_filter(
        self,
        db: AsyncSession,
        *,
        filters: List,
        obj_in: Dict[str, Any]
    ) -> int:
        """根据条件批量更新"""
        try:
            obj_in['updated_at'] = func.now()
            
            conditions = [self.model.is_deleted == 0] + filters
            stmt = (
                update(self.model)
                .where(*conditions)
                .values(**obj_in)
            )
            result = await db.execute(stmt)
            
            logger.info(f"批量更新记录成功: {self.model.__tablename__} 影响行数={result.rowcount}")
            return result.rowcount
        except Exception as e:
            logger.error(f"批量更新记录失败: {str(e)}")
            await db.rollback()
            raise

    async def delete(self, db: AsyncSession, id: int) -> bool:
        """软删除"""
        try:
            stmt = (
                update(self.model)
                .where(self.model.id == id)
                .values(is_deleted=1, updated_at=func.now())
            )
            result = await db.execute(stmt)
            
            if result.rowcount > 0:
                logger.info(f"软删除记录成功: {self.model.__tablename__} ID={id}")
                return True
            else:
                logger.warning(f"软删除记录失败，记录不存在: {self.model.__tablename__} ID={id}")
                return False
        except Exception as e:
            logger.error(f"软删除记录失败 ID={id}: {str(e)}")
            await db.rollback()
            raise

    async def delete_by_filter(self, db: AsyncSession, filters: List) -> int:
        """根据条件批量软删除"""
        try:
            conditions = [self.model.is_deleted == 0] + filters
            stmt = (
                update(self.model)
                .where(*conditions)
                .values(is_deleted=1, updated_at=func.now())
            )
            result = await db.execute(stmt)
            
            logger.info(f"批量软删除记录成功: {self.model.__tablename__} 影响行数={result.rowcount}")
            return result.rowcount
        except Exception as e:
            logger.error(f"批量软删除记录失败: {str(e)}")
            await db.rollback()
            raise

    async def hard_delete(self, db: AsyncSession, id: int) -> bool:
        """硬删除"""
        try:
            stmt = delete(self.model).where(self.model.id == id)
            result = await db.execute(stmt)
            
            if result.rowcount > 0:
                logger.info(f"硬删除记录成功: {self.model.__tablename__} ID={id}")
                return True
            else:
                logger.warning(f"硬删除记录失败，记录不存在: {self.model.__tablename__} ID={id}")
                return False
        except Exception as e:
            logger.error(f"硬删除记录失败 ID={id}: {str(e)}")
            await db.rollback()
            raise

    async def exists(self, db: AsyncSession, id: int) -> bool:
        """检查记录是否存在"""
        try:
            stmt = select(func.count(self.model.id)).where(
                self.model.id == id,
                self.model.is_deleted == 0
            )
            result = await db.execute(stmt)
            return (result.scalar() or 0) > 0
        except Exception as e:
            logger.error(f"检查记录存在性失败 ID={id}: {str(e)}")
            raise

    async def get_by_field(
        self, 
        db: AsyncSession, 
        field_name: str, 
        field_value: Any
    ) -> Optional[ModelType]:
        """根据字段值获取记录"""
        try:
            if not hasattr(self.model, field_name):
                raise ValueError(f"模型 {self.model.__name__} 没有字段 {field_name}")
            
            field_attr = getattr(self.model, field_name)
            stmt = select(self.model).where(
                field_attr == field_value,
                self.model.is_deleted == 0
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"根据字段查询失败 {field_name}={field_value}: {str(e)}")
            raise

    async def execute_raw_sql(
        self, 
        db: AsyncSession, 
        sql: str, 
        params: Optional[Dict] = None
    ) -> Any:
        """执行原生SQL"""
        try:
            result = await db.execute(text(sql), params or {})
            return result
        except Exception as e:
            logger.error(f"执行原生SQL失败: {sql} - {str(e)}")
            raise