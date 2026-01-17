"""
出入库管理模型
包含: 采购批次表、入库记录表、出库记录表
"""
from sqlalchemy import Column, String, Enum, BigInteger, Integer, Date, DateTime, Text
from enum import Enum as PyEnum
from app.db.models.base import BaseModel
from app.db.models.package import CarrierType, PeriodType


class BatchStatus(str, PyEnum):
    """批次状态"""
    pending = "pending"       # 待入库
    stocked = "stocked"       # 已入库
    completed = "completed"   # 已完成(全部出库)


class StockInStatus(str, PyEnum):
    """入库状态"""
    pending = "pending"       # 待确认
    confirmed = "confirmed"   # 已确认


class StockOutStatus(str, PyEnum):
    """出库状态"""
    pending = "pending"       # 待确认
    confirmed = "confirmed"   # 已确认
    cancelled = "cancelled"   # 已取消


BATCH_STATUS_NAMES = {
    "pending": "待入库",
    "stocked": "已入库",
    "completed": "已完成"
}

STOCK_IN_STATUS_NAMES = {
    "pending": "待确认",
    "confirmed": "已确认"
}

STOCK_OUT_STATUS_NAMES = {
    "pending": "待确认",
    "confirmed": "已确认",
    "cancelled": "已取消"
}


class PurchaseBatchModel(BaseModel):
    """采购批次模型"""
    __tablename__ = "purchase_batches"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="批次ID")
    batch_no = Column(String(50), nullable=False, unique=True, comment="批次号")
    supplier_id = Column(BigInteger, nullable=False, index=True, comment="供应商ID")
    package_id = Column(BigInteger, nullable=False, comment="底层套餐ID")
    
    # 规格信息 (冗余)
    carrier = Column(Enum(CarrierType), nullable=False, comment="运营商")
    flow_size = Column(BigInteger, nullable=False, comment="套餐流量(MB)")
    period_type = Column(Enum(PeriodType), nullable=False, comment="周期类型")
    
    # 生命周期配置
    test_expire_date = Column(Date, nullable=True, comment="测试期到期日")
    silent_expire_date = Column(Date, nullable=False, comment="沉默期到期日")
    
    # 数量统计
    card_count = Column(Integer, nullable=False, default=0, comment="卡片总数")
    stocked_count = Column(Integer, nullable=False, default=0, comment="已入库数")
    out_count = Column(Integer, nullable=False, default=0, comment="已出库数")
    
    purchase_date = Column(Date, nullable=False, comment="采购日期")
    remark = Column(String(500), nullable=True, comment="备注")
    status = Column(Enum(BatchStatus), default=BatchStatus.pending, comment="状态")
    created_by = Column(BigInteger, nullable=True, comment="创建人ID")

    def to_dict(self):
        from app.db.models.package import CARRIER_NAMES, PERIOD_CONFIG
        return {
            "id": self.id,
            "batch_no": self.batch_no,
            "supplier_id": self.supplier_id,
            "package_id": self.package_id,
            "carrier": self.carrier.value if self.carrier else None,
            "carrier_name": CARRIER_NAMES.get(self.carrier.value, "") if self.carrier else None,
            "flow_size": self.flow_size,
            "period_type": self.period_type.value if self.period_type else None,
            "period_name": PERIOD_CONFIG.get(self.period_type.value, {}).get("name", "") if self.period_type else None,
            "test_expire_date": self.test_expire_date.strftime("%y/%m/%d") if self.test_expire_date else None,
            "silent_expire_date": self.silent_expire_date.strftime("%y/%m/%d") if self.silent_expire_date else None,
            "card_count": self.card_count,
            "stocked_count": self.stocked_count,
            "out_count": self.out_count,
            "stock_remain": self.stocked_count - self.out_count,
            "purchase_date": self.purchase_date.strftime("%Y-%m-%d") if self.purchase_date else None,
            "remark": self.remark,
            "status": self.status.value if self.status else None,
            "status_name": BATCH_STATUS_NAMES.get(self.status.value, "") if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class StockInRecordModel(BaseModel):
    """入库记录模型"""
    __tablename__ = "stock_in_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    record_no = Column(String(50), nullable=False, unique=True, comment="入库单号")
    batch_id = Column(BigInteger, nullable=False, index=True, comment="批次ID")
    
    card_count = Column(Integer, nullable=False, default=0, comment="入库卡数")
    success_count = Column(Integer, nullable=False, default=0, comment="成功数")
    fail_count = Column(Integer, nullable=False, default=0, comment="失败数")
    
    # 导入的原始数据 (JSON格式: [{iccid, imsi, msisdn}, ...])
    import_data = Column(Text, nullable=True, comment="导入数据JSON")
    fail_reason = Column(Text, nullable=True, comment="失败原因JSON")
    
    remark = Column(String(500), nullable=True, comment="备注")
    status = Column(Enum(StockInStatus), default=StockInStatus.pending, comment="状态")
    confirmed_at = Column(DateTime, nullable=True, comment="确认时间")
    confirmed_by = Column(BigInteger, nullable=True, comment="确认人ID")
    created_by = Column(BigInteger, nullable=True, comment="创建人ID")

    def to_dict(self):
        return {
            "id": self.id,
            "record_no": self.record_no,
            "batch_id": self.batch_id,
            "card_count": self.card_count,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "remark": self.remark,
            "status": self.status.value if self.status else None,
            "status_name": STOCK_IN_STATUS_NAMES.get(self.status.value, "") if self.status else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class StockOutRecordModel(BaseModel):
    """出库记录模型"""
    __tablename__ = "stock_out_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    record_no = Column(String(50), nullable=False, unique=True, comment="出库单号")
    
    to_user_id = Column(BigInteger, nullable=False, index=True, comment="目标用户ID")
    sale_package_id = Column(BigInteger, nullable=False, comment="销售套餐ID")
    
    card_count = Column(Integer, nullable=False, default=0, comment="出库卡数")
    
    # 出库的卡片ID列表 (JSON格式)
    card_ids = Column(Text, nullable=True, comment="卡片ID列表JSON")
    
    remark = Column(String(500), nullable=True, comment="备注")
    status = Column(Enum(StockOutStatus), default=StockOutStatus.pending, comment="状态")
    confirmed_at = Column(DateTime, nullable=True, comment="确认时间")
    confirmed_by = Column(BigInteger, nullable=True, comment="确认人ID")
    created_by = Column(BigInteger, nullable=True, comment="创建人ID")

    def to_dict(self):
        return {
            "id": self.id,
            "record_no": self.record_no,
            "to_user_id": self.to_user_id,
            "sale_package_id": self.sale_package_id,
            "card_count": self.card_count,
            "remark": self.remark,
            "status": self.status.value if self.status else None,
            "status_name": STOCK_OUT_STATUS_NAMES.get(self.status.value, "") if self.status else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
