"""
仪表盘 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.database import get_db
from app.utils.auth import get_current_user
from app.schemas.common import ResponseModel
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/overview", summary="仪表盘总览")
async def get_overview(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取仪表盘总览数据
    - 管理员: 查看全部数据
    - 普通用户: 只看自己的数据
    """
    is_admin = current_user.user_level == 1
    user_id = current_user.id
    
    overview = await DashboardService.get_overview(
        db=db,
        user_id=user_id,
        is_admin=is_admin
    )
    
    return ResponseModel(data=overview.model_dump())


@router.get("/cards/stats", summary="卡片统计")
async def get_card_stats(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取卡片统计数据"""
    is_admin = current_user.user_level == 1
    user_id = None if is_admin else current_user.id
    
    stats = await DashboardService.get_card_stats(db, user_id)
    return ResponseModel(data=stats.model_dump())


@router.get("/usage/trend", summary="流量趋势")
async def get_usage_trend(
    period: str = Query("daily", description="周期: daily/weekly/monthly"),
    days: int = Query(7, ge=1, le=30, description="天数"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取流量使用趋势"""
    is_admin = current_user.user_level == 1
    user_id = None if is_admin else current_user.id
    
    trend = await DashboardService.get_usage_trend(
        db=db,
        period=period,
        days=days,
        user_id=user_id
    )
    return ResponseModel(data=trend.model_dump())


@router.get("/alerts", summary="最近告警")
async def get_recent_alerts(
    limit: int = Query(10, ge=1, le=50, description="数量"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取最近告警消息"""
    is_admin = current_user.user_level == 1
    user_id = None if is_admin else current_user.id
    
    alerts = await DashboardService.get_recent_alerts(
        db=db,
        limit=limit,
        user_id=user_id
    )
    return ResponseModel(data=alerts)


@router.get("/activities", summary="最近活动")
async def get_recent_activities(
    limit: int = Query(10, ge=1, le=50, description="数量"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取最近活动记录"""
    activities = await DashboardService.get_recent_activities(
        db=db,
        limit=limit
    )
    return ResponseModel(data=activities)


@router.get("/pools/stats", summary="流量池统计")
async def get_pool_stats(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取流量池统计数据"""
    is_admin = current_user.user_level == 1
    user_id = None if is_admin else current_user.id
    
    stats = await DashboardService.get_pool_stats(db, user_id)
    return ResponseModel(data=stats.model_dump())


@router.get("/users/stats", summary="用户统计")
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取用户统计数据 (仅管理员)"""
    if current_user.user_level != 1:
        return ResponseModel(code=403, msg="无权限查看")
    
    stats = await DashboardService.get_user_stats(db)
    return ResponseModel(data=stats.model_dump())


@router.get("/account/balance", summary="账户余额")
async def get_account_balance(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取账户余额信息"""
    balance = await DashboardService.get_account_balance(db, current_user.id)
    return ResponseModel(data=balance)


@router.get("/pools/usage-percent", summary="流量池用量百分比")
async def get_pools_usage_percent(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取流量池用量百分比"""
    is_admin = current_user.user_level == 1
    user_id = None if is_admin else current_user.id
    
    pools = await DashboardService.get_pools_usage_percent(db, user_id)
    return ResponseModel(data=pools)


@router.get("/cards/expiring", summary="本月到期卡")
async def get_expiring_cards(
    carrier: Optional[str] = Query(None, description="运营商筛选"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取本月到期卡明细"""
    if carrier and carrier not in ['cmcc', 'cucc', 'ctcc']:
        raise HTTPException(status_code=400, detail="无效的运营商参数")

    is_admin = current_user.user_level == 1
    user_id = None if is_admin else current_user.id

    cards = await DashboardService.get_expiring_cards(db, user_id, carrier)
    return ResponseModel(data=cards)


@router.get("/cards/over-usage", summary="超量卡")
async def get_over_usage_cards(
    carrier: Optional[str] = Query(None, description="运营商筛选"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取超量卡明细"""
    if carrier and carrier not in ['cmcc', 'cucc', 'ctcc']:
        raise HTTPException(status_code=400, detail="无效的运营商参数")

    is_admin = current_user.user_level == 1
    user_id = None if is_admin else current_user.id

    cards = await DashboardService.get_over_usage_cards(db, user_id, carrier)
    return ResponseModel(data=cards)
