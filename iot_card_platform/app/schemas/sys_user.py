"""
系统用户模块数据模型
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum as PyEnum


class UserStatus(str, PyEnum):
    """用户状态枚举 - 值必须与数据库 ENUM 一致"""
    enable = "enable"
    disable = "disable"


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    account: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=50)
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")
    email: Optional[str] = Field(None, max_length=100)
    alert_notify: Optional[Dict[str, Any]] = Field(default={"sms": True, "email": True})
    quota: Optional[Dict[str, Any]] = Field(default={
        "max_cards": 100,
        "max_sub_users": 5,
        "pool_stop_threshold": 100,
        "account_balance": 0,
        "balance_alert_threshold": 1000
    })
    remark: Optional[str] = Field(None, max_length=500)
    status: UserStatus = Field(default=UserStatus.enable)

    @field_validator("phone", "email", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        return None if v == "" else v


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")
    email: Optional[str] = Field(None, max_length=100)
    alert_notify: Optional[Dict[str, Any]] = None
    quota: Optional[Dict[str, Any]] = None
    remark: Optional[str] = Field(None, max_length=500)
    status: Optional[UserStatus] = None


class UserH5Config(BaseModel):
    enabled: bool = False
    slug: Optional[str] = None
    title: Optional[str] = None
    logo: Optional[str] = None
    banner: Optional[str] = None
    notice: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_wechat: Optional[str] = None
    theme: Optional[Dict[str, Any]] = None
    allow_suspend: bool = True
    allow_resume: bool = True
    allow_remark: bool = True
    require_verify: bool = False
    status: str = "enabled"
    last_reset_at: Optional[datetime] = None


class UserH5ConfigUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    logo: Optional[str] = Field(None, max_length=255)
    banner: Optional[str] = Field(None, max_length=255)
    notice: Optional[str] = Field(None, max_length=1000)
    contact_phone: Optional[str] = Field(None, max_length=30)
    contact_wechat: Optional[str] = Field(None, max_length=50)
    theme: Optional[Dict[str, Any]] = None
    allow_suspend: Optional[bool] = None
    allow_resume: Optional[bool] = None
    allow_remark: Optional[bool] = None
    require_verify: Optional[bool] = None
    status: Optional[str] = Field(None, pattern=r"^(enabled|disabled|expired)$")


class UserH5StatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(enabled|disabled|expired)$")


class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    parent_id: Optional[int] = None
    user_level: int
    name: str
    account: str
    phone: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    alert_notify: Optional[Dict[str, Any]] = None
    quota: Optional[Dict[str, Any]] = None
    remark: Optional[str] = None
    h5: Optional[UserH5Config] = None
    status: str
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class UserQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    keyword: Optional[str] = None
    status: Optional[UserStatus] = None


class UserPasswordUpdate(BaseModel):
    old_password: str = Field(..., min_length=6, max_length=50)
    new_password: str = Field(..., min_length=6, max_length=50)
    confirm_password: str = Field(..., min_length=6, max_length=50)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("新密码与确认密码不一致")
        return v


class UserPasswordReset(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=50)


class UserBalanceGrantRequest(BaseModel):
    amount: float = Field(..., gt=0, description="分配金额")
    remark: Optional[str] = Field(None, max_length=200, description="备注")
    request_id: Optional[str] = Field(None, max_length=64, description="幂等请求ID")
