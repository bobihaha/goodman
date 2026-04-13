"""
系统设置 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.utils.auth import get_current_user, require_super_admin, require_user_level
from app.schemas.common import ResponseModel, PageResponseModel
from app.schemas.system import (
    ConfigCreate, ConfigUpdate, ConfigBatchUpdate,
    AlertRulesUpdate, NotifyTemplateCreate, NotifyTemplateUpdate
)
from app.services.system_service import (
    SystemConfigService, LoginLogService, OperationLogService,
    AlertRulesService, NotifyTemplateService
)

router = APIRouter()


# ============ 系统配置 ============

@router.get("/configs", summary="获取系统配置列表")
async def get_configs(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取所有系统配置"""
    configs = await SystemConfigService.get_all_configs(db)
    return ResponseModel(data=configs)


@router.get("/configs/public", summary="获取公开配置")
async def get_public_configs(
    db: AsyncSession = Depends(get_db)
):
    """获取公开的系统配置 (无需登录)"""
    configs = await SystemConfigService.get_configs_as_dict(db, is_public=True)
    return ResponseModel(data=configs)


@router.get("/configs/{config_key}", summary="获取单个配置")
async def get_config(
    config_key: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取单个配置"""
    config = await SystemConfigService.get_config(db, config_key)
    if not config:
        return ResponseModel(code=404, msg="配置不存在")
    return ResponseModel(data=config)


@router.post("/configs", summary="创建配置")
async def create_config(
    data: ConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_user_level)
):
    """创建系统配置"""
    # 检查是否已存在
    existing = await SystemConfigService.get_config(db, data.config_key)
    if existing:
        return ResponseModel(code=400, msg="配置键已存在")
    
    config = await SystemConfigService.create_config(db, data)
    return ResponseModel(data=config.to_dict(), msg="创建成功")


@router.put("/configs/{config_key}", summary="更新配置")
async def update_config(
    config_key: str,
    data: ConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_user_level)
):
    """更新系统配置"""
    config = await SystemConfigService.update_config(db, config_key, data)
    if not config:
        return ResponseModel(code=404, msg="配置不存在")
    return ResponseModel(data=config, msg="更新成功")


@router.put("/configs", summary="批量更新配置")
async def batch_update_configs(
    data: ConfigBatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_user_level)
):
    """批量更新系统配置"""
    # 将列表转为字典
    configs_dict = {}
    for item in data.configs:
        for key, value in item.items():
            configs_dict[key] = value
    
    updated = await SystemConfigService.batch_update_configs(db, configs_dict)
    return ResponseModel(data={"updated": updated}, msg=f"更新成功，共{updated}条")


@router.delete("/configs/{config_key}", summary="删除配置")
async def delete_config(
    config_key: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_user_level)
):
    """删除系统配置"""
    success = await SystemConfigService.delete_config(db, config_key)
    if not success:
        return ResponseModel(code=404, msg="配置不存在")
    return ResponseModel(msg="删除成功")


# ============ 登录日志 ============

@router.get("/logs/login", summary="获取登录日志")
async def get_login_logs(
    user_id: Optional[int] = Query(None, description="用户ID"),
    account: Optional[str] = Query(None, description="账户"),
    is_success: Optional[bool] = Query(None, description="是否成功"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取登录日志"""
    logs, total = await LoginLogService.get_logs(
        db=db,
        current_user_id=current_user.id,
        current_user_level=current_user.user_level,
        user_id=user_id,
        account=account,
        is_success=is_success,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size
    )
    
    return PageResponseModel(
        data=logs,
        total=total,
        page=page,
        page_size=page_size
    )


# ============ 操作日志 ============

@router.get("/logs/operation", summary="获取操作日志")
async def get_operation_logs(
    user_id: Optional[int] = Query(None, description="用户ID"),
    module: Optional[str] = Query(None, description="模块"),
    action: Optional[str] = Query(None, description="动作"),
    target_type: Optional[str] = Query(None, description="目标类型"),
    target_id: Optional[int] = Query(None, description="目标ID"),
    is_success: Optional[bool] = Query(None, description="是否成功"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取操作日志"""
    logs, total = await OperationLogService.get_logs(
        db=db,
        current_user_id=current_user.id,
        current_user_level=current_user.user_level,
        user_id=user_id,
        module=module,
        action=action,
        target_type=target_type,
        target_id=target_id,
        is_success=is_success,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size
    )
    
    return PageResponseModel(
        data=logs,
        total=total,
        page=page,
        page_size=page_size
    )


# ============ 告警规则 ============

@router.get("/alerts/rules", summary="获取告警规则")
async def get_alert_rules(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取告警规则配置"""
    rules = await AlertRulesService.get_rules(db)
    return ResponseModel(data=rules)


@router.put("/alerts/rules", summary="更新告警规则")
async def update_alert_rules(
    data: AlertRulesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """更新告警规则配置 (仅管理员)"""
    rules = await AlertRulesService.update_rules(db, data.model_dump(exclude_none=True))
    return ResponseModel(data=rules, msg="更新成功")


# ============ 通知模板 ============

@router.get("/notify/templates", summary="获取通知模板列表")
async def get_notify_templates(
    type: Optional[str] = Query(None, description="通知类型: sms/email/wechat/webhook"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取通知模板列表"""
    templates, total = await NotifyTemplateService.get_templates(
        db=db,
        type=type,
        is_enabled=is_enabled,
        keyword=keyword,
        page=page,
        page_size=page_size
    )
    return PageResponseModel(
        data=templates,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/notify/templates/{template_id}", summary="获取通知模板详情")
async def get_notify_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取单个通知模板"""
    template = await NotifyTemplateService.get_template(db, template_id)
    if not template:
        return ResponseModel(code=404, msg="模板不存在")
    return ResponseModel(data=template)


@router.post("/notify/templates", summary="创建通知模板")
async def create_notify_template(
    data: NotifyTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """创建通知模板 (仅管理员)"""
    # 检查编码是否已存在
    existing = await NotifyTemplateService.get_template_by_code(db, data.code)
    if existing:
        return ResponseModel(code=400, msg="模板编码已存在")
    
    template = await NotifyTemplateService.create_template(db, data, created_by=current_user.id)
    return ResponseModel(data=template.to_dict(), msg="创建成功")


@router.put("/notify/templates/{template_id}", summary="更新通知模板")
async def update_notify_template(
    template_id: int,
    data: NotifyTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """更新通知模板 (仅管理员)"""
    template = await NotifyTemplateService.update_template(db, template_id, data)
    if not template:
        return ResponseModel(code=404, msg="模板不存在")
    return ResponseModel(data=template, msg="更新成功")


@router.delete("/notify/templates/{template_id}", summary="删除通知模板")
async def delete_notify_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """删除通知模板 (仅管理员)"""
    success = await NotifyTemplateService.delete_template(db, template_id)
    if not success:
        return ResponseModel(code=404, msg="模板不存在")
    return ResponseModel(msg="删除成功")
