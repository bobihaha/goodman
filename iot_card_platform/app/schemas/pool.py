"""
流量池相关 Pydantic 模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from app.flow_packages import FLOW_PACKAGE_LABELS, is_valid_flow_package_size


class PoolCreate(BaseModel):
    """创建流量池请求"""
    name: str = Field(..., min_length=1, max_length=100, description="流量池名称")
    carrier: str = Field(..., description="运营商: cmcc/cucc/ctcc")
    flow_size: int = Field(..., gt=0, description="套餐流量(MB)")
    period_type: str = Field(..., description="周期类型: monthly/yearly")
    alert_threshold_1: Optional[int] = Field(None, ge=0, le=100, description="告警阈值1百分比")
    alert_threshold_2: Optional[int] = Field(None, ge=0, le=100, description="告警阈值2百分比")
    alert_threshold_3: Optional[int] = Field(None, ge=0, le=100, description="告警阈值3百分比")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class PoolUpdate(BaseModel):
    """更新流量池请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="流量池名称")
    alert_threshold_1: Optional[int] = Field(None, ge=0, le=100, description="告警阈值1百分比")
    alert_threshold_2: Optional[int] = Field(None, ge=0, le=100, description="告警阈值2百分比")
    alert_threshold_3: Optional[int] = Field(None, ge=0, le=100, description="告警阈值3百分比")
    status: Optional[str] = Field(None, description="状态: enable/disable")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class PoolAddCards(BaseModel):
    """添加卡片到流量池"""
    card_ids: List[int] = Field(..., min_length=1, description="卡片ID列表")
    remark: Optional[str] = Field(None, max_length=200, description="备注")


class PoolRemoveCards(BaseModel):
    """从流量池移除卡片"""
    card_ids: List[int] = Field(..., min_length=1, description="卡片ID列表")
    remark: Optional[str] = Field(None, max_length=200, description="备注")


class PoolRechargeRequest(BaseModel):
    """流量池后台补量"""
    added_flow_mb: int = Field(..., gt=0, description="增加流量(MB)")
    remark: Optional[str] = Field(None, max_length=200, description="备注")

    @field_validator("added_flow_mb")
    @classmethod
    def validate_added_flow_mb(cls, value: int) -> int:
        if not is_valid_flow_package_size(value):
            supported = " / ".join(FLOW_PACKAGE_LABELS[size] for size in FLOW_PACKAGE_LABELS)
            raise ValueError(f"仅支持固定补量规格: {supported}")
        return value


class PoolTopupPurchaseRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="购买份数")
    remark: Optional[str] = Field(None, max_length=200, description="备注")


class PoolInfo(BaseModel):
    """流量池信息"""
    id: int
    name: str
    carrier: str
    carrier_name: str
    flow_size: int
    flow_size_display: str
    period_type: str
    period_name: str
    spec_name: str
    user_id: Optional[int]
    card_count: int
    data_total: int
    data_used: int
    data_remain: int
    usage_percent: float
    alert_threshold_1: Optional[int]
    alert_threshold_2: Optional[int]
    alert_threshold_3: Optional[int]
    is_alert: bool
    is_exceed: bool
    status: str
    status_name: str
    remark: Optional[str]
    created_at: Optional[str]


class PoolUsageInfo(BaseModel):
    """流量池用量统计"""
    pool_id: int
    pool_name: str
    spec_name: str
    card_count: int
    data_total: int
    data_used: int
    data_remain: int
    usage_percent: float
    is_alert: bool
    is_exceed: bool
    cards: Optional[List[dict]] = None  # 池内卡片用量明细


class PoolCardResult(BaseModel):
    """流量池卡片操作结果"""
    total: int
    success: int
    failed: int
    fail_details: Optional[List[dict]] = None
