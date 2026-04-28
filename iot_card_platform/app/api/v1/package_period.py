"""
套餐周期管理 API
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.common import ResponseModel
from app.schemas.auth import CurrentUser
from app.schemas.package_period import (
    BatchCancelPackagePeriodRequest,
    BatchForceActivateRequest,
)
from app.services.package_period_service import package_period_service
from app.utils.auth import require_super_admin

router = APIRouter(prefix="/package-period", tags=["套餐周期管理"])


@router.post("/force-activate", summary="批量强制激活")
async def batch_force_activate(
    data: BatchForceActivateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    result = await package_period_service.batch_force_activate(
        db=db,
        data=data,
        operator_id=current_user.id,
        operator_name=current_user.name
    )
    return ResponseModel(
        data=result,
        msg=f"强制激活完成，成功{result['success']}张，失败{result['failed']}张"
    )


@router.post("/cancel-period", summary="批量取消计划套餐")
async def batch_cancel_period(
    data: BatchCancelPackagePeriodRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    result = await package_period_service.batch_cancel_package_period(
        db=db,
        data=data,
        operator_id=current_user.id,
        operator_name=current_user.name
    )
    return ResponseModel(
        data=result,
        msg=f"取消计划套餐完成，成功{result['success']}张，失败{result['failed']}张"
    )


@router.get("/logs", summary="套餐周期操作记录")
async def get_operation_logs(
    action: str = Query(..., description="操作类型: force_activate/cancel_period"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    result = await package_period_service.get_operation_logs(
        db=db,
        action=action,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size
    )
    return ResponseModel(data=result)
