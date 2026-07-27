"""
套餐周期管理相关 Schema
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class BatchForceActivateRequest(BaseModel):
    """批量强制激活请求"""
    iccids: List[str] = Field(..., min_length=1, max_length=10000, description="ICCID 列表")
    reason: Optional[str] = Field(None, max_length=500, description="强制激活原因")


class BatchCancelPackagePeriodRequest(BaseModel):
    """批量取消计划套餐请求"""
    iccids: List[str] = Field(..., min_length=1, max_length=10000, description="ICCID 列表")
    cancel_count: int = Field(..., ge=1, le=120, description="减少的套餐周期数")
    reason: Optional[str] = Field(None, max_length=500, description="取消原因")


class BatchChangePackageRequest(BaseModel):
    """批量修改本地销售套餐请求"""
    iccids: List[str] = Field(..., min_length=1, max_length=10000, description="ICCID 列表")
    target_sale_package_id: int = Field(..., gt=0, description="目标销售套餐ID")
    reason: Optional[str] = Field(None, max_length=500, description="修改原因")


class PackagePeriodOperationRecord(BaseModel):
    id: int
    action: str
    operation_time: Optional[str] = None
    card_no: Optional[str] = None
    operator_name: Optional[str] = None
    detail: Optional[str] = None


class PackagePeriodOperationQuery(BaseModel):
    action: str = Field(..., pattern="^(force_activate|cancel_period|change_package)$")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
