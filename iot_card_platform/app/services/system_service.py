"""
系统设置服务层
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

from app.crud.system_crud import SysConfigCRUD, SysLoginLogCRUD, SysOperationLogCRUD, SysNotifyTemplateCRUD
from app.db.models.sys_log import SysConfigModel, SysNotifyTemplateModel
from app.schemas.system import ConfigCreate, ConfigUpdate, NotifyTemplateCreate, NotifyTemplateUpdate, AlertRules


class SystemConfigService:
    """系统配置服务"""

    @staticmethod
    async def create_config(
        db: AsyncSession,
        data: ConfigCreate
    ) -> SysConfigModel:
        """创建配置"""
        return await SysConfigCRUD.create(
            db=db,
            config_key=data.config_key,
            config_value=data.config_value,
            config_type=data.config_type,
            description=data.description,
            is_public=data.is_public
        )

    @staticmethod
    async def get_config(db: AsyncSession, config_key: str) -> Optional[dict]:
        """获取单个配置"""
        config = await SysConfigCRUD.get_by_key(db, config_key)
        return config.to_dict() if config else None

    @staticmethod
    async def get_config_value(db: AsyncSession, config_key: str, default: Any = None) -> Any:
        """获取配置值"""
        config = await SysConfigCRUD.get_by_key(db, config_key)
        if config:
            return config.get_value()
        return default

    @staticmethod
    async def get_all_configs(
        db: AsyncSession,
        is_public: Optional[bool] = None
    ) -> List[dict]:
        """获取所有配置"""
        configs = await SysConfigCRUD.get_all(db, is_public)
        return [c.to_dict() for c in configs]

    @staticmethod
    async def get_configs_as_dict(
        db: AsyncSession,
        is_public: Optional[bool] = None
    ) -> Dict[str, Any]:
        """获取配置为字典格式"""
        configs = await SysConfigCRUD.get_all(db, is_public)
        return {c.config_key: c.get_value() for c in configs}

    @staticmethod
    async def update_config(
        db: AsyncSession,
        config_key: str,
        data: ConfigUpdate
    ) -> Optional[dict]:
        """更新配置"""
        config = await SysConfigCRUD.update(
            db=db,
            config_key=config_key,
            config_value=data.config_value,
            description=data.description,
            is_public=data.is_public
        )
        return config.to_dict() if config else None

    @staticmethod
    async def batch_update_configs(
        db: AsyncSession,
        configs: Dict[str, Any]
    ) -> int:
        """批量更新配置"""
        return await SysConfigCRUD.batch_update(db, configs)

    @staticmethod
    async def delete_config(db: AsyncSession, config_key: str) -> bool:
        """删除配置"""
        return await SysConfigCRUD.delete(db, config_key)


class AlertRulesService:
    """告警规则服务"""

    # 告警规则配置键映射
    RULE_KEYS = {
        "warning_threshold": "alert_warning_threshold",
        "critical_threshold": "alert_critical_threshold",
        "stop_threshold": "alert_stop_threshold",
        "expired_days": "alert_expired_days",
        "auto_suspend": "alert_auto_suspend",
        "auto_notify": "alert_auto_notify",
    }

    @staticmethod
    async def get_rules(db: AsyncSession) -> Dict[str, Any]:
        """获取告警规则"""
        rules = {}
        for rule_key, config_key in AlertRulesService.RULE_KEYS.items():
            value = await SystemConfigService.get_config_value(db, config_key)
            if value is not None:
                rules[rule_key] = value
            else:
                # 默认值
                defaults = {
                    "warning_threshold": 80,
                    "critical_threshold": 90,
                    "stop_threshold": 100,
                    "expired_days": 7,
                    "auto_suspend": True,
                    "auto_notify": True,
                }
                rules[rule_key] = defaults.get(rule_key)
        return rules

    @staticmethod
    async def update_rules(db: AsyncSession, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新告警规则"""
        configs_to_update = {}
        for rule_key, config_key in AlertRulesService.RULE_KEYS.items():
            if rule_key in data and data[rule_key] is not None:
                value = data[rule_key]
                # 转换布尔值为字符串
                if isinstance(value, bool):
                    value = "true" if value else "false"
                configs_to_update[config_key] = str(value)
        
        if configs_to_update:
            await SysConfigCRUD.batch_update(db, configs_to_update)
        
        return await AlertRulesService.get_rules(db)


class NotifyTemplateService:
    """通知模板服务"""

    @staticmethod
    async def create_template(
        db: AsyncSession,
        data: NotifyTemplateCreate,
        created_by: Optional[int] = None
    ) -> SysNotifyTemplateModel:
        """创建通知模板"""
        return await SysNotifyTemplateCRUD.create(
            db=db,
            code=data.code,
            name=data.name,
            type=data.type.value,
            title=data.title,
            content=data.content,
            variables=data.variables,
            is_enabled=data.is_enabled,
            remark=data.remark,
            created_by=created_by
        )

    @staticmethod
    async def get_template(db: AsyncSession, template_id: int) -> Optional[dict]:
        """获取单个模板"""
        template = await SysNotifyTemplateCRUD.get_by_id(db, template_id)
        return template.to_dict() if template else None

    @staticmethod
    async def get_template_by_code(db: AsyncSession, code: str) -> Optional[dict]:
        """根据编码获取模板"""
        template = await SysNotifyTemplateCRUD.get_by_code(db, code)
        return template.to_dict() if template else None

    @staticmethod
    async def get_templates(
        db: AsyncSession,
        type: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取模板列表"""
        templates, total = await SysNotifyTemplateCRUD.get_list(
            db=db,
            type=type,
            is_enabled=is_enabled,
            keyword=keyword,
            page=page,
            page_size=page_size
        )
        return [t.to_dict() for t in templates], total

    @staticmethod
    async def update_template(
        db: AsyncSession,
        template_id: int,
        data: NotifyTemplateUpdate
    ) -> Optional[dict]:
        """更新模板"""
        template = await SysNotifyTemplateCRUD.update(
            db=db,
            template_id=template_id,
            name=data.name,
            title=data.title,
            content=data.content,
            variables=data.variables,
            is_enabled=data.is_enabled,
            remark=data.remark
        )
        return template.to_dict() if template else None

    @staticmethod
    async def delete_template(db: AsyncSession, template_id: int) -> bool:
        """删除模板"""
        return await SysNotifyTemplateCRUD.delete(db, template_id)

    @staticmethod
    async def render_template(
        db: AsyncSession,
        code: str,
        variables: Dict[str, Any]
    ) -> Optional[Dict[str, str]]:
        """渲染模板内容"""
        template = await SysNotifyTemplateCRUD.get_by_code(db, code)
        if not template:
            return None
        
        title = template.title or ""
        content = template.content or ""
        
        # 替换变量
        for key, value in variables.items():
            title = title.replace(f"{{{key}}}", str(value))
            content = content.replace(f"{{{key}}}", str(value))
        
        return {
            "type": template.type.value,
            "title": title,
            "content": content
        }


class LoginLogService:
    """登录日志服务"""

    @staticmethod
    async def get_logs(
        db: AsyncSession,
        user_id: Optional[int] = None,
        account: Optional[str] = None,
        is_success: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """获取登录日志列表"""
        logs, total = await SysLoginLogCRUD.get_list(
            db=db,
            user_id=user_id,
            account=account,
            is_success=is_success,
            start_time=start_time,
            end_time=end_time,
            page=page,
            page_size=page_size
        )
        return [log.to_dict() for log in logs], total


class OperationLogService:
    """操作日志服务"""

    @staticmethod
    async def log_operation(
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
    ):
        """记录操作日志"""
        await SysOperationLogCRUD.create(
            db=db,
            module=module,
            action=action,
            user_id=user_id,
            user_name=user_name,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            detail=detail,
            ip=ip,
            is_success=is_success,
            error_msg=error_msg
        )

    @staticmethod
    async def get_logs(
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
    ) -> Tuple[List[dict], int]:
        """获取操作日志列表"""
        logs, total = await SysOperationLogCRUD.get_list(
            db=db,
            user_id=user_id,
            module=module,
            action=action,
            target_type=target_type,
            is_success=is_success,
            start_time=start_time,
            end_time=end_time,
            page=page,
            page_size=page_size
        )
        return [log.to_dict() for log in logs], total
