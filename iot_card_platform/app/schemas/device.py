"""
设备数据模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum as PyEnum


class DeviceStatus(str, PyEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    FAULT = "fault"


class DeviceCreate(BaseModel):
    """创建设备"""
    name: str = Field(..., max_length=100)
    sn: str = Field(..., max_length=50)
    model: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    longitude: Optional[str] = None
    latitude: Optional[str] = None
    remark: Optional[str] = None


class DeviceUpdate(BaseModel):
    """更新设备"""
    name: Optional[str] = None
    model: Optional[str] = None
    type: Optional[str] = None
    status: Optional[DeviceStatus] = None
    location: Optional[str] = None
    longitude: Optional[str] = None
    latitude: Optional[str] = None
    remark: Optional[str] = None


class DeviceInfo(BaseModel):
    """设备信息"""
    id: int
    name: str
    sn: str
    model: Optional[str] = None
    type: Optional[str] = None
    status: DeviceStatus
    location: Optional[str] = None
    longitude: Optional[str] = None
    latitude: Optional[str] = None
    user_id: Optional[int] = None
    remark: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
