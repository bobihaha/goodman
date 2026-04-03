"""
停卡策略模型
包含: 停卡策略表、停卡记录表、告警记录表、供应商停复机操作表
"""
from sqlalchemy import Column, String, Enum, BigInteger, Integer, DateTime, Text
from enum import Enum as PyEnum
from app.db.models.base import BaseModel


class SuspendActionType(str, PyEnum):
    """停卡操作类型"""
    suspend = "suspend"       # 停卡
    resume = "resume"         # 复机


class AlertLevel(str, PyEnum):
    """告警级别"""
    warning = "warning"       # 警告 (80%)
    critical = "critical"     # 紧急 (90%)
    exceed = "exceed"         # 超限 (100%)


class AlertTargetType(str, PyEnum):
    """告警目标类型"""
    card = "card"             # 单卡
    pool = "pool"             # 流量池


# 显示名称
SUSPEND_ACTION_NAMES = {
    "suspend": "停卡",
    "resume": "复机"
}

ALERT_LEVEL_NAMES = {
    "warning": "警告",
    "critical": "紧急",
    "exceed": "超限"
}

ALERT_LEVEL_THRESHOLDS = {
    "warning": 80,
    "critical": 90,
    "exceed": 100
}

ALERT_TARGET_NAMES = {
    "card": "单卡",
    "pool": "流量池"
}


class SuspendPolicyModel(BaseModel):
    """停卡策略模型"""
    __tablename__ = "suspend_policies"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="策略ID")
    
    # 基本信息
    name = Column(String(100), nullable=False, comment="策略名称")
    description = Column(String(500), nullable=True, comment="策略描述")
    
    # 策略类型 (对应 SuspendType: expired/pool_exceed/card_exceed)
    policy_type = Column(String(20), nullable=False, comment="策略类型: expired/pool_exceed/card_exceed")
    
    # 阈值设置 (百分比，仅 pool_exceed/card_exceed 使用)
    warning_threshold = Column(Integer, nullable=True, default=80, comment="警告阈值%")
    critical_threshold = Column(Integer, nullable=True, default=90, comment="紧急阈值%")
    stop_threshold = Column(Integer, nullable=True, default=100, comment="停卡阈值%")
    
    # 作用范围
    user_id = Column(BigInteger, nullable=True, index=True, comment="指定用户ID(NULL=全局)")
    pool_id = Column(BigInteger, nullable=True, index=True, comment="指定流量池ID(NULL=全部)")
    
    # 自动执行
    auto_suspend = Column(Integer, nullable=False, default=1, comment="是否自动停卡: 0=否, 1=是")
    auto_resume = Column(Integer, nullable=False, default=0, comment="是否自动复机: 0=否, 1=是")
    
    # 通知设置
    notify_warning = Column(Integer, nullable=False, default=1, comment="警告时通知: 0=否, 1=是")
    notify_critical = Column(Integer, nullable=False, default=1, comment="紧急时通知: 0=否, 1=是")
    notify_suspend = Column(Integer, nullable=False, default=1, comment="停卡时通知: 0=否, 1=是")
    
    # 状态
    is_enabled = Column(Integer, nullable=False, default=1, comment="是否启用: 0=否, 1=是")
    
    # 创建人
    created_by = Column(BigInteger, nullable=True, comment="创建人ID")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "policy_type": self.policy_type,
            "warning_threshold": self.warning_threshold,
            "critical_threshold": self.critical_threshold,
            "stop_threshold": self.stop_threshold,
            "user_id": self.user_id,
            "pool_id": self.pool_id,
            "auto_suspend": self.auto_suspend == 1,
            "auto_resume": self.auto_resume == 1,
            "notify_warning": self.notify_warning == 1,
            "notify_critical": self.notify_critical == 1,
            "notify_suspend": self.notify_suspend == 1,
            "is_enabled": self.is_enabled == 1,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SuspendLogModel(BaseModel):
    """停卡/复机记录"""
    __tablename__ = "suspend_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    
    # 操作目标
    card_id = Column(BigInteger, nullable=False, index=True, comment="卡片ID")
    iccid = Column(String(30), nullable=False, comment="ICCID")
    
    # 操作信息
    action = Column(Enum(SuspendActionType), nullable=False, comment="操作: suspend/resume")
    suspend_type = Column(String(20), nullable=False, comment="停卡类型: manual/expired/pool_exceed/card_exceed")
    
    # 关联
    policy_id = Column(BigInteger, nullable=True, comment="触发策略ID(手动操作为NULL)")
    pool_id = Column(BigInteger, nullable=True, comment="关联流量池ID")
    
    # 详情
    reason = Column(String(500), nullable=True, comment="原因说明")
    
    # 供应商API调用
    api_called = Column(Integer, nullable=False, default=0, comment="是否调用供应商API: 0=否, 1=是")
    api_result = Column(Text, nullable=True, comment="API调用结果")
    
    # 操作人
    operator_id = Column(BigInteger, nullable=True, comment="操作人ID(自动操作为NULL)")
    
    def to_dict(self):
        return {
            "id": self.id,
            "card_id": self.card_id,
            "iccid": self.iccid,
            "action": self.action.value if self.action else None,
            "action_name": SUSPEND_ACTION_NAMES.get(self.action.value, "") if self.action else None,
            "suspend_type": self.suspend_type,
            "policy_id": self.policy_id,
            "pool_id": self.pool_id,
            "reason": self.reason,
            "api_called": self.api_called == 1,
            "api_result": self.api_result,
            "operator_id": self.operator_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SupplierSuspendOperationModel(BaseModel):
    """供应商停复机操作记录"""
    __tablename__ = "supplier_suspend_operations"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    card_id = Column(BigInteger, nullable=False, index=True, comment="卡片ID")
    supplier_id = Column(BigInteger, nullable=True, index=True, comment="供应商ID")
    iccid = Column(String(30), nullable=False, index=True, comment="ICCID")
    msisdn = Column(String(20), nullable=True, comment="号码")
    action = Column(Enum(SuspendActionType), nullable=False, comment="操作: suspend/resume")
    callback_no = Column(String(64), nullable=False, unique=True, index=True, comment="供应商回调单号")
    request_payload = Column(Text, nullable=True, comment="请求报文")
    request_result = Column(Text, nullable=True, comment="请求结果")
    callback_payload = Column(Text, nullable=True, comment="回调报文")
    callback_code = Column(String(32), nullable=True, comment="回调状态码")
    callback_msg = Column(String(255), nullable=True, comment="回调消息")
    account_status = Column(String(32), nullable=True, comment="供应商回调卡状态")
    callback_status = Column(String(20), nullable=False, default="pending", comment="回调状态: pending/success/failed")
    operator_id = Column(BigInteger, nullable=True, comment="操作人ID")
    completed_at = Column(DateTime, nullable=True, comment="回调完成时间")

    def to_dict(self):
        return {
            "id": self.id,
            "card_id": self.card_id,
            "supplier_id": self.supplier_id,
            "iccid": self.iccid,
            "msisdn": self.msisdn,
            "action": self.action.value if self.action else None,
            "callback_no": self.callback_no,
            "request_payload": self.request_payload,
            "request_result": self.request_result,
            "callback_payload": self.callback_payload,
            "callback_code": self.callback_code,
            "callback_msg": self.callback_msg,
            "account_status": self.account_status,
            "callback_status": self.callback_status,
            "operator_id": self.operator_id,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AlertLogModel(BaseModel):
    """告警记录"""
    __tablename__ = "alert_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    
    # 告警目标
    target_type = Column(Enum(AlertTargetType), nullable=False, comment="目标类型: card/pool")
    target_id = Column(BigInteger, nullable=False, index=True, comment="目标ID(卡片ID或流量池ID)")
    target_name = Column(String(100), nullable=True, comment="目标名称/ICCID")

    # 告警信息
    alert_level = Column(Enum(AlertLevel), nullable=False, comment="告警级别")
    usage_percent = Column(Integer, nullable=False, comment="当前用量百分比")
    threshold = Column(Integer, nullable=False, comment="触发阈值")
    
    # 关联
    policy_id = Column(BigInteger, nullable=True, comment="触发策略ID")
    user_id = Column(BigInteger, nullable=True, index=True, comment="所属用户ID")
    
    # 通知
    notified = Column(Integer, nullable=False, default=0, comment="是否已通知: 0=否, 1=是")
    notified_at = Column(DateTime, nullable=True, comment="通知时间")
    
    # 处理
    handled = Column(Integer, nullable=False, default=0, comment="是否已处理: 0=否, 1=是")
    handled_at = Column(DateTime, nullable=True, comment="处理时间")
    handled_by = Column(BigInteger, nullable=True, comment="处理人ID")
    handle_remark = Column(String(500), nullable=True, comment="处理备注")

    def to_dict(self):
        return {
            "id": self.id,
            "target_type": self.target_type.value if self.target_type else None,
            "target_type_name": ALERT_TARGET_NAMES.get(self.target_type.value, "") if self.target_type else None,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "alert_level": self.alert_level.value if self.alert_level else None,
            "alert_level_name": ALERT_LEVEL_NAMES.get(self.alert_level.value, "") if self.alert_level else None,
            "usage_percent": self.usage_percent,
            "threshold": self.threshold,
            "policy_id": self.policy_id,
            "user_id": self.user_id,
            "notified": self.notified == 1,
            "notified_at": self.notified_at.isoformat() if self.notified_at else None,
            "handled": self.handled == 1,
            "handled_at": self.handled_at.isoformat() if self.handled_at else None,
            "handled_by": self.handled_by,
            "handle_remark": self.handle_remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
