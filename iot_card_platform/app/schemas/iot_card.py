"""
物联网卡数据模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum as PyEnum


class CardStatus(str, PyEnum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"
    TESTING = "testing"


class Carrier(str, PyEnum):
    CHINA_MOBILE = "china_mobile"
    CHINA_UNICOM = "china_unicom"
    CHINA_TELECOM = "china_telecom"


class IoTCardCreate(BaseModel):
    """创建物联网卡"""
    iccid: str = Field(..., min_length=19, max_length=20, description="ICCID")
    imsi: Optional[str] = Field(None, max_length=15, description="IMSI")
    msisdn: Optional[str] = Field(None, max_length=15, description="MSISDN")
    carrier: Carrier = Field(..., description="运营商")
    remark: Optional[str] = None


class IoTCardUpdate(BaseModel):
    """更新物联网卡"""
    imsi: Optional[str] = None
    msisdn: Optional[str] = None
    status: Optional[CardStatus] = None
    remark: Optional[str] = None


class IoTCardInfo(BaseModel):
    """物联网卡信息"""
    id: int
    iccid: str
    imsi: Optional[str] = None
    msisdn: Optional[str] = None
    carrier: Carrier
    status: CardStatus
    package_id: Optional[int] = None
    package_name: Optional[str] = None
    package_start_date: Optional[datetime] = None
    package_end_date: Optional[datetime] = None
    total_data: int = 0
    used_data: int = 0
    remaining_data: int = 0
    device_id: Optional[int] = None
    device_name: Optional[str] = None
    user_id: Optional[int] = None
    activate_date: Optional[datetime] = None
    remark: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IoTCardQuery(BaseModel):
    """物联网卡查询"""
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)
    iccid: Optional[str] = None
    msisdn: Optional[str] = None
    carrier: Optional[Carrier] = None
    status: Optional[CardStatus] = None


class IoTCardActivate(BaseModel):
    """激活物联网卡"""
    iccid: str
    package_id: int = Field(..., description="套餐ID")


class IoTCardBindDevice(BaseModel):
    """绑定设备"""
    card_id: int
    device_id: int
