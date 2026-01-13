"""
认证模块数据模型
"""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum as PyEnum


class UserLevel(int, PyEnum):
    SUPER_ADMIN = 1
    USER = 2
    SUB_USER = 3


class LoginRequest(BaseModel):
    account: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=50)


class CurrentUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    parent_id: Optional[int] = None
    user_level: int
    name: str
    account: str
    phone: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    status: str
    permissions: List[str] = Field(default_factory=list)
    is_super_login: bool = False
    original_user_id: Optional[int] = None

    def is_super_admin(self) -> bool:
        return self.user_level == UserLevel.SUPER_ADMIN.value

    def is_user(self) -> bool:
        return self.user_level == UserLevel.USER.value
    
    def is_sub_user(self) -> bool:
        return self.user_level == UserLevel.SUB_USER.value


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: CurrentUser


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class SuperLoginRequest(BaseModel):
    target_user_id: int
