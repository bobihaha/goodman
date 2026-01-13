"""
系统日志模型
"""
from sqlalchemy import Column, String, Enum, BigInteger, SmallInteger, Integer, JSON
from enum import Enum as PyEnum
from app.db.models.base import BaseModel


class LoginType(str, PyEnum):
    NORMAL = "normal"
    SUPER = "super"


class SysLoginLogModel(BaseModel):
    __tablename__ = "sys_login_logs"

    user_id = Column(BigInteger, nullable=True, index=True, comment="用户ID")
    account = Column(String(50), nullable=True, index=True, comment="登录账户")
    login_type = Column(Enum(LoginType), default=LoginType.NORMAL, comment="登录类型")
    operator_id = Column(BigInteger, nullable=True, comment="操作人ID")
    is_success = Column(SmallInteger, default=1, comment="是否成功")
    fail_reason = Column(String(200), nullable=True, comment="失败原因")
    ip = Column(String(50), nullable=True, comment="IP地址")
    user_agent = Column(String(500), nullable=True, comment="User-Agent")
