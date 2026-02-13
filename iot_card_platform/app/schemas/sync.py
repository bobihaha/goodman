"""
数据同步 Pydantic 模型
"""
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class SyncType(str, Enum):
    """同步类型"""
    usage = "usage"
    lifecycle = "lifecycle"
    status = "status"
    single_card = "single_card"


class SyncStatus(str, Enum):
    """同步状态"""
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"
    partial = "partial"


# ============ 同步请求 ============

class UsageSyncRequest(BaseModel):
    """流量用量同步请求"""
    supplier_id: Optional[int] = Field(None, description="供应商ID (NULL=全部)")
    iccid_list: Optional[List[str]] = Field(None, description="指定ICCID列表")


class LifecycleSyncRequest(BaseModel):
    """生命周期同步请求"""
    supplier_id: Optional[int] = Field(None, description="供应商ID (NULL=全部)")
    iccid_list: Optional[List[str]] = Field(None, description="指定ICCID列表")


class SingleCardSyncRequest(BaseModel):
    """单卡信息同步请求"""
    iccid: str = Field(..., description="ICCID")


# ============ 同步日志 ============

class SyncLogInfo(BaseModel):
    """同步日志信息"""
    id: int
    sync_no: str
    sync_type: Optional[str] = None
    sync_type_name: Optional[str] = None
    supplier_id: Optional[int] = None
    card_id: Optional[int] = None
    iccid: Optional[str] = None
    total_count: int = 0
    success_count: int = 0
    fail_count: int = 0
    status: Optional[str] = None
    status_name: Optional[str] = None
    error_message: Optional[str] = None
    sync_data: Optional[Any] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration: Optional[int] = None
    triggered_by: Optional[int] = None
    trigger_type: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class SyncLogQuery(BaseModel):
    """同步日志查询"""
    sync_type: Optional[str] = Field(None, description="同步类型")
    supplier_id: Optional[int] = Field(None, description="供应商ID")
    status: Optional[str] = Field(None, description="状态")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


# ============ 同步任务 ============

class SyncTaskCreate(BaseModel):
    """创建同步任务"""
    task_name: str = Field(..., max_length=100, description="任务名称")
    sync_type: SyncType = Field(..., description="同步类型")
    supplier_id: Optional[int] = Field(None, description="供应商ID")
    cron_expression: Optional[str] = Field(None, max_length=100, description="Cron表达式")
    is_enabled: int = Field(1, description="是否启用")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class SyncTaskUpdate(BaseModel):
    """更新同步任务"""
    task_name: Optional[str] = Field(None, max_length=100, description="任务名称")
    cron_expression: Optional[str] = Field(None, max_length=100, description="Cron表达式")
    is_enabled: Optional[int] = Field(None, description="是否启用")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class SyncTaskInfo(BaseModel):
    """同步任务信息"""
    id: int
    task_name: str
    sync_type: Optional[str] = None
    sync_type_name: Optional[str] = None
    supplier_id: Optional[int] = None
    cron_expression: Optional[str] = None
    is_enabled: int
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    last_status: Optional[str] = None
    last_status_name: Optional[str] = None
    remark: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


# ============ 同步结果 ============

class SyncResult(BaseModel):
    """同步结果"""
    sync_no: str
    sync_type: str
    total: int
    success: int
    failed: int
    status: str
    duration: Optional[int] = None
    error_message: Optional[str] = None







