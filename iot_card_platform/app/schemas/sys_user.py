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
    quota: Optional[Dict[str, Any]] = Field(default={"max_cards": 100, "max_sub_users": 5, "pool_stop_threshold": 100})
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
