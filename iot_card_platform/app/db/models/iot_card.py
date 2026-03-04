"""
物联网卡模型
包含: 卡片表、采购批次表、流量池表、划拨记录表
"""
from sqlalchemy import Column, String, Enum, BigInteger, Integer, Date, DateTime, Text, DECIMAL
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from app.db.models.base import BaseModel
from app.db.models.package import CarrierType, PeriodType, CARRIER_NAMES, PERIOD_CONFIG


class CardType(str, PyEnum):
    """卡片类型"""
    single = "single"         # 单卡 (达量停机)
    pool = "pool"             # 流量池卡


class CardStatus(str, PyEnum):
    """卡片状态"""
    stock = "stock"           # 库存 (未出库)
    testing = "testing"       # 测试期
    silent = "silent"         # 沉默期
    activated = "activated"   # 已激活
    expired = "expired"       # 已到期
    suspended = "suspended"   # 已停机
    cancelled = "cancelled"   # 已销卡


class SuspendType(str, PyEnum):
    """停卡类型"""
    none = "none"             # 未停卡
    manual = "manual"         # 手动停卡
    expired = "expired"       # 到期停卡
    pool_exceed = "pool_exceed"   # 流量池超限
    card_exceed = "card_exceed"   # 单卡超量


# 状态显示名称
CARD_TYPE_NAMES = {
    "single": "单卡",
    "pool": "流量池卡"
}

CARD_STATUS_NAMES = {
    "stock": "库存",
    "testing": "测试期",
    "silent": "沉默期",
    "activated": "已激活",
    "expired": "已到期",
    "suspended": "已停机",
    "cancelled": "已销卡"
}

SUSPEND_TYPE_NAMES = {
    "none": "未停卡",
    "manual": "手动停卡",
    "expired": "到期停卡",
    "pool_exceed": "流量池超限停卡",
    "card_exceed": "单卡超量停卡"
}


class IotCardModel(BaseModel):
    """物联网卡模型"""
    __tablename__ = "iot_cards"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="卡片ID")
    
    # 卡片标识
    iccid = Column(String(30), nullable=False, unique=True, index=True, comment="ICCID")
    imsi = Column(String(20), nullable=True, comment="IMSI")
    msisdn = Column(String(20), nullable=True, index=True, comment="号码")
    
    # 归属关系
    user_id = Column(BigInteger, nullable=True, index=True, comment="当前所属用户ID")
    supplier_id = Column(BigInteger, nullable=True, index=True, comment="供应商ID")
    batch_id = Column(BigInteger, nullable=True, index=True, comment="采购批次ID")
    sale_package_id = Column(BigInteger, nullable=True, comment="销售套餐ID")
    sale_price = Column(DECIMAL(10, 2), nullable=True, comment="套餐单价(元/周期) - 出库时记录")
    project_id = Column(BigInteger, nullable=True, index=True, comment="所属项目ID")
    
    # 规格信息 (冗余，方便查询和组池)
    carrier = Column(Enum(CarrierType), nullable=False, comment="运营商")
    flow_size = Column(BigInteger, nullable=False, comment="套餐流量(MB)")
    period_type = Column(Enum(PeriodType), nullable=False, comment="周期类型")
    period_count = Column(Integer, nullable=False, default=1, comment="套餐周期数量: 月包=月数(3/6/12等), 年包=年数(1/2/3等)")
    
    # 卡片类型
    card_type = Column(Enum(CardType), nullable=False, default=CardType.single, comment="卡片类型: single=单卡, pool=流量池卡")
    
    # 生命周期日期 (格式: YYYY-MM-DD, 显示为 26/1/31)
    test_expire_date = Column(Date, nullable=True, comment="测试期到期日")
    silent_expire_date = Column(Date, nullable=True, comment="沉默期到期日")
    activated_at = Column(Date, nullable=True, comment="激活日")
    expired_at = Column(Date, nullable=True, comment="套餐过期日")
    
    # 流量使用 (单位: MB)
    data_used = Column(BigInteger, nullable=False, default=0, comment="已用流量(MB)")
    data_total = Column(BigInteger, nullable=False, comment="总流量(MB)")
    data_used_month = Column(BigInteger, nullable=False, default=0, comment="本月已用流量(MB)")
    data_sync_at = Column(DateTime, nullable=True, comment="流量同步时间")
    
    # 状态
    status = Column(Enum(CardStatus), nullable=False, default=CardStatus.stock, index=True, comment="状态")
    
    # 停卡信息
    suspend_type = Column(Enum(SuspendType), default=SuspendType.none, comment="停卡类型")
    suspend_at = Column(DateTime, nullable=True, comment="停卡时间")
    suspend_reason = Column(String(200), nullable=True, comment="停卡原因")
    
    # 流量池
    pool_id = Column(BigInteger, nullable=True, index=True, comment="所属流量池ID")
    is_pool_member = Column(Integer, default=0, comment="是否加入流量池: 0=否, 1=是")
    
    # 备注
    remark = Column(String(500), nullable=True, comment="备注")
    
    # 出入库时间
    stock_in_at = Column(DateTime, nullable=True, comment="入库时间")
    stock_out_at = Column(DateTime, nullable=True, comment="出库时间")
    stock_out_date = Column(Date, nullable=True, comment="出库日期")
    
    # 创建人
    created_by = Column(BigInteger, nullable=True, comment="创建人ID")

    def get_spec_name(self) -> str:
        """生成规格名称: 移动1G/月"""
        carrier_name = CARRIER_NAMES.get(self.carrier.value, "") if self.carrier else ""
        flow_display = self._format_flow_size()
        period_name = PERIOD_CONFIG.get(self.period_type.value, {}).get("name", "") if self.period_type else ""
        return f"{carrier_name}{flow_display}/{period_name}"

    def _format_flow_size(self) -> str:
        """格式化流量显示: 1024MB -> 1G"""
        if not self.flow_size:
            return "0M"
        if self.flow_size >= 1024:
            gb = self.flow_size / 1024
            if gb == int(gb):
                return f"{int(gb)}G"
            return f"{gb:.1f}G"
        return f"{self.flow_size}M"

    def _format_date(self, date_obj) -> str:
        """格式化日期: 2026-01-31 -> 26/1/31"""
        if not date_obj:
            return None
        return f"{date_obj.year % 100}/{date_obj.month}/{date_obj.day}"

    def get_data_usage_percent(self) -> float:
        """获取流量使用百分比"""
        if not self.data_total or self.data_total == 0:
            return 0
        return round((self.data_used / self.data_total) * 100, 2)

    def to_dict(self):
        return {
            "id": self.id,
            "iccid": self.iccid,
            "imsi": self.imsi,
            "msisdn": self.msisdn,
            "user_id": self.user_id,
            "supplier_id": self.supplier_id,
            "batch_id": self.batch_id,
            "sale_package_id": self.sale_package_id,
            "sale_price": float(self.sale_price) if self.sale_price else None,
            "project_id": self.project_id,
            # 规格信息
            "carrier": self.carrier.value if self.carrier else None,
            "carrier_name": CARRIER_NAMES.get(self.carrier.value, "") if self.carrier else None,
            "flow_size": self.flow_size,
            "flow_size_display": self._format_flow_size(),
            "period_type": self.period_type.value if self.period_type else None,
            "period_count": self.period_count,
            "period_name": PERIOD_CONFIG.get(self.period_type.value, {}).get("name", "") if self.period_type else None,
            "spec_name": self.get_spec_name(),
            # 卡片类型
            "card_type": self.card_type.value if self.card_type else None,
            "card_type_name": CARD_TYPE_NAMES.get(self.card_type.value, "") if self.card_type else None,
            # 生命周期日期
            "test_expire_date": self._format_date(self.test_expire_date),
            "silent_expire_date": self._format_date(self.silent_expire_date),
            "activated_at": self._format_date(self.activated_at),
            "expired_at": self._format_date(self.expired_at),
            # 流量使用
            "data_used": self.data_used,
            "data_total": self.data_total,
            "data_used_month": self.data_used_month,
            "data_remain": self.data_total - self.data_used if self.data_total else 0,
            "data_usage_percent": self.get_data_usage_percent(),
            "data_sync_at": self.data_sync_at.isoformat() if self.data_sync_at else None,
            # 状态
            "status": self.status.value if self.status else None,
            "status_name": CARD_STATUS_NAMES.get(self.status.value, "") if self.status else None,
            # 停卡信息
            "suspend_type": self.suspend_type.value if self.suspend_type else None,
            "suspend_type_name": SUSPEND_TYPE_NAMES.get(self.suspend_type.value, "") if self.suspend_type else None,
            "suspend_at": self.suspend_at.isoformat() if self.suspend_at else None,
            "suspend_reason": self.suspend_reason,
            # 流量池
            "pool_id": self.pool_id,
            "is_pool_member": self.is_pool_member == 1,
            # 备注
            "remark": self.remark,
            # 时间
            "stock_in_at": self.stock_in_at.isoformat() if self.stock_in_at else None,
            "stock_out_at": self.stock_out_at.isoformat() if self.stock_out_at else None,
            "stock_out_date": self._format_date(self.stock_out_date),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CardTransferModel(BaseModel):
    """卡片划拨记录"""
    __tablename__ = "card_transfers"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    card_id = Column(BigInteger, nullable=False, index=True, comment="卡片ID")
    iccid = Column(String(30), nullable=False, comment="ICCID")
    from_user_id = Column(BigInteger, nullable=False, comment="原用户ID")
    to_user_id = Column(BigInteger, nullable=False, comment="目标用户ID")
    operator_id = Column(BigInteger, nullable=False, comment="操作人ID")
    remark = Column(String(200), nullable=True, comment="备注")

    def to_dict(self):
        return {
            "id": self.id,
            "card_id": self.card_id,
            "iccid": self.iccid,
            "from_user_id": self.from_user_id,
            "to_user_id": self.to_user_id,
            "operator_id": self.operator_id,
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }