"""
开放 API 接口
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.auth import CurrentUser
from app.schemas.common import ResponseModel
from app.services.iot_card_service import iot_card_service
from app.services.pool_service import pool_service
from app.utils.open_api_auth import get_open_api_current_user

router = APIRouter(prefix="/open", tags=["开放API"])


@router.get("/cards", summary="开放API-获取卡片列表", response_model=ResponseModel)
async def open_get_cards(
    keyword: Optional[str] = Query(None, description="关键词(ICCID/MSISDN/后6位)"),
    status: Optional[str] = Query(None, description="卡片状态"),
    carrier: Optional[str] = Query(None, description="运营商"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_open_api_current_user)
):
    items, total = await iot_card_service.get_cards(
        db=db,
        current_user_id=current_user.id,
        user_level=current_user.user_level,
        keyword=keyword,
        status=status,
        carrier=carrier,
        page=page,
        page_size=page_size
    )
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})


@router.get("/cards/stats", summary="开放API-获取卡片统计", response_model=ResponseModel)
async def open_get_card_stats(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_open_api_current_user)
):
    stats = await iot_card_service.get_stats(
        db=db,
        current_user_id=current_user.id,
        user_level=current_user.user_level
    )
    return ResponseModel(data=stats)


@router.post("/cards/batch-query", summary="开放API-批量查询卡片", response_model=ResponseModel)
async def open_batch_query_cards(
    iccids: List[str] = Body(..., description="ICCID列表"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_open_api_current_user)
):
    if len(iccids) > 10000:
        return ResponseModel(code=400, msg="单次最多查询10000个ICCID")

    result = await iot_card_service.batch_query_cards(
        db=db,
        iccids=iccids,
        current_user_id=current_user.id,
        user_level=current_user.user_level
    )
    return ResponseModel(data=result, msg=f"查询完成：找到 {len(result['found'])} 张卡片")


@router.get("/cards/{card_id}", summary="开放API-获取卡片详情", response_model=ResponseModel)
async def open_get_card_detail(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_open_api_current_user)
):
    card = await iot_card_service.get_card_detail(
        db=db,
        card_id=card_id,
        current_user_id=current_user.id,
        user_level=current_user.user_level
    )
    return ResponseModel(data=card)


@router.get("/cards/{card_id}/usage-summary", summary="开放API-获取卡片用量摘要", response_model=ResponseModel)
async def open_get_card_usage_summary(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_open_api_current_user)
):
    card = await iot_card_service.get_card_detail(
        db=db,
        card_id=card_id,
        current_user_id=current_user.id,
        user_level=current_user.user_level
    )
    history = await iot_card_service.get_card_usage_history(
        db=db,
        card_id=card_id,
        current_user_id=current_user.id,
        user_level=current_user.user_level
    )

    latest_daily = history[-1] if history else None
    return ResponseModel(data={
        "card_id": card.get("id"),
        "iccid": card.get("iccid"),
        "status": card.get("status"),
        "status_name": card.get("status_name"),
        "daily_usage": {
            "snapshot_date": latest_daily.get("snapshot_date") if latest_daily else date.today().isoformat(),
            "used_mb": latest_daily.get("daily_used", 0) if latest_daily else 0,
            "total_used_mb": latest_daily.get("data_used", card.get("data_used", 0)) if latest_daily else card.get("data_used", 0)
        },
        "monthly_usage": {
            "snapshot_month": date.today().strftime("%Y-%m"),
            "used_mb": card.get("data_used_month", 0),
            "total_mb": card.get("data_total", 0),
            "remaining_mb": card.get("data_remain", 0),
            "usage_percent": card.get("data_usage_percent", 0)
        },
        "pool_info": {
            "pool_id": card.get("pool_id"),
            "is_pool_member": card.get("is_pool_member", False)
        },
        "data_sync_at": card.get("data_sync_at")
    })


@router.get("/cards/{card_id}/usage-history", summary="开放API-获取卡片用量历史", response_model=ResponseModel)
async def open_get_card_usage_history(
    card_id: int,
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_open_api_current_user)
):
    history = await iot_card_service.get_card_usage_history(
        db=db,
        card_id=card_id,
        current_user_id=current_user.id,
        user_level=current_user.user_level,
        start_date=start_date,
        end_date=end_date
    )
    return ResponseModel(data={
        "card_id": card_id,
        "start_date": start_date,
        "end_date": end_date,
        "items": history
    })


@router.get("/pools", summary="开放API-获取流量池列表", response_model=ResponseModel)
async def open_get_pools(
    name: Optional[str] = Query(None, description="流量池名称"),
    carrier: Optional[str] = Query(None, description="运营商"),
    status: Optional[str] = Query(None, description="状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_open_api_current_user)
):
    items, total = await pool_service.get_pools(
        db=db,
        current_user_id=current_user.id,
        user_level=current_user.user_level,
        name=name,
        carrier=carrier,
        status=status,
        page=page,
        page_size=page_size
    )
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})


@router.get("/pools/{pool_id}", summary="开放API-获取流量池详情", response_model=ResponseModel)
async def open_get_pool_detail(
    pool_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_open_api_current_user)
):
    pool = await pool_service.get_pool(
        db=db,
        pool_id=pool_id,
        current_user_id=current_user.id,
        user_level=current_user.user_level
    )
    return ResponseModel(data=pool)


@router.get("/pools/{pool_id}/usage", summary="开放API-获取流量池用量详情", response_model=ResponseModel)
async def open_get_pool_usage(
    pool_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_open_api_current_user)
):
    usage = await pool_service.get_pool_usage(
        db=db,
        pool_id=pool_id,
        current_user_id=current_user.id,
        user_level=current_user.user_level
    )
    return ResponseModel(data=usage)
