"""
物联网卡表模型
"""
from sqlalchemy import Column, String, Integer, Enum, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.db.models.base import BaseModel


class CardStatus(str, PyEnum):
    """卡片状态"""
    INACTIVE = "inactive"       # 未激活
    ACTIVE = "active"           # 已激活
    SUSPENDED = "suspended"     # 已停机
    DEACTIVATED = "deactivated" # 已销户
    TESTING = "testing"         # 测试期


class Carrier(str, PyEnum):
    """运营商"""
    CHINA_MOBILE = "china_mobile"    # 中国移动
    CHINA_UNICOM = "china_unicom"    # 中国联通
    CHINA_TELECOM = "china_telecom"  # 中国电信


class IoTCardModel(BaseModel):
    """物联网卡表"""
    __tablename__ = "iot_cards"

    iccid = Column(String(20), unique=True, index=True, nullable=False, comment="ICCID（集成电路卡识别码）")
    imsi = Column(String(15), unique=True, index=True, nullable=True, comment="IMSI（国际移动用户识别码）")
    msisdn = Column(String(15), unique=True, index=True, nullable=True, comment="MSISDN（手机号码）")
    
    carrier = Column(Enum(Carrier), nullable=False, comment="运营商")
    status = Column(Enum(CardStatus), default=CardStatus.INACTIVE, comment="卡片状态")
    
    # 套餐关联
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=True, comment="当前套餐ID")
    package_start_date = Column(DateTime, nullable=True, comment="套餐开始日期")
    package_end_date = Column(DateTime, nullable=True, comment="套餐到期日期")
    
    # 流量信息（单位：KB）
    total_data = Column(BigInteger, default=0, server_default="0",comment="套餐总流量(KB)")
    used_data = Column(BigInteger, default=0, server_default="0",comment="已用流量(KB)")
    
    # 设备绑定
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True, comment="绑定设备ID")
    
    # 所属用户/企业
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="所属用户ID")
    
    # 激活信息
    activate_date = Column(DateTime, nullable=True, comment="激活日期")
    
    # 备注
    remark = Column(String(500), nullable=True, comment="备注")
