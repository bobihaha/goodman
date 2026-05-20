"""
供应商侧流量池管理 API
"""
from typing import Optional

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.common import ResponseModel
from app.schemas.supplier_pool import SupplierTrafficPoolAlertUpdate, SupplierTrafficPoolSyncRequest
from app.services.supplier_pool_service import supplier_traffic_pool_service
from app.utils.auth import require_super_admin

router = APIRouter(tags=["供应商流量池管理"])


@router.get("", summary="获取供应商流量池列表", response_model=ResponseModel)
async def get_supplier_traffic_pools(
    supplier_name: Optional[str] = Query(None, description="供应商名称"),
    carrier: Optional[str] = Query(None, description="运营商"),
    pool_specification: Optional[int] = Query(None, description="流量池规格(MB)"),
    order_by: str = Query(
        "usage_percent",
        pattern=(
            "^(usage_percent|pool_specification|used_flow|total_flow|remaining_flow|"
            "estimated_monthly_used_flow|estimated_month_end_remaining_flow|updated_at|last_sync_at)$"
        ),
    ),
    order_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_super_admin),
):
    items, total = await supplier_traffic_pool_service.get_list(
        db=db,
        supplier_name=supplier_name,
        carrier=carrier,
        pool_specification=pool_specification,
        order_by=order_by,
        order_dir=order_dir,
        page=page,
        page_size=page_size,
    )
    return ResponseModel(data={"items": items, "total": total, "page": page, "page_size": page_size})


@router.post("/sync", summary="同步供应商流量池", response_model=ResponseModel)
async def sync_supplier_traffic_pools(
    request: SupplierTrafficPoolSyncRequest = Body(default_factory=SupplierTrafficPoolSyncRequest),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_super_admin),
):
    result = await supplier_traffic_pool_service.sync_supplier_pools(
        db=db,
        supplier_id=request.supplier_id,
    )
    return ResponseModel(
        data=result,
        msg=(
            f"同步完成：池成功 {result['success_pools']} 个，池失败 {result['failed_pools']} 个，"
            f"供应商失败 {result['failed_suppliers']} 个"
        ),
    )


@router.get("/{pool_id}", summary="获取供应商流量池详情", response_model=ResponseModel)
async def get_supplier_traffic_pool_detail(
    pool_id: int = Path(..., description="供应商流量池ID"),
    months: int = Query(12, ge=1, le=36, description="历史月份数量"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_super_admin),
):
    detail = await supplier_traffic_pool_service.get_detail(
        db=db,
        pool_id=pool_id,
        months=months,
    )
    return ResponseModel(data=detail)


@router.post("/{pool_id}/histories/export", summary="导出供应商流量池历史用量", response_model=ResponseModel)
async def export_supplier_traffic_pool_histories(
    pool_id: int = Path(..., description="供应商流量池ID"),
    months: int = Query(36, ge=1, le=36, description="历史月份数量"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_super_admin),
):
    rows = await supplier_traffic_pool_service.export_history(
        db=db,
        pool_id=pool_id,
        months=months,
    )
    return ResponseModel(data=rows)


@router.put("/{pool_id}/alert", summary="更新阈值邮件提醒", response_model=ResponseModel)
async def update_supplier_traffic_pool_alert(
    pool_id: int = Path(..., description="供应商流量池ID"),
    request: SupplierTrafficPoolAlertUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_super_admin),
):
    pool = await supplier_traffic_pool_service.update_alert(
        db=db,
        pool_id=pool_id,
        alert_threshold=request.alert_threshold,
        alert_thresholds=request.alert_thresholds,
        alert_emails=request.alert_emails,
    )
    return ResponseModel(data=pool, msg="提醒配置已更新")
