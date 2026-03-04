"""
供应商相关 Schema
"""
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class SupplierType(str, Enum):
    """供应商类型"""
    CMCC = "cmcc"
    CUCC = "cucc"
    CTCC = "ctcc"
    MVNO = "mvno"
    OTHER = "other"


class SupplierStatus(str, Enum):
    """供应商状态"""
    ENABLE = "enable"
    DISABLE = "disable"


# ========== 供应商 ==========

class SupplierCreate(BaseModel):
    """创建供应商"""
    name: str = Field(..., min_length=1, max_length=100, description="供应商名称")
    code: str = Field(..., min_length=1, max_length=50, description="供应商编码")
    type: SupplierType = Field(default=SupplierType.OTHER, description="供应商类型")
    contact_name: Optional[str] = Field(None, max_length=50, description="联系人")
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    contact_email: Optional[str] = Field(None, max_length=100, description="联系邮箱")
    api_url: Optional[str] = Field(None, max_length=255, description="API地址")
    api_key: Optional[str] = Field(None, max_length=255, description="API Key")
    api_secret: Optional[str] = Field(None, max_length=255, description="API Secret")
    api_config: Optional[dict] = Field(None, description="API配置")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class SupplierUpdate(BaseModel):
    """更新供应商"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[SupplierType] = None
    contact_name: Optional[str] = Field(None, max_length=50)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=100)
    api_url: Optional[str] = Field(None, max_length=255)
    api_key: Optional[str] = Field(None, max_length=255)
    api_secret: Optional[str] = Field(None, max_length=255)
    api_config: Optional[dict] = None
    sync_interval: Optional[int] = Field(None, ge=1, le=1440)
    remark: Optional[str] = Field(None, max_length=500)
    status: Optional[SupplierStatus] = None


class SupplierInfo(BaseModel):
    """供应商信息"""
    id: int
    name: str
    code: str
    type: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    api_url: Optional[str] = None
    api_config: Optional[dict] = None
    remark: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SupplierQuery(BaseModel):
    """供应商查询参数"""
    keyword: Optional[str] = Field(None, description="关键字搜索")
    type: Optional[SupplierType] = Field(None, description="供应商类型")
    status: Optional[SupplierStatus] = Field(None, description="状态")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class SupplierListResponse(BaseModel):
    """供应商列表响应"""
    list: List[SupplierInfo]
    total: int
    page: int
    page_size: int
