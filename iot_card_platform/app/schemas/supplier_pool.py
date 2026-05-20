"""
供应商侧流量池 Schema
"""
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class SupplierTrafficPoolQuery(BaseModel):
    supplier_name: Optional[str] = Field(None, description="供应商名称")
    carrier: Optional[str] = Field(None, description="运营商")
    pool_specification: Optional[int] = Field(None, ge=-1, description="流量池规格(MB)")
    order_by: Optional[str] = Field(
        "usage_percent",
        description="排序字段：usage_percent/pool_specification/used_flow/total_flow/remaining_flow/estimated_monthly_used_flow/estimated_month_end_remaining_flow",
    )
    order_dir: Optional[str] = Field("desc", description="排序方向")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class SupplierTrafficPoolAlertUpdate(BaseModel):
    alert_threshold: Optional[int] = Field(None, ge=0, le=100, description="邮件提醒阈值")
    alert_thresholds: Optional[List[int]] = Field(None, description="邮件提醒阈值列表")
    alert_emails: Optional[str] = Field(None, max_length=500, description="提醒邮箱")

    @field_validator("alert_thresholds")
    @classmethod
    def validate_alert_thresholds(cls, value: Optional[List[int]]) -> Optional[List[int]]:
        if value is None:
            return value
        cleaned = sorted({int(item) for item in value if item is not None})
        if any(item < 0 or item > 100 for item in cleaned):
            raise ValueError("提醒阈值必须在0到100之间")
        if len(cleaned) > 5:
            raise ValueError("提醒阈值最多设置5个")
        return cleaned

    @field_validator("alert_emails")
    @classmethod
    def validate_alert_emails(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return value
        emails = [item.strip() for item in value.replace(";", ",").split(",") if item.strip()]
        if len(",".join(emails)) > 500:
            raise ValueError("提醒邮箱过长")
        return ",".join(emails)


class SupplierTrafficPoolSyncRequest(BaseModel):
    supplier_id: Optional[int] = Field(None, description="供应商ID，空表示同步全部启用供应商")
