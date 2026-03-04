"""
物联网卡 Pydantic 模型
"""
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field
from enum import Enum


class CardStatus(str, Enum):
    stock = "stock"
    testing = "testing"
    silent = "silent"
    activated = "activated"
    expired = "expired"
    suspended = "suspended"
    cancelled = "cancelled"


class CarrierType(str, Enum):
    cmcc = "cmcc"
    cucc = "cucc"
    ctcc = "ctcc"


class PeriodType(str, Enum):
    monthly = "monthly"
    yearly = "yearly"


# ============ 查询相关 ============

class CardQuery(BaseModel):
    """卡片查询参数"""
    keyword: Optional[str] = Field(None, description="关键词 (ICCID/MSISDN/后6位)")
    status: Optional[CardStatus] = Field(None, description="卡片状态")
    carrier: Optional[CarrierType] = Field(None, description="运营商")
    period_type: Optional[PeriodType] = Field(None, description="周期类型")
    pool_id: Optional[int] = Field(None, description="流量池ID")
    is_pool_member: Optional[bool] = Field(None, description="是否加入流量池")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class CardSearchRequest(BaseModel):
    """快速搜索请求 (支持后6位)"""
    keyword: str = Field(..., min_length=1, max_length=30, description="ICCID/MSISDN/后6位")


# ============ 卡片信息 ============

class CardInfo(BaseModel):
    """卡片信息"""
    id: int
    iccid: str
    imsi: Optional[str] = None
    msisdn: Optional[str] = None
    user_id: Optional[int] = None
    supplier_id: Optional[int] = None
    batch_id: Optional[int] = None
    sale_package_id: Optional[int] = None
    sale_price: Optional[float] = Field(None, description="套餐单价(元/周期)")
    # 规格
    carrier: Optional[str] = None
    carrier_name: Optional[str] = None
    flow_size: int
    flow_size_display: Optional[str] = None
    period_type: Optional[str] = None
    period_name: Optional[str] = None
    spec_name: Optional[str] = None
    # 日期
    test_expire_date: Optional[str] = None
    silent_expire_date: Optional[str] = None
    activated_at: Optional[str] = None
    expired_at: Optional[str] = None
    # 流量
    data_used: int = 0
    data_total: int
    data_remain: int = 0
    data_usage_percent: float = 0
    data_sync_at: Optional[str] = None
    # 状态
    status: Optional[str] = None
    status_name: Optional[str] = None
    suspend_type: Optional[str] = None
    suspend_type_name: Optional[str] = None
    suspend_at: Optional[str] = None
    suspend_reason: Optional[str] = None
    # 流量池
    pool_id: Optional[int] = None
    is_pool_member: bool = False
    # 其他
    remark: Optional[str] = None
    stock_in_at: Optional[str] = None
    stock_out_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class CardListResponse(BaseModel):
    """卡片列表响应"""
    total: int
    page: int
    page_size: int
    items: List[CardInfo]


class CardStats(BaseModel):
    """卡片统计"""
    total: int = 0
    stock: int = 0
    testing: int = 0
    silent: int = 0
    activated: int = 0
    expired: int = 0
    suspended: int = 0
    cancelled: int = 0


# ============ 划拨相关 ============

class CardTransferRequest(BaseModel):
    """单卡划拨请求"""
    to_user_id: int = Field(..., description="目标用户ID")
    remark: Optional[str] = Field(None, max_length=200, description="备注")


class BatchTransferRequest(BaseModel):
    """批量划拨请求"""
    card_ids: List[int] = Field(..., min_length=1, description="卡片ID列表")
    to_user_id: int = Field(..., description="目标用户ID")
    remark: Optional[str] = Field(None, max_length=200, description="备注")


class TransferRecord(BaseModel):
    """划拨记录"""
    id: int
    card_id: int
    iccid: str
    from_user_id: int
    from_user_name: Optional[str] = None
    to_user_id: int
    to_user_name: Optional[str] = None
    operator_id: int
    operator_name: Optional[str] = None
    remark: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


# ============ 备注相关 ============

class CardRemarkRequest(BaseModel):
    """单卡备注请求"""
    remark: str = Field(..., max_length=500, description="备注内容")


class BatchRemarkRequest(BaseModel):
    """批量备注请求"""
    card_ids: List[int] = Field(..., min_length=1, description="卡片ID列表")
    remark: str = Field(..., max_length=500, description="备注内容")


# ============ 导出相关 ============

class CardExportRequest(BaseModel):
    """卡片导出请求"""
    card_ids: Optional[List[int]] = Field(None, description="指定卡片ID列表 (为空则导出全部)")
    status: Optional[CardStatus] = Field(None, description="按状态筛选")
    carrier: Optional[CarrierType] = Field(None, description="按运营商筛选")
