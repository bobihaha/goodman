"""
超级登录日志模型
"""
from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.sql import func
from app.db.models.base import BaseModel


class SuperLoginLogModel(BaseModel):
    """超级登录日志表"""
    __tablename__ = "sys_super_login_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    original_user_id = Column(BigInteger, nullable=False, index=True, comment="原用户ID")
    target_user_id = Column(BigInteger, nullable=False, index=True, comment="目标用户ID")
    login_at = Column(DateTime, nullable=False, index=True, comment="登录时间")
    logout_at = Column(DateTime, nullable=True, comment="退出时间")
    ip = Column(String(50), nullable=True, comment="IP地址")
    user_agent = Column(String(500), nullable=True, comment="浏览器信息")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "original_user_id": self.original_user_id,
            "target_user_id": self.target_user_id,
            "login_at": self.login_at.isoformat() if self.login_at else None,
            "logout_at": self.logout_at.isoformat() if self.logout_at else None,
            "ip": self.ip,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


