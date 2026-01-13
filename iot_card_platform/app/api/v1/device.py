"""
设备模块接口
"""
from fastapi import APIRouter, Depends, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceInfo
from app.schemas.common import ResponseModel
from app.services.device_service import DeviceService
from app.db.database import get_db
from app.utils.auth import get_current_user
from app.schemas.user import UserInfo

router = APIRouter()


@router.post("/create", summary="添加设备", response_model=ResponseModel)
async def create_device(
    data: DeviceCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    device_info = await DeviceService.create_device(db, data, current_user.id)
    return ResponseModel(data=device_info.model_dump())


@router.get("/list", summary="设备列表", response_model=ResponseModel)
async def get_device_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    devices, total = await DeviceService.get_device_list(db, page, page_size, current_user)
    return ResponseModel(data={
        "list": [d.model_dump() for d in devices],
        "total": total,
        "page": page,
        "page_size": page_size
    })


@router.get("/detail/{device_id}", summary="设备详情", response_model=ResponseModel)
async def get_device_detail(
    device_id: int,
    db: AsyncSession = Depends(get_db)
):
    device_info = await DeviceService.get_device_by_id(db, device_id)
    return ResponseModel(data=device_info.model_dump())


@router.put("/update/{device_id}", summary="更新设备", response_model=ResponseModel)
async def update_device(
    device_id: int,
    data: DeviceUpdate = Body(...),
    db: AsyncSession = Depends(get_db)
):
    device_info = await DeviceService.update_device(db, device_id, data)
    return ResponseModel(data=device_info.model_dump())


@router.delete("/delete/{device_id}", summary="删除设备", response_model=ResponseModel)
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db)
):
    await DeviceService.delete_device(db, device_id)
    return ResponseModel(msg="删除成功")
