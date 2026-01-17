"""
出入库管理 API
平台侧：采购批次管理、卡片入库、卡片出库、库存统计
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.stock_service import stock_service
from app.utils.auth import get_current_user, require_super_admin
from app.schemas.common import ResponseModel
from app.schemas.auth import CurrentUser
from app.schemas.stock import (
    BatchCreate, BatchInfo,
    StockInCreate, StockInInfo, StockInResult,
    StockOutCreate, StockOutInfo, StockOutResult,
    StockSummary
)

router = APIRouter(tags=["出入库管理"])


# ============ 采购批次 ============

@router.post("/batches", summary="创建采购批次", response_model=ResponseModel)
async def create_batch(
    request: BatchCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    创建采购批次 (仅超级管理员)

    - 关联供应商和底层套餐
    - 设置测试期和沉默期到期日
    """
    batch = await stock_service.create_batch(
        db=db,
        supplier_id=request.supplier_id,
        package_id=request.package_id,
        test_expire_date=request.test_expire_date,
        silent_expire_date=request.silent_expire_date,
        purchase_date=request.purchase_date,
        created_by=current_user.id,
        remark=request.remark
    )
    return ResponseModel(data=batch, msg="批次创建成功")


@router.get("/batches", summary="获取批次列表", response_model=ResponseModel)
async def get_batches(
    supplier_id: Optional[int] = Query(None, description="供应商ID"),
    status: Optional[str] = Query(None, description="状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取采购批次列表"""
    items, total = await stock_service.get_batches(
        db=db, supplier_id=supplier_id, status=status, page=page, page_size=page_size
    )
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})


@router.get("/batches/{batch_id}", summary="获取批次详情", response_model=ResponseModel)
async def get_batch_detail(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取批次详情"""
    batch = await stock_service.get_batch_detail(db, batch_id)
    return ResponseModel(data=batch)


# ============ 入库 ============

@router.post("/in", summary="批量入库", response_model=ResponseModel)
async def stock_in(
    request: StockInCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    批量入库卡片 (仅超级管理员)

    - 关联采购批次
    - 批量导入卡片 (ICCID, IMSI, MSISDN)
    - 自动继承批次的生命周期配置
    """
    cards = [{"iccid": c.iccid, "imsi": c.imsi, "msisdn": c.msisdn} for c in request.cards]
    result = await stock_service.stock_in(
        db=db,
        batch_id=request.batch_id,
        cards=cards,
        created_by=current_user.id,
        remark=request.remark
    )
    return ResponseModel(data=result, msg=f"成功入库 {result['success']} 张卡片")


@router.get("/in", summary="获取入库记录", response_model=ResponseModel)
async def get_stock_in_records(
    batch_id: Optional[int] = Query(None, description="批次ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取入库记录列表"""
    items, total = await stock_service.get_stock_in_records(
        db=db, batch_id=batch_id, page=page, page_size=page_size
    )
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})


# ============ 出库 ============

@router.post("/out", summary="批量出库", response_model=ResponseModel)
async def stock_out(
    request: StockOutCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    批量出库卡片 (仅超级管理员)

    - 选择库存卡片
    - 分配给目标用户
    - 关联销售套餐
    """
    result = await stock_service.stock_out(
        db=db,
        card_ids=request.card_ids,
        to_user_id=request.to_user_id,
        sale_package_id=request.sale_package_id,
        created_by=current_user.id,
        remark=request.remark
    )
    return ResponseModel(data=result, msg=f"成功出库 {result['success']} 张卡片")


@router.get("/out", summary="获取出库记录", response_model=ResponseModel)
async def get_stock_out_records(
    to_user_id: Optional[int] = Query(None, description="目标用户ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取出库记录列表"""
    items, total = await stock_service.get_stock_out_records(
        db=db, to_user_id=to_user_id, page=page, page_size=page_size
    )
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})


# ============ 库存统计 ============

@router.get("/summary", summary="库存统计", response_model=ResponseModel)
async def get_stock_summary(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取库存统计"""
    summary = await stock_service.get_summary(db)
    return ResponseModel(data=summary)


@router.get("/inventory", summary="库存卡片列表", response_model=ResponseModel)
async def get_inventory(
    supplier_id: Optional[int] = Query(None, description="供应商ID"),
    carrier: Optional[str] = Query(None, description="运营商"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取库存卡片列表 (未出库的卡)"""
    items, total = await stock_service.get_inventory(
        db=db, supplier_id=supplier_id, carrier=carrier, page=page, page_size=page_size
    )
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})
