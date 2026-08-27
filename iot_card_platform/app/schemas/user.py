"""
用户模块数据模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from enum import Enum as PyEnum


class UserStatus(str, PyEnum):
    ENABLE = "enable"
    DISABLE = "disable"


class UserCreate(BaseModel):
    """用户注册"""
    username: str = Field(..., min_length=3, max_length=50)
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    email: Optional[str] = None
    password: str = Field(..., min_length=6, max_length=20)
    confirm_password: str
    company: Optional[str] = None

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("密码与确认密码不一致")
        return v


class UserLogin(BaseModel):
    """用户登录"""
    account: str = Field(..., description="登录账号")
    password: str


class UserInfo(BaseModel):
    """用户信息"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    phone: str
    email: Optional[str] = None
    status: UserStatus
    role: str
    company: Optional[str] = None
    created_at: Optional[datetime] = None
