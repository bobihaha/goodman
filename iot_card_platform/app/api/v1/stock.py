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
    BatchCreate, StockInCreate, StockOutCreate,
    StockRecycleCreate, StockRecycleByIccidsCreate, BatchQueryRequest,
    ExcelStockOutCreate
)

router = APIRouter(tags=["出入库管理"])


# ============ 采购批次 ============

@router.post("/batches", summary="创建采购批次", response_model=ResponseModel)
async def create_batch(
    request: BatchCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """创建采购批次 (仅超级管理员)"""
    batch = await stock_service.create_batch(
        db=db,
        supplier_id=request.supplier_id,
        package_id=request.package_id,
        package_period_count=request.package_period_count,
        material=request.material,
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
    """批量入库卡片 (仅超级管理员)"""
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
    """批量出库卡片 (仅超级管理员)"""
    result = await stock_service.stock_out(
        db=db,
        card_ids=request.card_ids,
        to_user_id=request.to_user_id,
        sale_package_id=request.sale_package_id,
        period_count=request.period_count,
        card_type=request.card_type,
        stock_out_date=request.stock_out_date,
        test_expire_date=request.test_expire_date,
        silent_expire_date=request.silent_expire_date,
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
    package_id: Optional[int] = Query(None, description="套餐ID"),
    sort_by: Optional[str] = Query("stock_in_at", description="排序字段"),
    sort_order: Optional[str] = Query("desc", description="排序方式: asc/desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取库存卡片列表 (未出库的卡)"""
    items, total = await stock_service.get_inventory(
        db=db,
        supplier_id=supplier_id,
        carrier=carrier,
        package_id=package_id,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})


# ============ 入库记录 ============

@router.get("/in/records", summary="获取入库记录列表", response_model=ResponseModel)
async def get_stock_in_records_list(
    supplier_id: Optional[int] = Query(None, description="供应商ID"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取入库记录列表"""
    items, total = await stock_service.get_in_records_list(
        db=db,
        supplier_id=supplier_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size
    )
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})


@router.get("/in/records/{record_id}", summary="获取入库记录详情", response_model=ResponseModel)
async def get_stock_in_record_detail(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取入库记录详情（含卡片列表）"""
    detail = await stock_service.get_in_record_detail(db, record_id)
    return ResponseModel(data=detail)


@router.post("/in/records/export", summary="导出入库记录", response_model=ResponseModel)
async def export_stock_in_records(
    supplier_id: Optional[int] = Body(None, description="供应商ID"),
    start_date: Optional[str] = Body(None, description="开始日期"),
    end_date: Optional[str] = Body(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """导出入库记录（返回JSON数据，前端用xlsx生成Excel）"""
    data = await stock_service.export_in_records(
        db=db,
        supplier_id=supplier_id,
        start_date=start_date,
        end_date=end_date
    )
    return ResponseModel(data=data, msg="导出成功")


# ============ 出库记录 ============

@router.get("/out/records", summary="获取出库记录列表", response_model=ResponseModel)
async def get_stock_out_records_list(
    user_id: Optional[int] = Query(None, description="目标用户ID"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取出库记录列表"""
    items, total = await stock_service.get_out_records_list(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size
    )
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})


@router.get("/out/records/{record_id}", summary="获取出库记录详情", response_model=ResponseModel)
async def get_stock_out_record_detail(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取出库记录详情（含卡片列表）"""
    detail = await stock_service.get_out_record_detail(db, record_id)
    return ResponseModel(data=detail)


@router.post("/out/records/export", summary="导出出库记录", response_model=ResponseModel)
async def export_stock_out_records(
    user_id: Optional[int] = Body(None, description="目标用户ID"),
    start_date: Optional[str] = Body(None, description="开始日期"),
    end_date: Optional[str] = Body(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """导出出库记录（返回JSON数据，前端用xlsx生成Excel）"""
    data = await stock_service.export_out_records(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    return ResponseModel(data=data, msg="导出成功")


# ============ 卡片回收 ============

@router.post("/recycle", summary="卡片回收", response_model=ResponseModel)
async def recycle_cards(
    request: StockRecycleCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """卡片回收 (仅超级管理员)"""
    result = await stock_service.recycle_cards(
        db=db,
        card_ids=request.card_ids,
        recycle_reason=request.recycle_reason,
        operator_id=current_user.id,
        remark=request.remark
    )
    return ResponseModel(data=result, msg=f"成功回收 {result['success']} 张卡片")


@router.post("/recycle/by-iccids", summary="通过ICCID批量回收", response_model=ResponseModel)
async def recycle_cards_by_iccids(
    request: StockRecycleByIccidsCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """通过ICCID批量回收卡片 (仅超级管理员)"""
    result = await stock_service.recycle_by_iccids(
        db=db,
        iccids=request.iccids,
        recycle_reason=request.recycle_reason,
        operator_id=current_user.id,
        remark=request.remark
    )
    return ResponseModel(data=result, msg=f"成功回收 {result['success']} 张卡片")


@router.get("/recycle/records", summary="获取回收记录列表", response_model=ResponseModel)
async def get_recycle_records(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取回收记录列表"""
    items, total = await stock_service.get_recycle_records(
        db=db,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size
    )
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})


# ============ 批量查询 ============

@router.post("/inventory/batch-query", summary="批量查询卡片", response_model=ResponseModel)
async def batch_query_cards(
    request: BatchQueryRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """批量查询卡片（最多10000个ICCID）"""
    result = await stock_service.batch_query_cards(db, request.iccids)
    return ResponseModel(data=result, msg=f"查询完成：找到 {len(result['found'])} 张卡片")


@router.post("/inventory/export", summary="导出库存数据", response_model=ResponseModel)
async def export_inventory(
    supplier_id: Optional[int] = Body(None, description="供应商ID"),
    carrier: Optional[str] = Body(None, description="运营商"),
    package_id: Optional[int] = Body(None, description="套餐ID"),
    iccids: Optional[List[str]] = Body(None, description="指定导出的ICCID列表"),
    sort_by: Optional[str] = Body("stock_in_at", description="排序字段"),
    sort_order: Optional[str] = Body("desc", description="排序方式"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """导出库存数据（返回JSON数据，前端用xlsx生成Excel）"""
    data = await stock_service.export_inventory(
        db=db,
        supplier_id=supplier_id,
        carrier=carrier,
        package_id=package_id,
        iccids=iccids,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return ResponseModel(data=data, msg="导出成功")


# ============ 模板下载 ============

@router.get("/import-template", summary="下载Excel导入模板")
async def download_import_template():
    """下载Excel导入模板"""
    template_data = [
        ["ICCID", "IMSI", "电话号码"],
        ["89860123456789012345", "460012345678901", "13800138000"],
        ["89860123456789012346", "460012345678902", "13800138001"]
    ]
    return ResponseModel(data=template_data, msg="模板数据获取成功")


@router.get("/out/template", summary="下载Excel出库模板")
async def download_stock_out_template():
    """下载Excel出库模板"""
    template_data = [
        ["ICCID", "用户ID", "销售套餐ID", "套餐周期", "卡类型", "出库日期", "测试期截止日期", "沉默期截止日期", "备注"],
        ["89860123456789012345", "10", "5", "12", "single", "2026-02-11", "2026-03-11", "2026-04-11", "测试卡"],
        ["89860123456789012346", "10", "5", "12", "pool", "2026-02-11", "", "2026-04-11", "正式卡"]
    ]
    return ResponseModel(data=template_data, msg="出库模板数据获取成功")


@router.post("/out/batch-import", summary="Excel批量出库", response_model=ResponseModel)
async def batch_stock_out_import(
    request: ExcelStockOutCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """Excel批量出库 (仅超级管理员)"""
    result = await stock_service.batch_stock_out_import(
        db=db,
        items=request.items,
        created_by=current_user.id
    )
    return ResponseModel(data=result, msg="批量出库完成")


@router.get("/records/card", summary="按卡号查询出入库记录", response_model=ResponseModel)
async def get_card_stock_records(
    iccid: str = Query(..., description="卡号ICCID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """按卡号查询出入库记录"""
    from app.crud.stock_crud import card_stock_record_crud
    records = await card_stock_record_crud.get_card_records(db, iccid)
    return ResponseModel(data={"total": len(records), "records": records}, msg="查询成功")
