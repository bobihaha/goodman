"""
停卡策略相关的 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============ 停卡策略 ============

class PolicyCreate(BaseModel):
    """创建停卡策略"""
    name: str = Field(..., min_length=1, max_length=100, description="策略名称")
    description: Optional[str] = Field(None, max_length=500, description="策略描述")
    policy_type: str = Field(..., description="策略类型: expired/pool_exceed/card_exceed")
    warning_threshold: Optional[int] = Field(80, ge=1, le=100, description="警告阈值%")
    critical_threshold: Optional[int] = Field(90, ge=1, le=100, description="紧急阈值%")
    stop_threshold: Optional[int] = Field(100, ge=1, le=100, description="停卡阈值%")
    user_id: Optional[int] = Field(None, description="指定用户ID")
    pool_id: Optional[int] = Field(None, description="指定流量池ID")
    auto_suspend: bool = Field(True, description="是否自动停卡")
    auto_resume: bool = Field(False, description="是否自动复机")
    notify_warning: bool = Field(True, description="警告时通知")
    notify_critical: bool = Field(True, description="紧急时通知")
    notify_suspend: bool = Field(True, description="停卡时通知")
    is_enabled: bool = Field(True, description="是否启用")


class PolicyUpdate(BaseModel):
    """更新停卡策略"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="策略名称")
    description: Optional[str] = Field(None, max_length=500, description="策略描述")
    warning_threshold: Optional[int] = Field(None, ge=1, le=100, description="警告阈值%")
    critical_threshold: Optional[int] = Field(None, ge=1, le=100, description="紧急阈值%")
    stop_threshold: Optional[int] = Field(None, ge=1, le=100, description="停卡阈值%")
    user_id: Optional[int] = Field(None, description="指定用户ID")
    pool_id: Optional[int] = Field(None, description="指定流量池ID")
    auto_suspend: Optional[bool] = Field(None, description="是否自动停卡")
    auto_resume: Optional[bool] = Field(None, description="是否自动复机")
    notify_warning: Optional[bool] = Field(None, description="警告时通知")
    notify_critical: Optional[bool] = Field(None, description="紧急时通知")
    notify_suspend: Optional[bool] = Field(None, description="停卡时通知")
    is_enabled: Optional[bool] = Field(None, description="是否启用")


class PolicyInfo(BaseModel):
    """策略信息"""
    id: int
    name: str
    description: Optional[str]
    policy_type: str
    warning_threshold: Optional[int]
    critical_threshold: Optional[int]
    stop_threshold: Optional[int]
    user_id: Optional[int]
    pool_id: Optional[int]
    auto_suspend: bool
    auto_resume: bool
    notify_warning: bool
    notify_critical: bool
    notify_suspend: bool
    is_enabled: bool
    created_by: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]


# ============ 手动停卡/复机 ============

class ManualSuspend(BaseModel):
    """手动停卡"""
    card_ids: List[int] = Field(..., min_length=1, description="卡片ID列表")
    reason: Optional[str] = Field(None, max_length=500, description="停卡原因")


class ManualResume(BaseModel):
    """手动复机"""
    card_ids: List[int] = Field(..., min_length=1, description="卡片ID列表")
    reason: Optional[str] = Field(None, max_length=500, description="复机原因")


class SuspendResult(BaseModel):
    """停卡/复机结果"""
    success_count: int
    fail_count: int
    success_cards: List[str]  # ICCID 列表
    fail_cards: List[dict]    # {iccid, reason}


# ============ 停卡记录 ============

class SuspendLogInfo(BaseModel):
    """停卡记录信息"""
    id: int
    card_id: int
    iccid: str
    action: str
    action_name: str
    suspend_type: str
    policy_id: Optional[int]
    pool_id: Optional[int]
    reason: Optional[str]
    api_called: bool
    api_result: Optional[str]
    operator_id: Optional[int]
    created_at: Optional[str]


# ============ 告警记录 ============

class AlertLogInfo(BaseModel):
    """告警记录信息"""
    id: int
    target_type: str
    target_type_name: str
    target_id: int
    target_name: Optional[str]
    alert_level: str
    alert_level_name: str
    usage_percent: int
    threshold: int
    policy_id: Optional[int]
    user_id: Optional[int]
    notified: bool
    notified_at: Optional[str]
    handled: bool
    handled_at: Optional[str]
    handled_by: Optional[int]
    handle_remark: Optional[str]
    created_at: Optional[str]


class AlertHandle(BaseModel):
    """处理告警"""
    handle_remark: Optional[str] = Field(None, max_length=500, description="处理备注")


# ============ 检查用量 ============

class UsageCheckResult(BaseModel):
    """用量检查结果"""
    alerts_created: int       # 新增告警数
    cards_suspended: int      # 停卡数
    pools_exceeded: int       # 超限流量池数
