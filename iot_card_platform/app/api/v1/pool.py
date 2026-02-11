"""
流量池管理 API
功能: 创建流量池、添加/移除卡片、用量统计、阈值设置
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.pool_service import pool_service
from app.utils.auth import get_current_user, require_super_admin
from app.schemas.common import ResponseModel
from app.schemas.auth import CurrentUser
from app.schemas.pool import PoolCreate, PoolUpdate, PoolAddCards, PoolRemoveCards

router = APIRouter(tags=["流量池管理"])


# ============ 流量池基础操作 ============

@router.get("", summary="获取流量池列表", response_model=ResponseModel)
async def get_pools(
    carrier: Optional[str] = Query(None, description="运营商: cmcc/cucc/ctcc"),
    status: Optional[str] = Query(None, description="状态: enable/disable"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    获取流量池列表
    - 超级管理员: 可查看所有流量池
    - 普通用户: 只能查看自己的流量池
    """
    user_id = None if current_user.user_level == 1 else current_user.id

    items, total = await pool_service.get_pools(
        db=db,
        user_id=user_id,
        carrier=carrier,
        status=status,
        page=page,
        page_size=page_size
    )
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})


@router.get("/stats", summary="获取流量池总体统计", response_model=ResponseModel)
async def get_pool_stats(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    获取流量池总体统计
    - 总流量池数、总卡片数
    - 总流量、已用流量、剩余流量
    - 告警流量池数
    """
    user_id = None if current_user.user_level == 1 else current_user.id
    stats = await pool_service.get_pool_stats(db, user_id)
    return ResponseModel(data=stats)


@router.post("", summary="创建流量池", response_model=ResponseModel)
async def create_pool(
    request: PoolCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    创建流量池
    - 需要指定规格 (运营商+流量+周期)
    - 只有相同规格的已激活卡才能加入此池
    """
    # 普通用户创建的池归属于自己
    user_id = None if current_user.user_level == 1 else current_user.id

    pool = await pool_service.create_pool(
        db=db,
        name=request.name,
        carrier=request.carrier,
        flow_size=request.flow_size,
        period_type=request.period_type,
        user_id=user_id,
        alert_threshold=request.alert_threshold,
        stop_threshold=request.stop_threshold,
        created_by=current_user.id,
        remark=request.remark
    )
    return ResponseModel(data=pool, msg="流量池创建成功")


@router.get("/{pool_id}", summary="获取流量池详情", response_model=ResponseModel)
async def get_pool(
    pool_id: int = Path(..., description="流量池ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取流量池详情"""
    pool = await pool_service.get_pool(db, pool_id)
    return ResponseModel(data=pool)


@router.put("/{pool_id}", summary="更新流量池", response_model=ResponseModel)
async def update_pool(
    pool_id: int = Path(..., description="流量池ID"),
    request: PoolUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    更新流量池
    - 可修改名称、阈值、状态、备注
    - 规格信息创建后不可修改
    """
    update_data = request.model_dump(exclude_unset=True)
    pool = await pool_service.update_pool(db, pool_id, **update_data)
    return ResponseModel(data=pool, msg="更新成功")


@router.delete("/{pool_id}", summary="删除流量池", response_model=ResponseModel)
async def delete_pool(
    pool_id: int = Path(..., description="流量池ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    删除流量池
    - 池内有卡片时不允许删除
    """
    await pool_service.delete_pool(db, pool_id)
    return ResponseModel(msg="删除成功")


# ============ 流量池卡片操作 ============

@router.get("/{pool_id}/cards", summary="获取池内卡片列表", response_model=ResponseModel)
async def get_pool_cards(
    pool_id: int = Path(..., description="流量池ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取流量池内卡片列表"""
    items, total = await pool_service.get_pool_cards(
        db=db, pool_id=pool_id, page=page, page_size=page_size
    )
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})


@router.post("/{pool_id}/cards", summary="添加卡片到流量池", response_model=ResponseModel)
async def add_cards_to_pool(
    pool_id: int = Path(..., description="流量池ID"),
    request: PoolAddCards = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    添加卡片到流量池
    - 卡片必须是已激活状态
    - 卡片规格必须与流量池规格一致
    - 卡片不能已在其他流量池中
    """
    result = await pool_service.add_cards(
        db=db,
        pool_id=pool_id,
        card_ids=request.card_ids,
        operator_id=current_user.id,
        remark=request.remark
    )
    return ResponseModel(data=result, msg=f"成功添加 {result['success']} 张卡片")


@router.delete("/{pool_id}/cards", summary="从流量池移除卡片", response_model=ResponseModel)
async def remove_cards_from_pool(
    pool_id: int = Path(..., description="流量池ID"),
    request: PoolRemoveCards = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """从流量池移除卡片"""
    result = await pool_service.remove_cards(
        db=db,
        pool_id=pool_id,
        card_ids=request.card_ids,
        operator_id=current_user.id,
        remark=request.remark
    )
    return ResponseModel(data=result, msg=f"成功移除 {result['success']} 张卡片")


# ============ 流量池统计 ============

@router.get("/{pool_id}/usage", summary="获取流量池用量统计", response_model=ResponseModel)
async def get_pool_usage(
    pool_id: int = Path(..., description="流量池ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    获取流量池用量统计
    - 返回总用量、各卡片用量明细
    - 告警状态、是否超限
    """
    usage = await pool_service.get_pool_usage(db, pool_id)
    return ResponseModel(data=usage)


@router.get("/{pool_id}/logs", summary="获取流量池操作日志", response_model=ResponseModel)
async def get_pool_logs(
    pool_id: int = Path(..., description="流量池ID"),
    action: Optional[str] = Query(None, description="操作类型: add/remove"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取流量池卡片变动日志"""
    items, total = await pool_service.get_pool_logs(
        db=db, pool_id=pool_id, action=action, page=page, page_size=page_size
    )
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})
