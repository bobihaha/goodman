"""
物联网卡模块接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.iot_card import (
    IoTCardCreate, IoTCardUpdate, IoTCardInfo, 
    IoTCardQuery, IoTCardActivate, IoTCardBindDevice,
    CardStatus, Carrier
)
from app.schemas.common import ResponseModel
from app.services.iot_card_service import IoTCardService
from app.db.database import get_db
from app.utils.auth import get_current_user
from app.schemas.user import UserInfo

router = APIRouter()


@router.post("/create", summary="添加物联网卡", response_model=ResponseModel)
async def create_card(
    card_data: IoTCardCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """添加单张物联网卡"""
    card_info = await IoTCardService.create_card(db, card_data, current_user.id)
    return ResponseModel(data=card_info.model_dump())


@router.get("/list", summary="物联网卡列表", response_model=ResponseModel)
async def get_card_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    iccid: Optional[str] = None,
    msisdn: Optional[str] = None,
    carrier: Optional[Carrier] = None,
    status: Optional[CardStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """查询物联网卡列表"""
    query = IoTCardQuery(
        page=page, page_size=page_size,
        iccid=iccid, msisdn=msisdn, 
        carrier=carrier, status=status
    )
    cards, total = await IoTCardService.get_card_list(db, query, current_user)
    return ResponseModel(data={
        "list": [card.model_dump() for card in cards],
        "total": total,
        "page": page,
        "page_size": page_size
    })


@router.get("/detail/{card_id}", summary="物联网卡详情", response_model=ResponseModel)
async def get_card_detail(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """获取物联网卡详情"""
    card_info = await IoTCardService.get_card_by_id(db, card_id)
    return ResponseModel(data=card_info.model_dump())


@router.put("/update/{card_id}", summary="更新物联网卡", response_model=ResponseModel)
async def update_card(
    card_id: int,
    card_data: IoTCardUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """更新物联网卡信息"""
    card_info = await IoTCardService.update_card(db, card_id, card_data)
    return ResponseModel(data=card_info.model_dump())


@router.post("/activate", summary="激活物联网卡", response_model=ResponseModel)
async def activate_card(
    data: IoTCardActivate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """激活物联网卡并开通套餐"""
    card_info = await IoTCardService.activate_card(db, data)
    return ResponseModel(msg="激活成功", data=card_info.model_dump())


@router.post("/suspend/{card_id}", summary="停机", response_model=ResponseModel)
async def suspend_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """停机物联网卡"""
    await IoTCardService.change_card_status(db, card_id, CardStatus.SUSPENDED)
    return ResponseModel(msg="停机成功")


@router.post("/resume/{card_id}", summary="复机", response_model=ResponseModel)
async def resume_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """复机物联网卡"""
    await IoTCardService.change_card_status(db, card_id, CardStatus.ACTIVE)
    return ResponseModel(msg="复机成功")


@router.post("/bind-device", summary="绑定设备", response_model=ResponseModel)
async def bind_device(
    data: IoTCardBindDevice = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """物联网卡绑定设备"""
    await IoTCardService.bind_device(db, data.card_id, data.device_id)
    return ResponseModel(msg="绑定成功")


@router.post("/unbind-device/{card_id}", summary="解绑设备", response_model=ResponseModel)
async def unbind_device(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """物联网卡解绑设备"""
    await IoTCardService.unbind_device(db, card_id)
    return ResponseModel(msg="解绑成功")


@router.get("/statistics", summary="卡片统计", response_model=ResponseModel)
async def get_card_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """获取物联网卡统计信息"""
    stats = await IoTCardService.get_statistics(db, current_user)
    return ResponseModel(data=stats)
