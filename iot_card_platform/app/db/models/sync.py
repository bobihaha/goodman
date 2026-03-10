"""
数据同步模型
包含: 同步日志表、同步任务表
"""
from sqlalchemy import Column, String, Enum, BigInteger, Integer, DateTime, Text, JSON
from enum import Enum as PyEnum
from app.db.models.base import BaseModel


class SyncType(str, PyEnum):
    """同步类型"""
    usage = "usage"              # 流量用量同步
    lifecycle = "lifecycle"      # 生命周期同步
    status = "status"            # 状态同步
    single_card = "single_card"  # 单卡信息同步


class SyncStatus(str, PyEnum):
    """同步状态"""
    pending = "pending"      # 待执行
    running = "running"      # 执行中
    success = "success"      # 成功
    failed = "failed"        # 失败
    partial = "partial"      # 部分成功


SYNC_TYPE_NAMES = {
    "usage": "流量用量同步",
    "lifecycle": "生命周期同步",
    "status": "状态同步",
    "single_card": "单卡信息同步"
}

SYNC_STATUS_NAMES = {
    "pending": "待执行",
    "running": "执行中",
    "success": "成功",
    "failed": "失败",
    "partial": "部分成功"
}


class SyncLogModel(BaseModel):
    """同步日志模型"""
    __tablename__ = "sync_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="日志ID")
    sync_no = Column(String(50), nullable=False, unique=True, comment="同步单号")
    sync_type = Column(Enum(SyncType), nullable=False, comment="同步类型")

    # 同步范围
    supplier_id = Column(BigInteger, nullable=True, index=True, comment="供应商ID")
    card_id = Column(BigInteger, nullable=True, index=True, comment="卡片ID (单卡同步)")
    iccid = Column(String(30), nullable=True, comment="ICCID (单卡同步)")

    # 同步统计
    total_count = Column(Integer, nullable=False, default=0, comment="总数")
    success_count = Column(Integer, nullable=False, default=0, comment="成功数")
    fail_count = Column(Integer, nullable=False, default=0, comment="失败数")

    # 同步结果
    status = Column(Enum(SyncStatus), default=SyncStatus.pending, comment="状态")
    error_message = Column(Text, nullable=True, comment="错误信息")
    sync_data = Column(JSON, nullable=True, comment="同步数据详情")
    
    # 执行时间
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    finished_at = Column(DateTime, nullable=True, comment="完成时间")
    duration = Column(Integer, nullable=True, comment="耗时(秒)")
    
    # 操作人
    triggered_by = Column(BigInteger, nullable=True, comment="触发人ID")
    trigger_type = Column(String(20), nullable=True, comment="触发方式: manual/auto")

    def to_dict(self):
        return {
            "id": self.id,
            "sync_no": self.sync_no,
            "sync_type": self.sync_type.value if self.sync_type else None,
            "sync_type_name": SYNC_TYPE_NAMES.get(self.sync_type.value, "") if self.sync_type else None,
            "supplier_id": self.supplier_id,
            "card_id": self.card_id,
            "iccid": self.iccid,
            "total_count": self.total_count,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "status": self.status.value if self.status else None,
            "status_name": SYNC_STATUS_NAMES.get(self.status.value, "") if self.status else None,
            "error_message": self.error_message,
            "sync_data": self.sync_data,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration": self.duration,
            "triggered_by": self.triggered_by,
            "trigger_type": self.trigger_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SyncTaskModel(BaseModel):
    """同步任务模型 (定时任务配置)"""
    __tablename__ = "sync_tasks"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="任务ID")
    task_name = Column(String(100), nullable=False, comment="任务名称")
    sync_type = Column(Enum(SyncType), nullable=False, comment="同步类型")

    # 任务配置
    supplier_id = Column(BigInteger, nullable=True, comment="供应商ID (NULL=全部)")
    cron_expression = Column(String(100), nullable=True, comment="Cron表达式")

    # 任务状态
    is_enabled = Column(Integer, nullable=False, default=1, comment="是否启用")
    last_run_at = Column(DateTime, nullable=True, comment="上次运行时间")
    next_run_at = Column(DateTime, nullable=True, comment="下次运行时间")
    last_status = Column(Enum(SyncStatus), nullable=True, comment="上次状态")
    
    remark = Column(String(500), nullable=True, comment="备注")
    created_by = Column(BigInteger, nullable=True, comment="创建人ID")

    def to_dict(self):
        return {
            "id": self.id,
            "task_name": self.task_name,
            "sync_type": self.sync_type.value if self.sync_type else None,
            "sync_type_name": SYNC_TYPE_NAMES.get(self.sync_type.value, "") if self.sync_type else None,
            "supplier_id": self.supplier_id,
            "cron_expression": self.cron_expression,
            "is_enabled": self.is_enabled,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "last_status": self.last_status.value if self.last_status else None,
            "last_status_name": SYNC_STATUS_NAMES.get(self.last_status.value, "") if self.last_status else None,
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }







