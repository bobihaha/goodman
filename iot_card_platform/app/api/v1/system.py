"""
系统设置 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.utils.auth import get_current_user, require_super_admin
from app.schemas.common import ResponseModel, PageResponseModel
from app.schemas.system import ConfigCreate, ConfigUpdate, ConfigBatchUpdate
from app.services.system_service import (
    SystemConfigService, LoginLogService, OperationLogService
)

router = APIRouter()


# ============ 系统配置 ============

@router.get("/configs", summary="获取系统配置列表")
async def get_configs(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """获取所有系统配置 (仅管理员)"""
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
    current_user = Depends(require_super_admin)
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
    current_user = Depends(require_super_admin)
):
    """创建系统配置 (仅管理员)"""
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
    current_user = Depends(require_super_admin)
):
    """更新系统配置 (仅管理员)"""
    config = await SystemConfigService.update_config(db, config_key, data)
    if not config:
        return ResponseModel(code=404, msg="配置不存在")
    return ResponseModel(data=config, msg="更新成功")


@router.put("/configs", summary="批量更新配置")
async def batch_update_configs(
    data: ConfigBatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """批量更新系统配置 (仅管理员)"""
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
    current_user = Depends(require_super_admin)
):
    """删除系统配置 (仅管理员)"""
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
    current_user = Depends(require_super_admin)
):
    """获取登录日志 (仅管理员)"""
    logs, total = await LoginLogService.get_logs(
        db=db,
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
    is_success: Optional[bool] = Query(None, description="是否成功"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """获取操作日志 (仅管理员)"""
    logs, total = await OperationLogService.get_logs(
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
    
    return PageResponseModel(
        data=logs,
        total=total,
        page=page,
        page_size=page_size
    )
