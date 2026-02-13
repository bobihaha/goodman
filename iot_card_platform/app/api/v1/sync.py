"""
数据同步管理 API
功能：流量用量同步、生命周期同步、单卡同步、同步日志、同步任务管理
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.sync_service import sync_service
from app.utils.auth import get_current_user, require_super_admin
from app.schemas.common import ResponseModel
from app.schemas.auth import CurrentUser
from app.schemas.sync import (
    UsageSyncRequest, LifecycleSyncRequest, SingleCardSyncRequest,
    SyncLogQuery, SyncTaskCreate, SyncTaskUpdate
)

router = APIRouter(tags=["数据同步"])


# ============ 同步操作 ============

@router.post("/usage", summary="同步流量用量", response_model=ResponseModel)
async def sync_usage(
    request: UsageSyncRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    同步流量用量 (仅超级管理员)
    
    - 可指定供应商ID (NULL=全部供应商)
    - 可指定ICCID列表 (NULL=全部已出库卡片)
    - 调用供应商API获取流量使用情况
    - 更新卡片的 data_used 和 data_sync_at
    """
    result = await sync_service.sync_usage(
        db=db,
        supplier_id=request.supplier_id,
        iccid_list=request.iccid_list,
        triggered_by=current_user.id
    )
    return ResponseModel(data=result, msg=f"同步完成: 成功 {result['success']} 张，失败 {result['failed']} 张")


@router.post("/lifecycle", summary="同步生命周期", response_model=ResponseModel)
async def sync_lifecycle(
    request: LifecycleSyncRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    同步生命周期数据 (仅超级管理员)
    
    - 同步测试期/沉默期/激活日/过期日
    - 同步卡片状态
    """
    result = await sync_service.sync_lifecycle(
        db=db,
        supplier_id=request.supplier_id,
        iccid_list=request.iccid_list,
        triggered_by=current_user.id
    )
    return ResponseModel(data=result, msg=f"同步完成: 成功 {result['success']} 张，失败 {result['failed']} 张")


@router.post("/cards/{iccid}", summary="同步单卡信息", response_model=ResponseModel)
async def sync_single_card(
    iccid: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    同步单卡信息 (流量+生命周期)
    
    - 超级管理员可同步所有卡片
    - 普通用户只能同步自己的卡片
    """
    result = await sync_service.sync_single_card(
        db=db,
        iccid=iccid,
        triggered_by=current_user.id
    )
    return ResponseModel(data=result, msg="同步成功")


# ============ 同步日志 ============

@router.get("/logs", summary="获取同步日志", response_model=ResponseModel)
async def get_sync_logs(
    sync_type: Optional[str] = Query(None, description="同步类型"),
    supplier_id: Optional[int] = Query(None, description="供应商ID"),
    status: Optional[str] = Query(None, description="状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取同步日志列表"""
    items, total = await sync_service.get_sync_logs(
        db=db,
        sync_type=sync_type,
        supplier_id=supplier_id,
        status=status,
        page=page,
        page_size=page_size
    )
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})


# ============ 同步任务管理 ============

@router.post("/tasks", summary="创建同步任务", response_model=ResponseModel)
async def create_sync_task(
    request: SyncTaskCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    创建同步任务 (仅超级管理员)
    
    - 配置定时同步任务
    - 支持Cron表达式
    """
    task = await sync_service.create_sync_task(
        db=db,
        task_name=request.task_name,
        sync_type=request.sync_type.value,
        supplier_id=request.supplier_id,
        cron_expression=request.cron_expression,
        is_enabled=request.is_enabled,
        created_by=current_user.id,
        remark=request.remark
    )
    return ResponseModel(data=task, msg="任务创建成功")


@router.get("/tasks", summary="获取同步任务列表", response_model=ResponseModel)
async def get_sync_tasks(
    sync_type: Optional[str] = Query(None, description="同步类型"),
    is_enabled: Optional[int] = Query(None, description="是否启用"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取同步任务列表"""
    items, total = await sync_service.get_sync_tasks(
        db=db,
        sync_type=sync_type,
        is_enabled=is_enabled,
        page=page,
        page_size=page_size
    )
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})


@router.put("/tasks/{task_id}", summary="更新同步任务", response_model=ResponseModel)
async def update_sync_task(
    task_id: int,
    request: SyncTaskUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """更新同步任务"""
    task = await sync_service.update_sync_task(
        db=db,
        task_id=task_id,
        task_name=request.task_name,
        cron_expression=request.cron_expression,
        is_enabled=request.is_enabled,
        remark=request.remark
    )
    return ResponseModel(data=task, msg="任务更新成功")


@router.delete("/tasks/{task_id}", summary="删除同步任务", response_model=ResponseModel)
async def delete_sync_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """删除同步任务"""
    await sync_service.delete_sync_task(db, task_id)
    return ResponseModel(msg="任务删除成功")







