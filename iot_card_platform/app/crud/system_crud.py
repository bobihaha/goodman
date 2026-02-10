"""
系统设置相关的 CRUD 操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.sql import func
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

from app.db.models.sys_log import SysLoginLogModel, SysOperationLogModel, SysConfigModel, SysNotifyTemplateModel


class SysConfigCRUD:
    """系统配置 CRUD"""

    @staticmethod
    async def create(
        db: AsyncSession,
        config_key: str,
        config_value: Optional[str] = None,
        config_type: str = "string",
        description: Optional[str] = None,
        is_public: bool = False
    ) -> SysConfigModel:
        """创建配置"""
        config = SysConfigModel(
            config_key=config_key,
            config_value=config_value,
            config_type=config_type,
            description=description,
            is_public=1 if is_public else 0
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)
        return config

    @staticmethod
    async def get_by_key(db: AsyncSession, config_key: str) -> Optional[SysConfigModel]:
        """根据键获取配置"""
        result = await db.execute(
            select(SysConfigModel).where(
                SysConfigModel.config_key == config_key,
                SysConfigModel.is_deleted == 0
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(db: AsyncSession, config_id: int) -> Optional[SysConfigModel]:
        """根据ID获取配置"""
        result = await db.execute(
            select(SysConfigModel).where(
                SysConfigModel.id == config_id,
                SysConfigModel.is_deleted == 0
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        is_public: Optional[bool] = None
    ) -> List[SysConfigModel]:
        """获取所有配置"""
        query = select(SysConfigModel).where(SysConfigModel.is_deleted == 0)
        
        if is_public is not None:
            query = query.where(SysConfigModel.is_public == (1 if is_public else 0))
        
        query = query.order_by(SysConfigModel.config_key)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update(
        db: AsyncSession,
        config_key: str,
        config_value: Optional[str] = None,
        description: Optional[str] = None,
        is_public: Optional[bool] = None
    ) -> Optional[SysConfigModel]:
        """更新配置"""
        config = await SysConfigCRUD.get_by_key(db, config_key)
        if not config:
            return None

        if config_value is not None:
            config.config_value = config_value
        if description is not None:
            config.description = description
        if is_public is not None:
            config.is_public = 1 if is_public else 0

        await db.commit()
        await db.refresh(config)
        return config

    @staticmethod
    async def batch_update(
        db: AsyncSession,
        configs: Dict[str, Any]
    ) -> int:
        """批量更新配置"""
        updated = 0
        for key, value in configs.items():
            config = await SysConfigCRUD.get_by_key(db, key)
            if config:
                config.config_value = str(value) if value is not None else None
                updated += 1
            else:
                # 自动创建不存在的配置
                await SysConfigCRUD.create(db, key, str(value) if value is not None else None)
                updated += 1
        
        await db.commit()
        return updated

    @staticmethod
    async def delete(db: AsyncSession, config_key: str) -> bool:
        """删除配置"""
        config = await SysConfigCRUD.get_by_key(db, config_key)
        if not config:
            return False
        config.is_deleted = 1
        await db.commit()
        return True


class SysLoginLogCRUD:
    """登录日志 CRUD"""

    @staticmethod
    async def create(
        db: AsyncSession,
        account: str,
        user_id: Optional[int] = None,
        login_type: str = "normal",
        operator_id: Optional[int] = None,
        is_success: bool = True,
        fail_reason: Optional[str] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> SysLoginLogModel:
        """创建登录日志"""
        from app.db.models.sys_log import LoginType
        
        log = SysLoginLogModel(
            user_id=user_id,
            account=account,
            login_type=LoginType(login_type),
            operator_id=operator_id,
            is_success=1 if is_success else 0,
            fail_reason=fail_reason,
            ip=ip,
            user_agent=user_agent
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def get_list(
        db: AsyncSession,
        user_id: Optional[int] = None,
        account: Optional[str] = None,
        is_success: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[SysLoginLogModel], int]:
        """获取登录日志列表"""
        query = select(SysLoginLogModel).where(SysLoginLogModel.is_deleted == 0)
        count_query = select(func.count(SysLoginLogModel.id)).where(SysLoginLogModel.is_deleted == 0)

        if user_id:
            query = query.where(SysLoginLogModel.user_id == user_id)
            count_query = count_query.where(SysLoginLogModel.user_id == user_id)

        if account:
            query = query.where(SysLoginLogModel.account.like(f"%{account}%"))
            count_query = count_query.where(SysLoginLogModel.account.like(f"%{account}%"))

        if is_success is not None:
            query = query.where(SysLoginLogModel.is_success == (1 if is_success else 0))
            count_query = count_query.where(SysLoginLogModel.is_success == (1 if is_success else 0))

        if start_time:
            query = query.where(SysLoginLogModel.created_at >= start_time)
            count_query = count_query.where(SysLoginLogModel.created_at >= start_time)

        if end_time:
            query = query.where(SysLoginLogModel.created_at <= end_time)
            count_query = count_query.where(SysLoginLogModel.created_at <= end_time)

        # 总数
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # 分页
        query = query.order_by(SysLoginLogModel.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        logs = result.scalars().all()

        return list(logs), total


class SysOperationLogCRUD:
    """操作日志 CRUD"""

    @staticmethod
    async def create(
        db: AsyncSession,
        module: str,
        action: str,
        user_id: Optional[int] = None,
        user_name: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        target_name: Optional[str] = None,
        detail: Optional[str] = None,
        ip: Optional[str] = None,
        is_success: bool = True,
        error_msg: Optional[str] = None
    ) -> SysOperationLogModel:
        """创建操作日志"""
        log = SysOperationLogModel(
            user_id=user_id,
            user_name=user_name,
            module=module,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            detail=detail,
            ip=ip,
            is_success=1 if is_success else 0,
            error_msg=error_msg
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def get_list(
        db: AsyncSession,
        user_id: Optional[int] = None,
        module: Optional[str] = None,
        action: Optional[str] = None,
        target_type: Optional[str] = None,
        is_success: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[SysOperationLogModel], int]:
        """获取操作日志列表"""
        query = select(SysOperationLogModel).where(SysOperationLogModel.is_deleted == 0)
        count_query = select(func.count(SysOperationLogModel.id)).where(SysOperationLogModel.is_deleted == 0)

        if user_id:
            query = query.where(SysOperationLogModel.user_id == user_id)
            count_query = count_query.where(SysOperationLogModel.user_id == user_id)

        if module:
            query = query.where(SysOperationLogModel.module == module)
            count_query = count_query.where(SysOperationLogModel.module == module)

        if action:
            query = query.where(SysOperationLogModel.action == action)
            count_query = count_query.where(SysOperationLogModel.action == action)

        if target_type:
            query = query.where(SysOperationLogModel.target_type == target_type)
            count_query = count_query.where(SysOperationLogModel.target_type == target_type)

        if is_success is not None:
            query = query.where(SysOperationLogModel.is_success == (1 if is_success else 0))
            count_query = count_query.where(SysOperationLogModel.is_success == (1 if is_success else 0))

        if start_time:
            query = query.where(SysOperationLogModel.created_at >= start_time)
            count_query = count_query.where(SysOperationLogModel.created_at >= start_time)

        if end_time:
            query = query.where(SysOperationLogModel.created_at <= end_time)
            count_query = count_query.where(SysOperationLogModel.created_at <= end_time)

        # 总数
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # 分页
        query = query.order_by(SysOperationLogModel.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        logs = result.scalars().all()

        return list(logs), total


class SysNotifyTemplateCRUD:
    """通知模板 CRUD"""

    @staticmethod
    async def create(
        db: AsyncSession,
        code: str,
        name: str,
        content: str,
        type: str = "sms",
        title: Optional[str] = None,
        variables: Optional[list] = None,
        is_enabled: bool = True,
        remark: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> SysNotifyTemplateModel:
        """创建通知模板"""
        import json
        from app.db.models.sys_log import NotifyType
        
        template = SysNotifyTemplateModel(
            code=code,
            name=name,
            type=NotifyType(type),
            title=title,
            content=content,
            variables=json.dumps(variables) if variables else None,
            is_enabled=1 if is_enabled else 0,
            remark=remark,
            created_by=created_by
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def get_by_id(db: AsyncSession, template_id: int) -> Optional[SysNotifyTemplateModel]:
        """根据ID获取模板"""
        result = await db.execute(
            select(SysNotifyTemplateModel).where(
                SysNotifyTemplateModel.id == template_id,
                SysNotifyTemplateModel.is_deleted == 0
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_code(db: AsyncSession, code: str) -> Optional[SysNotifyTemplateModel]:
        """根据编码获取模板"""
        result = await db.execute(
            select(SysNotifyTemplateModel).where(
                SysNotifyTemplateModel.code == code,
                SysNotifyTemplateModel.is_deleted == 0
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_list(
        db: AsyncSession,
        type: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[SysNotifyTemplateModel], int]:
        """获取模板列表"""
        from app.db.models.sys_log import NotifyType
        
        query = select(SysNotifyTemplateModel).where(SysNotifyTemplateModel.is_deleted == 0)
        count_query = select(func.count(SysNotifyTemplateModel.id)).where(SysNotifyTemplateModel.is_deleted == 0)

        if type:
            query = query.where(SysNotifyTemplateModel.type == NotifyType(type))
            count_query = count_query.where(SysNotifyTemplateModel.type == NotifyType(type))

        if is_enabled is not None:
            query = query.where(SysNotifyTemplateModel.is_enabled == (1 if is_enabled else 0))
            count_query = count_query.where(SysNotifyTemplateModel.is_enabled == (1 if is_enabled else 0))

        if keyword:
            query = query.where(
                (SysNotifyTemplateModel.name.like(f"%{keyword}%")) |
                (SysNotifyTemplateModel.code.like(f"%{keyword}%"))
            )
            count_query = count_query.where(
                (SysNotifyTemplateModel.name.like(f"%{keyword}%")) |
                (SysNotifyTemplateModel.code.like(f"%{keyword}%"))
            )

        # 总数
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # 分页
        query = query.order_by(SysNotifyTemplateModel.id)
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        templates = result.scalars().all()

        return list(templates), total

    @staticmethod
    async def update(
        db: AsyncSession,
        template_id: int,
        name: Optional[str] = None,
        title: Optional[str] = None,
        content: Optional[str] = None,
        variables: Optional[list] = None,
        is_enabled: Optional[bool] = None,
        remark: Optional[str] = None
    ) -> Optional[SysNotifyTemplateModel]:
        """更新模板"""
        import json
        
        template = await SysNotifyTemplateCRUD.get_by_id(db, template_id)
        if not template:
            return None

        if name is not None:
            template.name = name
        if title is not None:
            template.title = title
        if content is not None:
            template.content = content
        if variables is not None:
            template.variables = json.dumps(variables)
        if is_enabled is not None:
            template.is_enabled = 1 if is_enabled else 0
        if remark is not None:
            template.remark = remark

        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def delete(db: AsyncSession, template_id: int) -> bool:
        """删除模板"""
        template = await SysNotifyTemplateCRUD.get_by_id(db, template_id)
        if not template:
            return False
        template.is_deleted = 1
        await db.commit()
        return True
