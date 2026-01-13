"""
套餐表模型
"""
from sqlalchemy import Column, String, Integer, Enum, Numeric
from enum import Enum as PyEnum

from app.db.models.base import BaseModel


class PackageType(str, PyEnum):
    """套餐类型"""
    MONTHLY = "monthly"     # 月套餐
    QUARTERLY = "quarterly" # 季套餐
    YEARLY = "yearly"       # 年套餐
    TRAFFIC = "traffic"     # 流量包


class PackageStatus(str, PyEnum):
    """套餐状态"""
    ENABLE = "enable"
    DISABLE = "disable"


class PackageModel(BaseModel):
    """套餐表"""
    __tablename__ = "packages"

    name = Column(String(100), nullable=False, comment="套餐名称")
    code = Column(String(50), unique=True, nullable=False, comment="套餐编码")
    package_type = Column(Enum(PackageType), nullable=False, comment="套餐类型")
    
    # 流量配置（单位：MB）
    data_allowance = Column(Integer, nullable=False, comment="流量额度(MB)")
    
    # 价格（单位：元）
    price = Column(Numeric(10, 2), nullable=False, comment="套餐价格")
    
    # 有效期（天）
    validity_days = Column(Integer, nullable=False, comment="有效期(天)")
    
    # 适用运营商（空表示全部）
    carrier = Column(String(50), nullable=True, comment="适用运营商")
    
    status = Column(Enum(PackageStatus), default=PackageStatus.ENABLE, comment="套餐状态")
    description = Column(String(500), nullable=True, comment="套餐描述")
