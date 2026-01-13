"""
套餐数据模型
"""
from typing import Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum as PyEnum


class PackageType(str, PyEnum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    TRAFFIC = "traffic"


class PackageStatus(str, PyEnum):
    ENABLE = "enable"
    DISABLE = "disable"


class PackageCreate(BaseModel):
    """创建套餐"""
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    type: PackageType
    data_allowance: int = Field(..., gt=0, description="流量额度(MB)")
    price: Decimal = Field(..., gt=0)
    validity_days: int = Field(..., gt=0)
    carrier: Optional[str] = None
    description: Optional[str] = None


class PackageUpdate(BaseModel):
    """更新套餐"""
    name: Optional[str] = None
    data_allowance: Optional[int] = None
    price: Optional[Decimal] = None
    validity_days: Optional[int] = None
    status: Optional[PackageStatus] = None
    description: Optional[str] = None


class PackageInfo(BaseModel):
    """套餐信息"""
    id: int
    name: str
    code: str
    type: PackageType
    data_allowance: int
    price: Decimal
    validity_days: int
    carrier: Optional[str] = None
    status: PackageStatus
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
