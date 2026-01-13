"""
设备表模型
"""
from sqlalchemy import Column, String, Integer, Enum, ForeignKey
from enum import Enum as PyEnum

from app.db.models.base import BaseModel


class DeviceStatus(str, PyEnum):
    """设备状态"""
    ONLINE = "online"
    OFFLINE = "offline"
    FAULT = "fault"


class DeviceModel(BaseModel):
    """设备表"""
    __tablename__ = "devices"

    name = Column(String(100), nullable=False, comment="设备名称")
    sn = Column(String(50), unique=True, nullable=False, comment="设备序列号")
    model = Column(String(50), nullable=True, comment="设备型号")
    device_type = Column(String(50), nullable=True, comment="设备类型")
    
    status = Column(Enum(DeviceStatus), default=DeviceStatus.OFFLINE, comment="设备状态")
    
    # 位置信息
    location = Column(String(200), nullable=True, comment="位置描述")
    longitude = Column(String(20), nullable=True, comment="经度")
    latitude = Column(String(20), nullable=True, comment="纬度")
    
    # 所属用户
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="所属用户ID")
    
    remark = Column(String(500), nullable=True, comment="备注")
