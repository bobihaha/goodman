"""
系统日志模型
"""
from sqlalchemy import Column, String, Enum, BigInteger, SmallInteger, Integer, JSON, Text
from enum import Enum as PyEnum
from app.db.models.base import BaseModel


class LoginType(str, PyEnum):
    """登录类型"""
    normal = "normal"
    super_ = "super"


class NotifyType(str, PyEnum):
    """通知类型"""
    sms = "sms"
    email = "email"
    wechat = "wechat"
    webhook = "webhook"


LOGIN_TYPE_NAMES = {
    "normal": "普通登录",
    "super_": "超级登录"
}


NOTIFY_TYPE_NAMES = {
    "sms": "短信",
    "email": "邮件",
    "wechat": "微信",
    "webhook": "Webhook"
}


class SysLoginLogModel(BaseModel):
    """登录日志"""
    __tablename__ = "sys_login_logs"

    user_id = Column(BigInteger, nullable=True, index=True, comment="用户ID")
    account = Column(String(50), nullable=True, index=True, comment="登录账户")
    login_type = Column(Enum(LoginType), default=LoginType.normal, comment="登录类型")
    operator_id = Column(BigInteger, nullable=True, comment="操作人ID")
    is_success = Column(SmallInteger, default=1, comment="是否成功")
    fail_reason = Column(String(200), nullable=True, comment="失败原因")
    ip = Column(String(50), nullable=True, comment="IP地址")
    user_agent = Column(String(500), nullable=True, comment="User-Agent")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "account": self.account,
            "login_type": self.login_type.value if self.login_type else None,
            "login_type_name": LOGIN_TYPE_NAMES.get(self.login_type.value, "") if self.login_type else "",
            "operator_id": self.operator_id,
            "is_success": self.is_success == 1,
            "fail_reason": self.fail_reason,
            "ip": self.ip,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SysOperationLogModel(BaseModel):
    """操作日志"""
    __tablename__ = "sys_operation_logs"

    user_id = Column(BigInteger, nullable=True, index=True, comment="用户ID")
    user_name = Column(String(50), nullable=True, comment="用户名称")
    module = Column(String(50), nullable=False, comment="操作模块")
    action = Column(String(50), nullable=False, comment="操作动作")
    target_type = Column(String(50), nullable=True, comment="目标类型")
    target_id = Column(BigInteger, nullable=True, comment="目标ID")
    target_name = Column(String(100), nullable=True, comment="目标名称")
    detail = Column(Text, nullable=True, comment="操作详情JSON")
    ip = Column(String(50), nullable=True, comment="IP地址")
    is_success = Column(SmallInteger, default=1, comment="是否成功")
    error_msg = Column(String(500), nullable=True, comment="错误信息")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "module": self.module,
            "action": self.action,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "detail": self.detail,
            "ip": self.ip,
            "is_success": self.is_success == 1,
            "error_msg": self.error_msg,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SysConfigModel(BaseModel):
    """系统配置"""
    __tablename__ = "sys_configs"

    config_key = Column(String(100), nullable=False, unique=True, index=True, comment="配置键")
    config_value = Column(Text, nullable=True, comment="配置值")
    config_type = Column(String(20), nullable=False, default="string", comment="配置类型: string/number/json/boolean")
    description = Column(String(200), nullable=True, comment="配置描述")
    is_public = Column(SmallInteger, default=0, comment="是否公开: 0=否, 1=是")

    def to_dict(self):
        return {
            "id": self.id,
            "config_key": self.config_key,
            "config_value": self.config_value,
            "config_type": self.config_type,
            "description": self.description,
            "is_public": self.is_public == 1,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_value(self):
        """获取转换后的配置值"""
        if self.config_type == "number":
            try:
                return float(self.config_value) if '.' in str(self.config_value) else int(self.config_value)
            except:
                return 0
        elif self.config_type == "boolean":
            return self.config_value.lower() in ("true", "1", "yes")
        elif self.config_type == "json":
            import json
            try:
                return json.loads(self.config_value)
            except:
                return {}
        return self.config_value


class SysNotifyTemplateModel(BaseModel):
    """通知模板"""
    __tablename__ = "sys_notify_templates"

    code = Column(String(50), nullable=False, unique=True, index=True, comment="模板编码")
    name = Column(String(100), nullable=False, comment="模板名称")
    type = Column(Enum(NotifyType), nullable=False, default=NotifyType.sms, comment="通知类型")
    title = Column(String(200), nullable=True, comment="标题模板")
    content = Column(Text, nullable=False, comment="内容模板")
    variables = Column(JSON, nullable=True, comment="可用变量列表")
    is_enabled = Column(SmallInteger, default=1, comment="是否启用")
    remark = Column(String(500), nullable=True, comment="备注")
    created_by = Column(BigInteger, nullable=True, comment="创建人ID")

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "type": self.type.value if self.type else None,
            "type_name": NOTIFY_TYPE_NAMES.get(self.type.value, "") if self.type else "",
            "title": self.title,
            "content": self.content,
            "variables": self.variables if isinstance(self.variables, list) else json.loads(self.variables) if self.variables else [],
            "is_enabled": self.is_enabled == 1,
            "remark": self.remark,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
