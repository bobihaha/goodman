"""
仪表盘相关的 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CardStatsItem(BaseModel):
    """卡片状态统计项"""
    status: str
    status_name: str
    count: int


class CardStats(BaseModel):
    """卡片统计"""
    total: int = Field(0, description="总卡片数")
    by_status: List[CardStatsItem] = Field(default_factory=list, description="按状态统计")
    by_carrier: List[dict] = Field(default_factory=list, description="按运营商统计")
    expiring_count: int = Field(0, description="本月到期卡数")
    over_usage_count: int = Field(0, description="超量卡数")


class UserStats(BaseModel):
    """用户统计"""
    total_users: int = Field(0, description="用户总数")
    total_sub_users: int = Field(0, description="子用户总数")
    active_users: int = Field(0, description="活跃用户数")


class PackageStats(BaseModel):
    """套餐统计"""
    supplier_packages: int = Field(0, description="底层套餐数")
    sale_packages: int = Field(0, description="销售套餐数")


class PoolStats(BaseModel):
    """流量池统计"""
    total_pools: int = Field(0, description="流量池总数")
    total_data: int = Field(0, description="总流量(MB)")
    used_data: int = Field(0, description="已用流量(MB)")
    usage_percent: float = Field(0, description="使用率%")


class AlertStats(BaseModel):
    """告警统计"""
    warning: int = Field(0, description="警告数")
    critical: int = Field(0, description="紧急数")
    exceed: int = Field(0, description="超限数")
    unhandled: int = Field(0, description="未处理总数")


class DashboardOverview(BaseModel):
    """仪表盘总览"""
    cards: CardStats
    users: UserStats
    packages: PackageStats
    pools: PoolStats
    alerts: AlertStats


class UsageTrendItem(BaseModel):
    """流量趋势数据项"""
    date: str
    used: int = Field(0, description="使用量(MB)")
    total: int = Field(0, description="总量(MB)")


class UsageTrend(BaseModel):
    """流量趋势"""
    period: str = Field("daily", description="周期: daily/weekly/monthly")
    data: List[UsageTrendItem] = Field(default_factory=list)


class AlertItem(BaseModel):
    """告警项"""
    id: int
    target_type: str
    target_name: str
    alert_level: str
    alert_level_name: str
    usage_percent: int
    created_at: str


class ActivityItem(BaseModel):
    """活动记录项"""
    id: int
    action: str
    action_name: str
    target: str
    operator: Optional[str]
    created_at: str
