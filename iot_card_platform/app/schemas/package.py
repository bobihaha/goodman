"""
套餐相关 Schema
规格三要素: 运营商 + 流量 + 周期类型
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class CarrierType(str, Enum):
    """运营商类型"""
    cmcc = "cmcc"  # 中国移动
    cucc = "cucc"  # 中国联通
    ctcc = "ctcc"  # 中国电信


class PeriodType(str, Enum):
    """周期类型"""
    monthly = "monthly"  # 月包
    yearly = "yearly"    # 年包


class PackageStatus(str, Enum):
    """套餐状态"""
    enable = "enable"
    disable = "disable"


# ========== 底层套餐 (供应商套餐) ==========

class SupplierPackageCreate(BaseModel):
    """创建底层套餐"""
    supplier_id: int = Field(..., description="供应商ID")
    name: str = Field(..., min_length=1, max_length=100, description="套餐名称")
    code: str = Field(..., min_length=1, max_length=50, description="套餐编码")
    # 规格三要素
    carrier: CarrierType = Field(..., description="运营商")
    flow_size: int = Field(..., gt=0, description="流量大小(MB)")
    period_type: PeriodType = Field(default=PeriodType.monthly, description="周期类型: 月包/年包")
    # 有效期 (月包默认30天, 年包默认360天)
    effective_days: Optional[int] = Field(None, ge=1, description="激活后有效天数")
    # 价格
    price_cost: float = Field(..., ge=0, description="成本价(元)")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class SupplierPackageUpdate(BaseModel):
    """更新底层套餐"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    carrier: Optional[CarrierType] = None
    flow_size: Optional[int] = Field(None, gt=0)
    period_type: Optional[PeriodType] = None
    effective_days: Optional[int] = Field(None, ge=1)
    price_cost: Optional[float] = Field(None, ge=0)
    remark: Optional[str] = Field(None, max_length=500)
    status: Optional[PackageStatus] = None


class SupplierPackageInfo(BaseModel):
    """底层套餐信息"""
    id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    name: str
    code: str
    carrier: Optional[str] = None
    carrier_name: Optional[str] = None
    flow_size: int
    flow_size_display: Optional[str] = None
    period_type: Optional[str] = None
    period_name: Optional[str] = None
    effective_days: int
    spec_name: Optional[str] = None  # 规格名称: 移动1G/月
    price_cost: float
    remark: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SupplierPackageQuery(BaseModel):
    """底层套餐查询"""
    keyword: Optional[str] = Field(None, description="关键字搜索")
    supplier_id: Optional[int] = Field(None, description="供应商ID")
    carrier: Optional[CarrierType] = Field(None, description="运营商")
    period_type: Optional[PeriodType] = Field(None, description="周期类型")
    status: Optional[PackageStatus] = Field(None, description="状态")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class SupplierPackageListResponse(BaseModel):
    """底层套餐列表响应"""
    list: List[SupplierPackageInfo]
    total: int
    page: int
    page_size: int


# ========== 销售套餐 ==========

class SalePackageCreate(BaseModel):
    """创建销售套餐"""
    base_package_id: Optional[int] = Field(None, description="关联底层套餐ID")
    name: str = Field(..., min_length=1, max_length=100, description="套餐名称")
    code: str = Field(..., min_length=1, max_length=50, description="套餐编码")
    # 规格三要素
    carrier: CarrierType = Field(..., description="运营商")
    flow_size: int = Field(..., gt=0, description="流量大小(MB)")
    period_type: PeriodType = Field(default=PeriodType.monthly, description="周期类型")
    # 有效期
    effective_days: Optional[int] = Field(None, ge=1, description="激活后有效天数")
    # 价格
    price_cost: float = Field(..., ge=0, description="成本价(元)")
    price_sale: float = Field(..., ge=0, description="销售价(元)")
    # 展示配置
    is_public: bool = Field(default=False, description="是否公开")
    sort_order: int = Field(default=0, description="排序")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class SalePackageUpdate(BaseModel):
    """更新销售套餐"""
    base_package_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    carrier: Optional[CarrierType] = None
    flow_size: Optional[int] = Field(None, gt=0)
    period_type: Optional[PeriodType] = None
    effective_days: Optional[int] = Field(None, ge=1)
    price_cost: Optional[float] = Field(None, ge=0)
    price_sale: Optional[float] = Field(None, ge=0)
    is_public: Optional[bool] = None
    sort_order: Optional[int] = None
    remark: Optional[str] = Field(None, max_length=500)
    status: Optional[PackageStatus] = None


class SalePackageInfo(BaseModel):
    """销售套餐信息"""
    id: int
    user_id: Optional[int] = None
    base_package_id: Optional[int] = None
    base_package_name: Optional[str] = None
    name: str
    code: str
    carrier: Optional[str] = None
    carrier_name: Optional[str] = None
    flow_size: int
    flow_size_display: Optional[str] = None
    period_type: Optional[str] = None
    period_name: Optional[str] = None
    effective_days: int
    spec_name: Optional[str] = None  # 规格名称
    price_cost: float
    price_sale: float
    profit: float = 0
    is_public: bool = False
    sort_order: int = 0
    remark: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SalePackageQuery(BaseModel):
    """销售套餐查询"""
    keyword: Optional[str] = Field(None, description="关键字搜索")
    user_id: Optional[int] = Field(None, description="用户ID")
    carrier: Optional[CarrierType] = Field(None, description="运营商")
    period_type: Optional[PeriodType] = Field(None, description="周期类型")
    is_public: Optional[bool] = Field(None, description="是否公开")
    status: Optional[PackageStatus] = Field(None, description="状态")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class SalePackageListResponse(BaseModel):
    """销售套餐列表响应"""
    list: List[SalePackageInfo]
    total: int
    page: int
    page_size: int
