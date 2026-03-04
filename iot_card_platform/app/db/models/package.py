"""
套餐模型
规格三要素: 运营商 + 流量 + 周期类型
"""
from sqlalchemy import Column, String, Enum, BigInteger, Integer, DECIMAL
from enum import Enum as PyEnum
from app.db.models.base import BaseModel


class CarrierType(str, PyEnum):
    """运营商类型"""
    cmcc = "cmcc"   # 中国移动
    cucc = "cucc"   # 中国联通
    ctcc = "ctcc"   # 中国电信


class PeriodType(str, PyEnum):
    """周期类型"""
    monthly = "monthly"   # 月包
    yearly = "yearly"     # 年包


class PackageStatus(str, PyEnum):
    """套餐状态"""
    enable = "enable"
    disable = "disable"


# 运营商显示名称
CARRIER_NAMES = {
    "cmcc": "移动",
    "cucc": "联通",
    "ctcc": "电信"
}

# 周期类型显示名称和默认有效天数
PERIOD_CONFIG = {
    "monthly": {"name": "月", "default_days": 30},
    "yearly": {"name": "年", "default_days": 360}  # 年包360天
}


class SupplierPackageModel(BaseModel):
    """
    底层套餐模型 (供应商套餐)
    定义套餐规格：运营商 + 流量 + 周期类型
    """
    __tablename__ = "supplier_packages"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="套餐ID")
    supplier_id = Column(BigInteger, nullable=False, index=True, comment="供应商ID")
    name = Column(String(100), nullable=False, comment="套餐名称")
    code = Column(String(50), nullable=False, unique=True, comment="套餐编码")
    
    # 规格三要素
    carrier = Column(Enum(CarrierType), nullable=False, comment="运营商")
    flow_size = Column(BigInteger, nullable=False, comment="流量大小(MB)")
    period_type = Column(Enum(PeriodType), default=PeriodType.monthly, comment="周期类型: 月包/年包")
    
    # 有效期配置
    effective_days = Column(Integer, nullable=True, comment="[已废弃]激活后有效天数")
    period_months = Column(Integer, nullable=True, comment="套餐周期(月) - 月包使用")
    period_days = Column(Integer, nullable=True, comment="套餐周期(天) - 年包使用")
    
    # 价格
    price_cost = Column(DECIMAL(10, 2), nullable=False, comment="成本价(元)")
    
    remark = Column(String(500), nullable=True, comment="备注")
    status = Column(Enum(PackageStatus), default=PackageStatus.enable, comment="状态")
    created_by = Column(BigInteger, nullable=True, comment="创建人ID")

    def get_spec_name(self) -> str:
        """
        生成规格名称: 移动1G/月, 联通5G/年
        """
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

    def to_dict(self):
        return {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "name": self.name,
            "code": self.code,
            "carrier": self.carrier.value if self.carrier else None,
            "carrier_name": CARRIER_NAMES.get(self.carrier.value, "") if self.carrier else None,
            "flow_size": self.flow_size,
            "flow_size_display": self._format_flow_size(),
            "period_type": self.period_type.value if self.period_type else None,
            "period_name": PERIOD_CONFIG.get(self.period_type.value, {}).get("name", "") if self.period_type else None,
            "effective_days": self.effective_days,
            "period_months": self.period_months,
            "period_days": self.period_days,
            "spec_name": self.get_spec_name(),
            "price_cost": float(self.price_cost) if self.price_cost else 0,
            "remark": self.remark,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SalePackageModel(BaseModel):
    """
    销售套餐模型
    继承底层套餐规格，添加销售价格
    """
    __tablename__ = "sale_packages"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="套餐ID")
    user_id = Column(BigInteger, nullable=True, index=True, comment="所属用户ID(NULL=平台套餐)")
    base_package_id = Column(BigInteger, nullable=True, index=True, comment="关联底层套餐ID")
    name = Column(String(100), nullable=False, comment="套餐名称")
    code = Column(String(50), nullable=False, unique=True, comment="套餐编码")
    
    # 规格三要素
    carrier = Column(Enum(CarrierType), nullable=False, comment="运营商")
    flow_size = Column(BigInteger, nullable=False, comment="流量大小(MB)")
    period_type = Column(Enum(PeriodType), default=PeriodType.monthly, comment="周期类型")
    
    # 有效期配置
    effective_days = Column(Integer, nullable=True, comment="[已废弃]激活后有效天数")
    period_months = Column(Integer, nullable=True, comment="套餐周期(月) - 月包使用")
    period_days = Column(Integer, nullable=True, comment="套餐周期(天) - 年包使用")
    
    # 价格
    price_cost = Column(DECIMAL(10, 2), nullable=False, comment="成本价(元)")
    price_sale = Column(DECIMAL(10, 2), nullable=False, comment="销售价(元)")
    
    # 展示配置
    is_public = Column(Integer, default=0, comment="是否公开(子用户可见)")
    sort_order = Column(Integer, default=0, comment="排序")
    
    remark = Column(String(500), nullable=True, comment="备注")
    status = Column(Enum(PackageStatus), default=PackageStatus.enable, comment="状态")
    created_by = Column(BigInteger, nullable=True, comment="创建人ID")

    def get_spec_name(self) -> str:
        """生成规格名称"""
        carrier_name = CARRIER_NAMES.get(self.carrier.value, "") if self.carrier else ""
        flow_display = self._format_flow_size()
        period_name = PERIOD_CONFIG.get(self.period_type.value, {}).get("name", "") if self.period_type else ""
        return f"{carrier_name}{flow_display}/{period_name}"

    def _format_flow_size(self) -> str:
        """格式化流量显示"""
        if not self.flow_size:
            return "0M"
        if self.flow_size >= 1024:
            gb = self.flow_size / 1024
            if gb == int(gb):
                return f"{int(gb)}G"
            return f"{gb:.1f}G"
        return f"{self.flow_size}M"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "base_package_id": self.base_package_id,
            "name": self.name,
            "code": self.code,
            "carrier": self.carrier.value if self.carrier else None,
            "carrier_name": CARRIER_NAMES.get(self.carrier.value, "") if self.carrier else None,
            "flow_size": self.flow_size,
            "flow_size_display": self._format_flow_size(),
            "period_type": self.period_type.value if self.period_type else None,
            "period_name": PERIOD_CONFIG.get(self.period_type.value, {}).get("name", "") if self.period_type else None,
            "effective_days": self.effective_days,
            "period_months": self.period_months,
            "period_days": self.period_days,
            "spec_name": self.get_spec_name(),
            "price_cost": float(self.price_cost) if self.price_cost else 0,
            "price_sale": float(self.price_sale) if self.price_sale else 0,
            "profit": float(self.price_sale - self.price_cost) if self.price_sale and self.price_cost else 0,
            "is_public": self.is_public == 1,
            "sort_order": self.sort_order,
            "remark": self.remark,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
