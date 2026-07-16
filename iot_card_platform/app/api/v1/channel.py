"""渠道伙伴、客户报备和推广积分接口。"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Depends, Path, Query, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models.channel import ChannelPartnerModel
from app.schemas.auth import CurrentUser
from app.schemas.channel import (
    ChannelCustomerRegisterRequest,
    ChannelLoginRequest,
    ChannelPartnerCreate,
    ChannelPartnerUpdate,
    ChannelPasswordResetRequest,
    ChannelPointsSettleRequest,
    ChannelSettingsUpdate,
)
from app.schemas.common import ResponseModel
from app.services.channel_service import channel_service
from app.utils.auth import require_super_admin
from app.utils.channel_auth import get_current_channel
from app.utils.exceptions import BusinessException


router = APIRouter()


def _client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("X-Forwarded-For")
    return forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else None)


@router.get("/public/{slug}", summary="获取渠道报备页信息", response_model=ResponseModel)
async def get_public_channel(slug: str, db: AsyncSession = Depends(get_db)):
    return ResponseModel(data=await channel_service.public_config(db, slug))


@router.post("/public/{slug}/register", summary="渠道客户报备", response_model=ResponseModel)
async def register_channel_customer(
    request: Request,
    slug: str,
    payload: ChannelCustomerRegisterRequest = Body(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await channel_service.register_customer(
            db=db,
            slug=slug,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            customer_profile=payload.customer_profile,
            client_ip=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
    except IntegrityError:
        await db.rollback()
        raise BusinessException(code=409, msg="该手机号已完成登记，请勿重复提交")
    return ResponseModel(data=result, msg=result["message"])


@router.post("/auth/login", summary="渠道登录", response_model=ResponseModel)
async def channel_login(payload: ChannelLoginRequest = Body(...), db: AsyncSession = Depends(get_db)):
    return ResponseModel(data=await channel_service.login(db, payload.account, payload.password))


@router.get("/me", summary="渠道当前账号", response_model=ResponseModel)
async def channel_me(partner: ChannelPartnerModel = Depends(get_current_channel)):
    return ResponseModel(data={
        "id": partner.id,
        "name": partner.name,
        "contact_name": partner.contact_name,
        "account": partner.account,
        "phone": partner.phone,
        "h5_path": f"/channel/register/{partner.h5_slug}",
    })


@router.get("/me/summary", summary="渠道积分汇总", response_model=ResponseModel)
async def channel_summary(
    db: AsyncSession = Depends(get_db),
    partner: ChannelPartnerModel = Depends(get_current_channel),
):
    return ResponseModel(data=await channel_service.summary(db, partner.id))


@router.get("/me/points", summary="渠道积分明细", response_model=ResponseModel)
async def channel_points(
    keyword: Optional[str] = Query(None),
    order_type: Optional[str] = Query(None, pattern=r"^(stock_out|renewal)$"),
    status: Optional[str] = Query(None, pattern=r"^(pending|settled)$"),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    partner: ChannelPartnerModel = Depends(get_current_channel),
):
    data = await channel_service.list_points(
        db, partner.id, keyword, order_type, status, start_time, end_time, page, page_size
    )
    return ResponseModel(data=data)


@router.get("/me/customers", summary="渠道推荐客户", response_model=ResponseModel)
async def channel_customers(
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    partner: ChannelPartnerModel = Depends(get_current_channel),
):
    return ResponseModel(data=await channel_service.list_customers(
        db, partner.id, keyword, page, page_size
    ))


@router.get("/admin/settings", summary="获取渠道积分默认比例", response_model=ResponseModel)
async def admin_get_settings(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_super_admin),
):
    return ResponseModel(data=await channel_service.get_settings(db))


@router.put("/admin/settings", summary="更新渠道积分默认比例", response_model=ResponseModel)
async def admin_update_settings(
    payload: ChannelSettingsUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin),
):
    data = await channel_service.update_settings(
        db,
        payload.default_stock_out_rate,
        payload.default_renewal_rate,
        current_user.id,
    )
    return ResponseModel(data=data, msg="默认积分比例已更新")


@router.get("/admin/partners", summary="渠道伙伴列表", response_model=ResponseModel)
async def admin_list_partners(
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None, pattern=r"^(enable|disable)$"),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_super_admin),
):
    items = await channel_service.list_partners(db, keyword, status)
    return ResponseModel(data={"items": items, "total": len(items)})


@router.post("/admin/partners", summary="创建渠道伙伴", response_model=ResponseModel)
async def admin_create_partner(
    payload: ChannelPartnerCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin),
):
    data = await channel_service.create_partner(db, payload, current_user.id)
    return ResponseModel(data=data, msg="渠道创建成功")


@router.put("/admin/partners/{partner_id}", summary="更新渠道伙伴", response_model=ResponseModel)
async def admin_update_partner(
    partner_id: int = Path(...),
    payload: ChannelPartnerUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_super_admin),
):
    return ResponseModel(data=await channel_service.update_partner(db, partner_id, payload), msg="渠道已更新")


@router.post("/admin/partners/{partner_id}/reset-password", summary="重置渠道密码", response_model=ResponseModel)
async def admin_reset_partner_password(
    partner_id: int = Path(...),
    payload: ChannelPasswordResetRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_super_admin),
):
    await channel_service.reset_password(db, partner_id, payload.new_password)
    return ResponseModel(msg="渠道密码已重置")


@router.get("/admin/points", summary="全部渠道积分明细", response_model=ResponseModel)
async def admin_points(
    channel_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    order_type: Optional[str] = Query(None, pattern=r"^(stock_out|renewal)$"),
    status: Optional[str] = Query(None, pattern=r"^(pending|settled)$"),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_super_admin),
):
    data = await channel_service.list_points(
        db, channel_id, keyword, order_type, status, start_time, end_time, page, page_size, True
    )
    return ResponseModel(data=data)


@router.post("/admin/points/settle", summary="确认结算推广积分", response_model=ResponseModel)
async def admin_settle_points(
    payload: ChannelPointsSettleRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin),
):
    data = await channel_service.settle_points(db, payload.point_ids, current_user.id)
    return ResponseModel(data=data, msg=f"已确认结算 {data['settled_count']} 条积分")
