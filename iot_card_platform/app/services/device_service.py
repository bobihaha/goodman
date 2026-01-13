"""
设备业务逻辑
"""
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_

from app.db.models.device import DeviceModel
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceInfo
from app.schemas.user import UserInfo
from app.utils.exceptions import BusinessException


class DeviceService:

    @staticmethod
    async def create_device(db: AsyncSession, data: DeviceCreate, user_id: int) -> DeviceInfo:
        # 检查SN是否已存在
        existing = await db.execute(
            select(DeviceModel).where(DeviceModel.sn == data.sn)
        )
        if existing.scalar_one_or_none():
            raise BusinessException(code=400, msg="设备序列号已存在")
        
        device = DeviceModel(**data.model_dump(), user_id=user_id)
        db.add(device)
        await db.flush()
        return DeviceInfo.model_validate(device)

    @staticmethod
    async def get_device_list(
        db: AsyncSession, 
        page: int, 
        page_size: int,
        current_user: UserInfo
    ) -> Tuple[List[DeviceInfo], int]:
        offset = (page - 1) * page_size
        
        conditions = [DeviceModel.is_deleted == 0]
        if current_user.role != "admin":
            conditions.append(DeviceModel.user_id == current_user.id)
        
        stmt = select(DeviceModel).where(and_(*conditions)).offset(offset).limit(page_size)
        result = await db.execute(stmt)
        devices = result.scalars().all()
        
        total_stmt = select(func.count(DeviceModel.id)).where(and_(*conditions))
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0
        
        return [DeviceInfo.model_validate(d) for d in devices], total

    @staticmethod
    async def get_device_by_id(db: AsyncSession, device_id: int) -> DeviceInfo:
        result = await db.execute(
            select(DeviceModel).where(
                DeviceModel.id == device_id,
                DeviceModel.is_deleted == 0
            )
        )
        device = result.scalar_one_or_none()
        if not device:
            raise BusinessException(code=404, msg="设备不存在")
        return DeviceInfo.model_validate(device)

    @staticmethod
    async def update_device(db: AsyncSession, device_id: int, data: DeviceUpdate) -> DeviceInfo:
        result = await db.execute(
            select(DeviceModel).where(
                DeviceModel.id == device_id,
                DeviceModel.is_deleted == 0
            )
        )
        device = result.scalar_one_or_none()
        if not device:
            raise BusinessException(code=404, msg="设备不存在")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(device, key, value)
        
        await db.flush()
        return DeviceInfo.model_validate(device)

    @staticmethod
    async def delete_device(db: AsyncSession, device_id: int):
        result = await db.execute(
            select(DeviceModel).where(
                DeviceModel.id == device_id,
                DeviceModel.is_deleted == 0
            )
        )
        device = result.scalar_one_or_none()
        if not device:
            raise BusinessException(code=404, msg="设备不存在")
        
        device.is_deleted = 1
        await db.flush()
