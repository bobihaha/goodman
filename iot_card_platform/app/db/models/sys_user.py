"""
系统用户模型 - 三级架构
"""
from sqlalchemy import Column, String, Enum, BigInteger, SmallInteger, DateTime, JSON, Integer
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
    h5_enabled = Column(Integer, nullable=False, default=0, comment="是否启用H5: 0=否, 1=是")
    h5_slug = Column(String(32), nullable=True, unique=True, index=True, comment="H5专属访问标识")
    h5_title = Column(String(100), nullable=True, comment="H5标题")
    h5_logo = Column(String(255), nullable=True, comment="H5 Logo")
    h5_banner = Column(String(255), nullable=True, comment="H5横幅图")
    h5_notice = Column(String(1000), nullable=True, comment="H5公告文案")
    h5_contact_phone = Column(String(30), nullable=True, comment="H5客服电话")
    h5_contact_wechat = Column(String(50), nullable=True, comment="H5客服微信")
    h5_theme = Column(JSON, nullable=True, comment="H5主题配置")
    h5_allow_suspend = Column(Integer, nullable=False, default=1, comment="H5是否允许停机: 0=否, 1=是")
    h5_allow_resume = Column(Integer, nullable=False, default=1, comment="H5是否允许复机: 0=否, 1=是")
    h5_allow_remark = Column(Integer, nullable=False, default=1, comment="H5是否允许备注: 0=否, 1=是")
    h5_require_verify = Column(Integer, nullable=False, default=0, comment="H5是否要求验证码: 0=否, 1=是")
    h5_status = Column(String(20), nullable=True, default="enabled", comment="H5状态: enabled/disabled/expired")
    h5_last_reset_at = Column(DateTime, nullable=True, comment="H5最近重置时间")
    open_api_app_id = Column(String(64), nullable=True, unique=True, index=True, comment="开放API APPID")
    open_api_app_secret = Column(String(255), nullable=True, comment="开放API AppSecret")
    open_api_enabled = Column(Integer, nullable=False, default=0, comment="开放API是否启用: 0=否, 1=是")
    open_api_last_reset_at = Column(DateTime, nullable=True, comment="开放API密钥最近重置时间")
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
