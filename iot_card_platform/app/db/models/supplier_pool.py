"""
供应商侧流量池快照模型
"""
from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, JSON, String, Text, UniqueConstraint

from app.db.models.base import BaseModel


class SupplierTrafficPoolModel(BaseModel):
    """供应商侧流量池快照"""
    __tablename__ = "supplier_traffic_pools"
    __table_args__ = (
        UniqueConstraint("supplier_id", "supplier_pool_code", name="uk_supplier_pool_code"),
    )

    supplier_id = Column(BigInteger, nullable=False, index=True, comment="供应商ID")
    supplier_name = Column(String(100), nullable=True, comment="供应商名称快照")
    supplier_pool_code = Column(String(100), nullable=False, comment="供应商流量池编码")
    supplier_pool_name = Column(String(100), nullable=True, comment="供应商流量池名称")
    carrier = Column(String(20), nullable=True, index=True, comment="运营商")
    pool_specification = Column(BigInteger, nullable=True, index=True, comment="流量池规格(MB)")
    total_flow = Column(Float, nullable=False, default=0, comment="总流量(MB)")
    used_flow = Column(Float, nullable=False, default=0, comment="已用流量(MB)")
    remaining_flow = Column(Float, nullable=False, default=0, comment="剩余流量(MB)")
    package_flow = Column(Float, nullable=False, default=0, comment="叠加包量(MB)")
    usage_percent = Column(Float, nullable=False, default=0, index=True, comment="使用率(%)")
    total_card_count = Column(Integer, nullable=False, default=0, comment="总卡数")
    active_card_count = Column(Integer, nullable=False, default=0, comment="激活卡数")
    suspended_card_count = Column(Integer, nullable=False, default=0, comment="停卡卡数")
    stock_card_count = Column(Integer, nullable=False, default=0, comment="库存卡数")
    testing_card_count = Column(Integer, nullable=False, default=0, comment="测试期卡数")
    cancelled_card_count = Column(Integer, nullable=False, default=0, comment="销卡卡数")
    activation_ready_count = Column(Integer, nullable=False, default=0, comment="待激活卡数")
    alert_threshold = Column(Integer, nullable=True, comment="邮件提醒阈值(%)")
    alert_thresholds = Column(String(100), nullable=False, default="60,80,100", comment="邮件提醒阈值列表(%)")
    alert_emails = Column(Text, nullable=True, comment="提醒邮箱，多个用逗号分隔")
    last_alert_at = Column(DateTime, nullable=True, comment="最近提醒时间")
    last_alert_usage_percent = Column(Float, nullable=True, comment="最近提醒使用率")
    last_alert_threshold = Column(Integer, nullable=True, comment="最近提醒阈值(%)")
    last_sync_at = Column(DateTime, nullable=True, comment="最近同步时间")
    sync_status = Column(String(20), nullable=False, default="success", comment="同步状态")
    sync_error = Column(String(500), nullable=True, comment="同步错误")
    raw_data = Column(JSON, nullable=True, comment="供应商原始数据")

    def to_dict(self):
        return {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "supplier_pool_code": self.supplier_pool_code,
            "supplier_pool_name": self.supplier_pool_name,
            "carrier": self.carrier,
            "pool_specification": self.pool_specification,
            "total_flow": self.total_flow,
            "used_flow": self.used_flow,
            "remaining_flow": self.remaining_flow,
            "package_flow": self.package_flow,
            "usage_percent": self.usage_percent,
            "total_card_count": self.total_card_count,
            "active_card_count": self.active_card_count,
            "suspended_card_count": self.suspended_card_count,
            "stock_card_count": self.stock_card_count,
            "testing_card_count": self.testing_card_count,
            "cancelled_card_count": self.cancelled_card_count,
            "activation_ready_count": self.activation_ready_count,
            "alert_threshold": self.alert_threshold,
            "alert_thresholds": self.alert_thresholds,
            "alert_emails": self.alert_emails,
            "last_alert_at": self.last_alert_at.isoformat() if self.last_alert_at else None,
            "last_alert_usage_percent": self.last_alert_usage_percent,
            "last_alert_threshold": self.last_alert_threshold,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "sync_status": self.sync_status,
            "sync_error": self.sync_error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SupplierTrafficPoolHistoryModel(BaseModel):
    """供应商侧流量池月度历史快照"""
    __tablename__ = "supplier_traffic_pool_histories"
    __table_args__ = (
        UniqueConstraint("supplier_pool_id", "record_month", name="uk_supplier_pool_month"),
    )

    supplier_pool_id = Column(BigInteger, nullable=False, index=True, comment="供应商流量池快照ID")
    supplier_id = Column(BigInteger, nullable=False, index=True, comment="供应商ID")
    supplier_name = Column(String(100), nullable=True, comment="供应商名称快照")
    supplier_pool_code = Column(String(100), nullable=False, comment="供应商流量池编码")
    supplier_pool_name = Column(String(100), nullable=True, comment="供应商流量池名称")
    record_month = Column(String(7), nullable=False, index=True, comment="记录月份 YYYY-MM")
    carrier = Column(String(20), nullable=True, comment="运营商")
    pool_specification = Column(BigInteger, nullable=True, comment="流量池规格(MB)")
    total_flow = Column(Float, nullable=False, default=0, comment="总流量(MB)")
    used_flow = Column(Float, nullable=False, default=0, comment="已用流量(MB)")
    remaining_flow = Column(Float, nullable=False, default=0, comment="剩余流量(MB)")
    package_flow = Column(Float, nullable=False, default=0, comment="叠加包量(MB)")
    usage_percent = Column(Float, nullable=False, default=0, comment="使用率(%)")
    total_card_count = Column(Integer, nullable=False, default=0, comment="总卡数")
    active_card_count = Column(Integer, nullable=False, default=0, comment="激活卡数")
    sync_at = Column(DateTime, nullable=True, comment="本月快照同步时间")

    def to_dict(self):
        return {
            "id": self.id,
            "supplier_pool_id": self.supplier_pool_id,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "supplier_pool_code": self.supplier_pool_code,
            "supplier_pool_name": self.supplier_pool_name,
            "record_month": self.record_month,
            "carrier": self.carrier,
            "pool_specification": self.pool_specification,
            "total_flow": self.total_flow,
            "used_flow": self.used_flow,
            "remaining_flow": self.remaining_flow,
            "package_flow": self.package_flow,
            "usage_percent": self.usage_percent,
            "total_card_count": self.total_card_count,
            "active_card_count": self.active_card_count,
            "sync_at": self.sync_at.isoformat() if self.sync_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
