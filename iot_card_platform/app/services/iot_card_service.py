"""
物联网卡业务逻辑
"""
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_

from app.db.models.iot_card import IoTCardModel, CardStatus
from app.db.models.package import PackageModel
from app.db.models.device import DeviceModel
from app.schemas.iot_card import (
    IoTCardCreate, IoTCardUpdate, IoTCardInfo, 
    IoTCardQuery, IoTCardActivate
)
from app.schemas.user import UserInfo
from app.utils.exceptions import BusinessException


class IoTCardService:

    @staticmethod
    async def create_card(db: AsyncSession, data: IoTCardCreate, user_id: int) -> IoTCardInfo:
        # 检查ICCID是否已存在
        existing = await db.execute(
            select(IoTCardModel).where(IoTCardModel.iccid == data.iccid)
        )
        if existing.scalar_one_or_none():
            raise BusinessException(code=400, msg="ICCID已存在")
        
        card = IoTCardModel(
            iccid=data.iccid,
            imsi=data.imsi,
            msisdn=data.msisdn,
            carrier=data.carrier,
            status=CardStatus.INACTIVE,
            user_id=user_id,
            remark=data.remark
        )
        db.add(card)
        await db.flush()
        return await IoTCardService._to_card_info(db, card)

    @staticmethod
    async def get_card_list(
        db: AsyncSession, 
        query: IoTCardQuery, 
        current_user: UserInfo
    ) -> Tuple[List[IoTCardInfo], int]:
        offset = (query.page - 1) * query.page_size
        
        conditions = [IoTCardModel.is_deleted == 0]
        
        # 非管理员只能查看自己的卡
        if current_user.role != "admin":
            conditions.append(IoTCardModel.user_id == current_user.id)
        
        if query.iccid:
            conditions.append(IoTCardModel.iccid.like(f"%{query.iccid}%"))
        if query.msisdn:
            conditions.append(IoTCardModel.msisdn.like(f"%{query.msisdn}%"))
        if query.carrier:
            conditions.append(IoTCardModel.carrier == query.carrier)
        if query.status:
            conditions.append(IoTCardModel.status == query.status)
        
        stmt = select(IoTCardModel).where(and_(*conditions)).offset(offset).limit(query.page_size)
        result = await db.execute(stmt)
        cards = result.scalars().all()
        
        total_stmt = select(func.count(IoTCardModel.id)).where(and_(*conditions))
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0
        
        card_infos = [await IoTCardService._to_card_info(db, c) for c in cards]
        return card_infos, total

    @staticmethod
    async def get_card_by_id(db: AsyncSession, card_id: int) -> IoTCardInfo:
        result = await db.execute(
            select(IoTCardModel).where(
                IoTCardModel.id == card_id,
                IoTCardModel.is_deleted == 0
            )
        )
        card = result.scalar_one_or_none()
        if not card:
            raise BusinessException(code=404, msg="物联网卡不存在")
        return await IoTCardService._to_card_info(db, card)

    @staticmethod
    async def update_card(db: AsyncSession, card_id: int, data: IoTCardUpdate) -> IoTCardInfo:
        result = await db.execute(
            select(IoTCardModel).where(
                IoTCardModel.id == card_id,
                IoTCardModel.is_deleted == 0
            )
        )
        card = result.scalar_one_or_none()
        if not card:
            raise BusinessException(code=404, msg="物联网卡不存在")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(card, key, value)
        
        await db.flush()
        return await IoTCardService._to_card_info(db, card)

    @staticmethod
    async def activate_card(db: AsyncSession, data: IoTCardActivate) -> IoTCardInfo:
        # 查询卡片
        result = await db.execute(
            select(IoTCardModel).where(
                IoTCardModel.iccid == data.iccid,
                IoTCardModel.is_deleted == 0
            )
        )
        card = result.scalar_one_or_none()
        if not card:
            raise BusinessException(code=404, msg="物联网卡不存在")
        
        if card.status == CardStatus.ACTIVE:
            raise BusinessException(code=400, msg="卡片已激活")
        
        # 查询套餐
        pkg_result = await db.execute(
            select(PackageModel).where(
                PackageModel.id == data.package_id,
                PackageModel.is_deleted == 0
            )
        )
        package = pkg_result.scalar_one_or_none()
        if not package:
            raise BusinessException(code=404, msg="套餐不存在")
        
        # 激活卡片
        now = datetime.now()
        card.status = CardStatus.ACTIVE
        card.package_id = package.id
        card.package_start_date = now
        card.package_end_date = now + timedelta(days=package.validity_days)
        card.total_data = package.data_allowance * 1024  # MB 转 KB
        card.used_data = 0
        card.activate_date = now
        
        await db.flush()
        return await IoTCardService._to_card_info(db, card)

    @staticmethod
    async def change_card_status(db: AsyncSession, card_id: int, status: CardStatus):
        result = await db.execute(
            select(IoTCardModel).where(
                IoTCardModel.id == card_id,
                IoTCardModel.is_deleted == 0
            )
        )
        card = result.scalar_one_or_none()
        if not card:
            raise BusinessException(code=404, msg="物联网卡不存在")
        
        card.status = status
        await db.flush()

    @staticmethod
    async def bind_device(db: AsyncSession, card_id: int, device_id: int):
        # 查询卡片
        card_result = await db.execute(
            select(IoTCardModel).where(
                IoTCardModel.id == card_id,
                IoTCardModel.is_deleted == 0
            )
        )
        card = card_result.scalar_one_or_none()
        if not card:
            raise BusinessException(code=404, msg="物联网卡不存在")
        
        # 查询设备
        device_result = await db.execute(
            select(DeviceModel).where(
                DeviceModel.id == device_id,
                DeviceModel.is_deleted == 0
            )
        )
        device = device_result.scalar_one_or_none()
        if not device:
            raise BusinessException(code=404, msg="设备不存在")
        
        card.device_id = device_id
        await db.flush()

    @staticmethod
    async def unbind_device(db: AsyncSession, card_id: int):
        result = await db.execute(
            select(IoTCardModel).where(
                IoTCardModel.id == card_id,
                IoTCardModel.is_deleted == 0
            )
        )
        card = result.scalar_one_or_none()
        if not card:
            raise BusinessException(code=404, msg="物联网卡不存在")
        
        card.device_id = None
        await db.flush()

    @staticmethod
    async def get_statistics(db: AsyncSession, current_user: UserInfo) -> Dict[str, Any]:
        conditions = [IoTCardModel.is_deleted == 0]
        if current_user.role != "admin":
            conditions.append(IoTCardModel.user_id == current_user.id)
        
        # 总数
        total_result = await db.execute(
            select(func.count(IoTCardModel.id)).where(and_(*conditions))
        )
        total = total_result.scalar() or 0
        
        # 各状态数量
        status_stats = {}
        for status in CardStatus:
            result = await db.execute(
                select(func.count(IoTCardModel.id)).where(
                    and_(*conditions, IoTCardModel.status == status)
                )
            )
            status_stats[status.value] = result.scalar() or 0
        
        return {
            "total": total,
            "status_stats": status_stats
        }

    @staticmethod
    async def _to_card_info(db: AsyncSession, card: IoTCardModel) -> IoTCardInfo:
        """转换为卡片信息模型"""
        package_name = None
        device_name = None
        
        if card.package_id:
            pkg_result = await db.execute(
                select(PackageModel).where(PackageModel.id == card.package_id)
            )
            package = pkg_result.scalar_one_or_none()
            package_name = package.name if package else None
        
        if card.device_id:
            dev_result = await db.execute(
                select(DeviceModel).where(DeviceModel.id == card.device_id)
            )
            device = dev_result.scalar_one_or_none()
            device_name = device.name if device else None
        
        return IoTCardInfo(
            id=card.id,
            iccid=card.iccid,
            imsi=card.imsi,
            msisdn=card.msisdn,
            carrier=card.carrier,
            status=card.status,
            package_id=card.package_id,
            package_name=package_name,
            package_start_date=card.package_start_date,
            package_end_date=card.package_end_date,
            total_data=card.total_data,
            used_data=card.used_data,
            remaining_data=max(0, card.total_data - card.used_data),
            device_id=card.device_id,
            device_name=device_name,
            user_id=card.user_id,
            activate_date=card.activate_date,
            remark=card.remark,
            created_at=card.created_at
        )
