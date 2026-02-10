"""
系统设置相关的 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class NotifyTypeEnum(str, Enum):
    """通知类型枚举"""
    sms = "sms"
    email = "email"
    wechat = "wechat"
    webhook = "webhook"


# ============ 系统配置 ============

class ConfigCreate(BaseModel):
    """创建配置"""
    config_key: str = Field(..., min_length=1, max_length=100, description="配置键")
    config_value: Optional[str] = Field(None, description="配置值")
    config_type: str = Field("string", description="配置类型: string/number/json/boolean")
    description: Optional[str] = Field(None, max_length=200, description="配置描述")
    is_public: bool = Field(False, description="是否公开")


class ConfigUpdate(BaseModel):
    """更新配置"""
    config_value: Optional[str] = Field(None, description="配置值")
    description: Optional[str] = Field(None, max_length=200, description="配置描述")
    is_public: Optional[bool] = Field(None, description="是否公开")


class ConfigBatchUpdate(BaseModel):
    """批量更新配置"""
    configs: List[dict] = Field(..., description="配置列表 [{key: value}, ...]")


class ConfigInfo(BaseModel):
    """配置信息"""
    id: int
    config_key: str
    config_value: Optional[str]
    config_type: str
    description: Optional[str]
    is_public: bool
    created_at: Optional[str]
    updated_at: Optional[str]


# ============ 登录日志 ============

class LoginLogInfo(BaseModel):
    """登录日志信息"""
    id: int
    user_id: Optional[int]
    account: Optional[str]
    login_type: Optional[str]
    login_type_name: Optional[str]
    operator_id: Optional[int]
    is_success: bool
    fail_reason: Optional[str]
    ip: Optional[str]
    user_agent: Optional[str]
    created_at: Optional[str]


# ============ 操作日志 ============

class OperationLogInfo(BaseModel):
    """操作日志信息"""
    id: int
    user_id: Optional[int]
    user_name: Optional[str]
    module: str
    action: str
    target_type: Optional[str]
    target_id: Optional[int]
    target_name: Optional[str]
    detail: Optional[str]
    ip: Optional[str]
    is_success: bool
    error_msg: Optional[str]
    created_at: Optional[str]


# ============ 告警规则 ============

class AlertRules(BaseModel):
    """告警规则配置"""
    warning_threshold: int = Field(80, ge=0, le=100, description="警告阈值百分比")
    critical_threshold: int = Field(90, ge=0, le=100, description="紧急阈值百分比")
    stop_threshold: int = Field(100, ge=0, le=100, description="停卡阈值百分比")
    expired_days: int = Field(7, ge=1, le=30, description="到期预警天数")
    auto_suspend: bool = Field(True, description="超限自动停卡")
    auto_notify: bool = Field(True, description="告警自动通知")


class AlertRulesUpdate(BaseModel):
    """更新告警规则"""
    warning_threshold: Optional[int] = Field(None, ge=0, le=100, description="警告阈值百分比")
    critical_threshold: Optional[int] = Field(None, ge=0, le=100, description="紧急阈值百分比")
    stop_threshold: Optional[int] = Field(None, ge=0, le=100, description="停卡阈值百分比")
    expired_days: Optional[int] = Field(None, ge=1, le=30, description="到期预警天数")
    auto_suspend: Optional[bool] = Field(None, description="超限自动停卡")
    auto_notify: Optional[bool] = Field(None, description="告警自动通知")


# ============ 通知模板 ============

class NotifyTemplateCreate(BaseModel):
    """创建通知模板"""
    code: str = Field(..., min_length=1, max_length=50, description="模板编码")
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    type: NotifyTypeEnum = Field(NotifyTypeEnum.sms, description="通知类型")
    title: Optional[str] = Field(None, max_length=200, description="标题模板")
    content: str = Field(..., min_length=1, description="内容模板")
    variables: Optional[List[str]] = Field(None, description="可用变量列表")
    is_enabled: bool = Field(True, description="是否启用")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class NotifyTemplateUpdate(BaseModel):
    """更新通知模板"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模板名称")
    title: Optional[str] = Field(None, max_length=200, description="标题模板")
    content: Optional[str] = Field(None, min_length=1, description="内容模板")
    variables: Optional[List[str]] = Field(None, description="可用变量列表")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class NotifyTemplateInfo(BaseModel):
    """通知模板信息"""
    id: int
    code: str
    name: str
    type: str
    type_name: str
    title: Optional[str]
    content: str
    variables: List[str]
    is_enabled: bool
    remark: Optional[str]
    created_by: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
