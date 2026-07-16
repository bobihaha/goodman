"""渠道伙伴与推广积分接口模型。"""
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ChannelLoginRequest(BaseModel):
    account: str = Field(..., min_length=4, max_length=50)
    password: str = Field(..., min_length=8, max_length=50)


class ChannelPartnerCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    contact_name: str = Field(..., min_length=2, max_length=50)
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    account: str = Field(..., min_length=4, max_length=50, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=50)
    stock_out_rate_override: Optional[float] = Field(None, ge=0, le=100)
    renewal_rate_override: Optional[float] = Field(None, ge=0, le=100)
    registration_enabled: bool = True
    remark: Optional[str] = Field(None, max_length=500)


class ChannelPartnerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    contact_name: Optional[str] = Field(None, min_length=2, max_length=50)
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")
    stock_out_rate_override: Optional[float] = Field(None, ge=0, le=100)
    renewal_rate_override: Optional[float] = Field(None, ge=0, le=100)
    registration_enabled: Optional[bool] = None
    status: Optional[str] = Field(None, pattern=r"^(enable|disable)$")
    remark: Optional[str] = Field(None, max_length=500)


class ChannelPasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=50)


class ChannelSettingsUpdate(BaseModel):
    default_stock_out_rate: float = Field(..., ge=0, le=100)
    default_renewal_rate: float = Field(..., ge=0, le=100)


class ChannelCustomerRegisterRequest(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=50)
    customer_phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    customer_profile: str = Field(..., min_length=5, max_length=500)
    consent: bool

    @field_validator("customer_profile")
    @classmethod
    def validate_customer_profile(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 5:
            raise ValueError("请填写设备、使用场景和预计规模")
        return value

    @field_validator("consent")
    @classmethod
    def validate_consent(cls, value: bool) -> bool:
        if not value:
            raise ValueError("请先阅读并同意隐私告知")
        return value


class ChannelPointsSettleRequest(BaseModel):
    point_ids: list[int] = Field(..., min_length=1, max_length=1000)
