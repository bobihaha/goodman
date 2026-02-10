"""
物联网卡管理 API
用户/代理商侧：查看、搜索、划拨、备注、导出
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.iot_card_service import iot_card_service
from app.utils.auth import get_current_user
from app.schemas.common import ResponseModel
from app.schemas.auth import CurrentUser
from app.schemas.iot_card import (
    CardQuery, CardSearchRequest, CardInfo, CardListResponse, CardStats,
    CardTransferRequest, BatchTransferRequest, TransferRecord,
    CardRemarkRequest, BatchRemarkRequest, CardExportRequest
)

router = APIRouter(prefix="/cards", tags=["卡片管理"])


@router.get("", summary="获取卡片列表", response_model=ResponseModel)
async def get_cards(
    keyword: Optional[str] = Query(None, description="关键词 (ICCID/MSISDN/后6位)"),
    status: Optional[str] = Query(None, description="卡片状态"),
    carrier: Optional[str] = Query(None, description="运营商"),
    period_type: Optional[str] = Query(None, description="周期类型"),
    pool_id: Optional[int] = Query(None, description="流量池ID"),
    is_pool_member: Optional[bool] = Query(None, description="是否加入流量池"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取卡片列表"""
    items, total = await iot_card_service.get_cards(
        db=db,
        current_user_id=current_user.id,
        user_level=current_user.user_level,
        keyword=keyword,
        status=status,
        carrier=carrier,
        period_type=period_type,
        pool_id=pool_id,
        is_pool_member=is_pool_member,
        page=page,
        page_size=page_size
    )
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})


@router.get("/stats", summary="获取卡片统计", response_model=ResponseModel)
async def get_card_stats(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取卡片统计信息"""
    stats = await iot_card_service.get_stats(
        db=db, current_user_id=current_user.id, user_level=current_user.user_level
    )
    return ResponseModel(data=stats)


@router.get("/search", summary="快速搜索卡片", response_model=ResponseModel)
async def search_cards(
    keyword: str = Query(..., min_length=1, max_length=30, description="ICCID/MSISDN/后6位"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """快速搜索卡片"""
    items = await iot_card_service.search_cards(
        db=db, keyword=keyword, current_user_id=current_user.id,
        user_level=current_user.user_level, limit=limit
    )
    return ResponseModel(data=items)


# === 批量操作放在单个操作之前 ===

@router.put("/batch/remark", summary="批量更新备注", response_model=ResponseModel)
async def batch_update_remark(
    request: BatchRemarkRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """批量更新卡片备注"""
    result = await iot_card_service.batch_update_remark(
        db=db, card_ids=request.card_ids, remark=request.remark,
        current_user_id=current_user.id, user_level=current_user.user_level
    )
    return ResponseModel(data=result, msg=f"成功更新 {result['success']} 张卡片备注")


@router.post("/batch/transfer", summary="批量划拨", response_model=ResponseModel)
async def batch_transfer_cards(
    request: BatchTransferRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """批量划拨卡片"""
    result = await iot_card_service.batch_transfer(
        db=db, card_ids=request.card_ids, to_user_id=request.to_user_id,
        current_user_id=current_user.id, user_level=current_user.user_level,
        remark=request.remark
    )
    return ResponseModel(data=result, msg=f"成功划拨 {result['success']} 张卡片")


@router.post("/batch-query", summary="批量查询卡片", response_model=ResponseModel)
async def batch_query_cards(
    iccids: List[str] = Body(..., description="ICCID列表"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    批量查询卡片
    
    - 根据多个ICCID查询卡片信息
    - 返回找到的卡片和未找到的ICCID列表
    - 最多支持10000个ICCID
    """
    if len(iccids) > 10000:
        return ResponseModel(code=400, msg="单次最多查询10000个ICCID")
    
    result = await iot_card_service.batch_query_cards(
        db=db, iccids=iccids,
        current_user_id=current_user.id, user_level=current_user.user_level
    )
    return ResponseModel(data=result, msg=f"查询完成：找到 {len(result['found'])} 张卡片")


@router.post("/export", summary="导出卡片数据", response_model=ResponseModel)
async def export_cards(
    request: CardExportRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """导出卡片数据"""
    data = await iot_card_service.export_cards(
        db=db, current_user_id=current_user.id, user_level=current_user.user_level,
        card_ids=request.card_ids,
        status=request.status.value if request.status else None,
        carrier=request.carrier.value if request.carrier else None
    )
    return ResponseModel(data={"count": len(data), "items": data})


# === 单个卡片操作 ===

@router.get("/{card_id}", summary="获取卡片详情", response_model=ResponseModel)
async def get_card_detail(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取卡片详情"""
    card = await iot_card_service.get_card_detail(
        db=db, card_id=card_id, current_user_id=current_user.id,
        user_level=current_user.user_level
    )
    return ResponseModel(data=card)


@router.put("/{card_id}/remark", summary="更新卡片备注", response_model=ResponseModel)
async def update_card_remark(
    card_id: int,
    request: CardRemarkRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """更新单卡备注"""
    card = await iot_card_service.update_remark(
        db=db, card_id=card_id, remark=request.remark,
        current_user_id=current_user.id, user_level=current_user.user_level
    )
    return ResponseModel(data=card, msg="备注更新成功")


@router.post("/{card_id}/transfer", summary="划拨卡片", response_model=ResponseModel)
async def transfer_card(
    card_id: int,
    request: CardTransferRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """划拨卡片给子用户"""
    card = await iot_card_service.transfer_card(
        db=db, card_id=card_id, to_user_id=request.to_user_id,
        current_user_id=current_user.id, user_level=current_user.user_level,
        remark=request.remark
    )
    return ResponseModel(data=card, msg="卡片划拨成功")


@router.get("/{card_id}/transfers", summary="获取卡片划拨记录", response_model=ResponseModel)
async def get_card_transfers(
    card_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取单张卡片的划拨记录"""
    items, total = await iot_card_service.get_card_transfers(
        db=db, card_id=card_id,
        current_user_id=current_user.id, user_level=current_user.user_level,
        page=page, page_size=page_size
    )
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})
