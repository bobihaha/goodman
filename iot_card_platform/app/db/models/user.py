"""
用户表模型
"""
from sqlalchemy import Column, String, Enum
from enum import Enum as PyEnum

from app.db.models.base import BaseModel


class UserStatus(str, PyEnum):
    ENABLE = "enable"
    DISABLE = "disable"


class UserModel(BaseModel):
    """用户表"""
    __tablename__ = "users"

    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    phone = Column(String(11), unique=True, index=True, nullable=False, comment="手机号")
    email = Column(String(100), unique=True, index=True, nullable=True, comment="邮箱")
    password = Column(String(100), nullable=False, comment="加密密码")
    status = Column(Enum(UserStatus), default=UserStatus.ENABLE, comment="用户状态")
    role = Column(String(20), default="user", comment="角色：admin/operator/user")
    company = Column(String(100), nullable=True, comment="所属企业")
