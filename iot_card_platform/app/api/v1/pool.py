"""
流量池管理 API
功能: 创建流量池、添加/移除卡片、用量统计、阈值设置
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.pool_service import pool_service
from app.utils.auth import get_current_user, require_super_admin, require_any_level
from app.utils.exceptions import BusinessException
from app.schemas.common import ResponseModel
from app.schemas.auth import CurrentUser
from app.schemas.pool import PoolCreate, PoolUpdate, PoolAddCards, PoolRemoveCards, PoolRechargeRequest, PoolTopupPurchaseRequest
from app.flow_packages import FLOW_PACKAGE_LABELS, FLOW_PACKAGE_SIZES_MB

router = APIRouter(tags=["流量池管理"])


# ============ 流量池基础操作 ============

@router.get("", summary="获取流量池列表", response_model=ResponseModel)
async def get_pools(
    name: Optional[str] = Query(None, description="流量池名称(模糊搜索)"),
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


@router.get("/stats", summary="获取流量池总体统计", response_model=ResponseModel)
async def get_pool_stats(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    获取流量池总体统计
    - 总流量池数、总卡片数
    - 总流量、已用流量
    - 告警流量池数、按运营商分类
    """
    stats = await pool_service.get_pool_stats(
        db,
        current_user_id=current_user.id,
        user_level=current_user.user_level
    )
    return ResponseModel(data=stats)


@router.get("/packages", summary="获取加油包列表", response_model=ResponseModel)
async def get_pool_packages(
    carrier: Optional[str] = Query(None, description="运营商"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取可用的固定规格加油包列表"""
    return ResponseModel(data=[
        {"label": FLOW_PACKAGE_LABELS[size], "flow_mb": size}
        for size in FLOW_PACKAGE_SIZES_MB
    ])


@router.post("/export", summary="导出流量池数据", response_model=ResponseModel)
async def export_pools(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """导出流量池数据（暂未实现）"""
    raise BusinessException(code=501, msg="导出功能暂未开放")


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
    user_id = None if current_user.user_level == 1 else current_user.id

    pool = await pool_service.create_pool(
        db=db,
        name=request.name,
        carrier=request.carrier,
        flow_size=request.flow_size,
        period_type=request.period_type,
        user_id=user_id,
        alert_threshold_1=request.alert_threshold_1,
        alert_threshold_2=request.alert_threshold_2,
        alert_threshold_3=request.alert_threshold_3,
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
    pool = await pool_service.get_pool(
        db,
        pool_id,
        current_user_id=current_user.id,
        user_level=current_user.user_level
    )
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
    pool = await pool_service.update_pool(
        db,
        pool_id,
        current_user_id=current_user.id,
        user_level=current_user.user_level,
        **update_data
    )
    return ResponseModel(data=pool, msg="更新成功")


@router.put("/{pool_id}/status", summary="切换流量池状态", response_model=ResponseModel)
async def toggle_pool_status(
    pool_id: int = Path(..., description="流量池ID"),
    status: str = Body(..., embed=True, description="状态: enable/disable"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """启用/禁用流量池"""
    if status not in ("enable", "disable"):
        raise BusinessException(code=400, msg="状态值无效，必须为 enable 或 disable")
    pool = await pool_service.update_pool(
        db,
        pool_id,
        current_user_id=current_user.id,
        user_level=current_user.user_level,
        status=status
    )
    return ResponseModel(data=pool, msg="状态更新成功")


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
    await pool_service.delete_pool(
        db,
        pool_id,
        current_user_id=current_user.id,
        user_level=current_user.user_level
    )
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
        db=db,
        pool_id=pool_id,
        current_user_id=current_user.id,
        user_level=current_user.user_level,
        page=page,
        page_size=page_size
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
        current_user_id=current_user.id,
        user_level=current_user.user_level,
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
        current_user_id=current_user.id,
        user_level=current_user.user_level,
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
    usage = await pool_service.get_pool_usage(
        db,
        pool_id,
        current_user_id=current_user.id,
        user_level=current_user.user_level
    )
    return ResponseModel(data=usage)


@router.get("/{pool_id}/usage/trend", summary="获取流量池用量趋势", response_model=ResponseModel)
async def get_pool_usage_trend(
    pool_id: int = Path(..., description="流量池ID"),
    days: int = Query(30, ge=1, le=90, description="天数"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取流量池最近N天的用量趋势数据（暂返回空数组）"""
    return ResponseModel(data=[])


@router.post("/{pool_id}/recharge", summary="充值加油包", response_model=ResponseModel)
async def recharge_pool(
    pool_id: int = Path(..., description="流量池ID"),
    request: PoolRechargeRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """后台给流量池增加流量，并自动重检池超限停卡"""
    result = await pool_service.recharge_pool(
        db=db,
        pool_id=pool_id,
        added_flow_mb=request.added_flow_mb,
        current_user_id=current_user.id,
        user_level=current_user.user_level,
        remark=request.remark
    )
    return ResponseModel(
        data=result,
        msg=f"补量成功，自动复机 {result['auto_resumed']} 张卡片"
    )


@router.post("/{pool_id}/topup/quote", summary="流量池加油包试算", response_model=ResponseModel)
async def quote_pool_topup(
    pool_id: int = Path(..., description="流量池ID"),
    request: PoolTopupPurchaseRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_any_level)
):
    quote = await pool_service.quote_pool_topup(
        db=db,
        pool_id=pool_id,
        current_user_id=current_user.id
    )
    return ResponseModel(data={
        **quote,
        "quantity": request.quantity,
        "added_flow_mb": quote["unit_flow_mb"] * request.quantity,
        "total_price": round(quote["unit_price"] * request.quantity, 2)
    })


@router.post("/{pool_id}/topup", summary="购买流量池加油包", response_model=ResponseModel)
async def purchase_pool_topup(
    pool_id: int = Path(..., description="流量池ID"),
    request: PoolTopupPurchaseRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_any_level)
):
    result = await pool_service.purchase_pool_topup(
        db=db,
        pool_id=pool_id,
        quantity=request.quantity,
        current_user_id=current_user.id,
        remark=request.remark
    )
    return ResponseModel(data=result, msg="流量池加油包购买成功")


@router.get("/{pool_id}/recharge-logs", summary="获取充值记录", response_model=ResponseModel)
async def get_recharge_logs(
    pool_id: int = Path(..., description="流量池ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取流量池充值记录（暂返回空列表）"""
    return ResponseModel(data={"total": 0, "page": page, "page_size": page_size, "items": []})


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
        db=db,
        pool_id=pool_id,
        current_user_id=current_user.id,
        user_level=current_user.user_level,
        action=action,
        page=page,
        page_size=page_size
    )
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})
