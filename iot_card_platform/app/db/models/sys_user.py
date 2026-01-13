"""
系统用户模型 - 三级架构
"""
from sqlalchemy import Column, String, Enum, BigInteger, SmallInteger, DateTime, JSON
from enum import Enum as PyEnum
from app.db.models.base import BaseModel


class UserLevel(int, PyEnum):
    SUPER_ADMIN = 1
    USER = 2
    SUB_USER = 3


class UserStatus(str, PyEnum):
    """用户状态枚举 - 值必须与数据库 ENUM 一致"""
    enable = "enable"
    disable = "disable"


class SysUserModel(BaseModel):
    __tablename__ = "sys_users"

    parent_id = Column(BigInteger, nullable=True, index=True, comment="上级用户ID")
    user_level = Column(SmallInteger, nullable=False, default=UserLevel.USER.value, comment="用户层级")
    name = Column(String(50), nullable=False, comment="用户名称")
    account = Column(String(50), unique=True, nullable=False, index=True, comment="用户账户")
    password = Column(String(128), nullable=False, comment="用户密码")
    phone = Column(String(20), nullable=True, index=True, comment="手机号")
    email = Column(String(100), nullable=True, comment="邮箱")
    avatar = Column(String(255), nullable=True, comment="头像URL")
    alert_notify = Column(JSON, nullable=True, comment="告警通知配置")
    quota = Column(JSON, nullable=True, comment="账户配额")
    remark = Column(String(500), nullable=True, comment="备注")
    status = Column(Enum(UserStatus), default=UserStatus.enable, comment="状态")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    last_login_ip = Column(String(50), nullable=True, comment="最后登录IP")
    created_by = Column(BigInteger, nullable=True, comment="创建人ID")

    def is_super_admin(self) -> bool:
        return self.user_level == UserLevel.SUPER_ADMIN.value

    def is_user(self) -> bool:
        return self.user_level == UserLevel.USER.value

    def is_sub_user(self) -> bool:
        return self.user_level == UserLevel.SUB_USER.value
