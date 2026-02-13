"""
数据同步 CRUD 操作
"""
from typing import Optional, List, Tuple
from datetime import datetime
import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.sync import SyncLogModel, SyncTaskModel, SyncType, SyncStatus


def generate_sync_no() -> str:
    """生成同步单号: SYNC + 日期 + 4位随机"""
    return f"SYNC{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:4].upper()}"


class SyncLogCRUD:
    """同步日志 CRUD"""

    async def create(
        self,
        db: AsyncSession,
        sync_type: SyncType,
        supplier_id: Optional[int] = None,
        card_id: Optional[int] = None,
        iccid: Optional[str] = None,
        triggered_by: Optional[int] = None,
        trigger_type: str = "manual"
    ) -> SyncLogModel:
        """创建同步日志"""
        log = SyncLogModel(
            sync_no=generate_sync_no(),
            sync_type=sync_type,
            supplier_id=supplier_id,
            card_id=card_id,
            iccid=iccid,
            status=SyncStatus.pending,
            triggered_by=triggered_by,
            trigger_type=trigger_type
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    async def update_status(
        self,
        db: AsyncSession,
        log_id: int,
        status: SyncStatus,
        total_count: int = 0,
        success_count: int = 0,
        fail_count: int = 0,
        error_message: Optional[str] = None,
        sync_data: Optional[dict] = None
    ):
        """更新同步状态"""
        log = await self.get_by_id(db, log_id)
        if log:
            log.status = status
            log.total_count = total_count
            log.success_count = success_count
            log.fail_count = fail_count
            log.error_message = error_message
            log.sync_data = sync_data
            
            if status == SyncStatus.running and not log.started_at:
                log.started_at = datetime.now()
            
            if status in [SyncStatus.success, SyncStatus.failed, SyncStatus.partial]:
                log.finished_at = datetime.now()
                if log.started_at:
                    log.duration = int((log.finished_at - log.started_at).total_seconds())
            
            await db.commit()
            await db.refresh(log)
        return log

    async def get_by_id(self, db: AsyncSession, log_id: int) -> Optional[SyncLogModel]:
        """根据ID获取日志"""
        query = select(SyncLogModel).where(
            SyncLogModel.id == log_id,
            SyncLogModel.is_deleted == 0
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        sync_type: Optional[str] = None,
        supplier_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[SyncLogModel], int]:
        """获取同步日志列表"""
        query = select(SyncLogModel).where(SyncLogModel.is_deleted == 0)
        count_query = select(func.count(SyncLogModel.id)).where(SyncLogModel.is_deleted == 0)

        if sync_type:
            query = query.where(SyncLogModel.sync_type == sync_type)
            count_query = count_query.where(SyncLogModel.sync_type == sync_type)

        if supplier_id:
            query = query.where(SyncLogModel.supplier_id == supplier_id)
            count_query = count_query.where(SyncLogModel.supplier_id == supplier_id)

        if status:
            query = query.where(SyncLogModel.status == status)
            count_query = count_query.where(SyncLogModel.status == status)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(SyncLogModel.id.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total


class SyncTaskCRUD:
    """同步任务 CRUD"""

    async def create(
        self,
        db: AsyncSession,
        task_name: str,
        sync_type: SyncType,
        supplier_id: Optional[int] = None,
        cron_expression: Optional[str] = None,
        is_enabled: int = 1,
        created_by: Optional[int] = None,
        remark: Optional[str] = None
    ) -> SyncTaskModel:
        """创建同步任务"""
        task = SyncTaskModel(
            task_name=task_name,
            sync_type=sync_type,
            supplier_id=supplier_id,
            cron_expression=cron_expression,
            is_enabled=is_enabled,
            remark=remark,
            created_by=created_by
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

    async def update(
        self,
        db: AsyncSession,
        task_id: int,
        task_name: Optional[str] = None,
        cron_expression: Optional[str] = None,
        is_enabled: Optional[int] = None,
        remark: Optional[str] = None
    ) -> Optional[SyncTaskModel]:
        """更新同步任务"""
        task = await self.get_by_id(db, task_id)
        if not task:
            return None

        if task_name is not None:
            task.task_name = task_name
        if cron_expression is not None:
            task.cron_expression = cron_expression
        if is_enabled is not None:
            task.is_enabled = is_enabled
        if remark is not None:
            task.remark = remark

        await db.commit()
        await db.refresh(task)
        return task

    async def delete(self, db: AsyncSession, task_id: int) -> bool:
        """删除同步任务"""
        task = await self.get_by_id(db, task_id)
        if not task:
            return False
        task.is_deleted = 1
        await db.commit()
        return True

    async def get_by_id(self, db: AsyncSession, task_id: int) -> Optional[SyncTaskModel]:
        """根据ID获取任务"""
        query = select(SyncTaskModel).where(
            SyncTaskModel.id == task_id,
            SyncTaskModel.is_deleted == 0
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        sync_type: Optional[str] = None,
        is_enabled: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[SyncTaskModel], int]:
        """获取同步任务列表"""
        query = select(SyncTaskModel).where(SyncTaskModel.is_deleted == 0)
        count_query = select(func.count(SyncTaskModel.id)).where(SyncTaskModel.is_deleted == 0)

        if sync_type:
            query = query.where(SyncTaskModel.sync_type == sync_type)
            count_query = count_query.where(SyncTaskModel.sync_type == sync_type)

        if is_enabled is not None:
            query = query.where(SyncTaskModel.is_enabled == is_enabled)
            count_query = count_query.where(SyncTaskModel.is_enabled == is_enabled)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(SyncTaskModel.id.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update_last_run(
        self,
        db: AsyncSession,
        task_id: int,
        status: SyncStatus,
        next_run_at: Optional[datetime] = None
    ):
        """更新任务最后运行信息"""
        task = await self.get_by_id(db, task_id)
        if task:
            task.last_run_at = datetime.now()
            task.last_status = status
            if next_run_at:
                task.next_run_at = next_run_at
            await db.commit()


sync_log_crud = SyncLogCRUD()
sync_task_crud = SyncTaskCRUD()







