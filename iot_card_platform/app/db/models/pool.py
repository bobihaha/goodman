"""
流量池模型
相同规格 (运营商+流量+周期) 的已激活卡可组池共享
"""
from sqlalchemy import Column, String, Enum, BigInteger, Integer, DateTime
from enum import Enum as PyEnum
from app.db.models.base import BaseModel
from app.db.models.package import CarrierType, PeriodType, CARRIER_NAMES, PERIOD_CONFIG


class PoolStatus(str, PyEnum):
    """流量池状态"""
    enable = "enable"       # 启用
    disable = "disable"     # 停用


POOL_STATUS_NAMES = {
    "enable": "启用",
    "disable": "停用"
}


class TrafficPoolModel(BaseModel):
    """流量池模型"""
    __tablename__ = "traffic_pools"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="流量池ID")
    
    # 基本信息
    name = Column(String(100), nullable=False, comment="流量池名称")
    
    # 规格信息 (组池条件：相同规格的卡才能入池)
    carrier = Column(Enum(CarrierType), nullable=False, comment="运营商")
    flow_size = Column(BigInteger, nullable=False, comment="套餐流量(MB)")
    period_type = Column(Enum(PeriodType), nullable=False, comment="周期类型")
    sale_package_id = Column(BigInteger, nullable=True, index=True, comment="销售套餐ID（组池依据）")

    # 归属
    user_id = Column(BigInteger, nullable=True, index=True, comment="所属用户ID(NULL=平台池)")

    # 统计 (实时更新)
    card_count = Column(Integer, nullable=False, default=0, comment="卡片数量")
    data_total = Column(BigInteger, nullable=False, default=0, comment="总流量(MB)")
    data_used = Column(BigInteger, nullable=False, default=0, comment="已用流量(MB)")
    package_flow = Column(BigInteger, nullable=False, default=0, comment="套餐流量(MB)")
    addon_flow = Column(BigInteger, nullable=False, default=0, comment="叠加流量包(MB)")
    addon_flow_month = Column(String(7), nullable=True, comment="叠加流量生效月份(YYYY-MM)")

    # 阈值设置
    alert_threshold_1 = Column(Integer, nullable=True, comment="告警阈值1百分比")
    alert_threshold_2 = Column(Integer, nullable=True, comment="告警阈值2百分比")
    alert_threshold_3 = Column(Integer, nullable=True, comment="告警阈值3百分比")

    # 状态
    status = Column(Enum(PoolStatus), nullable=False, default=PoolStatus.enable, comment="状态")
    
    # 备注
    remark = Column(String(500), nullable=True, comment="备注")
    
    # 同步时间
    last_sync_at = Column(DateTime, nullable=True, comment="最近同步时间")
    
    # 创建人
    created_by = Column(BigInteger, nullable=True, comment="创建人ID")

    def get_spec_name(self) -> str:
        """生成规格名称: 移动1G/月"""
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

    def get_data_remain(self) -> int:
        """获取剩余流量"""
        return max(0, self.data_total - self.data_used)

    def get_usage_percent(self) -> float:
        """获取用量百分比"""
        if not self.data_total or self.data_total == 0:
            return 0
        return round((self.data_used / self.data_total) * 100, 2)

    def is_alert(self) -> bool:
        """是否达到告警阈值"""
        usage = self.get_usage_percent()
        if self.alert_threshold_1 and usage >= self.alert_threshold_1:
            return True
        if self.alert_threshold_2 and usage >= self.alert_threshold_2:
            return True
        if self.alert_threshold_3 and usage >= self.alert_threshold_3:
            return True
        return False

    def is_exceed(self) -> bool:
        """是否超过最高阈值"""
        if not self.alert_threshold_3:
            return False
        return self.get_usage_percent() >= self.alert_threshold_3

    def to_dict(self, include_card_stats=False, card_stats=None):
        """
        转换为字典
        :param include_card_stats: 是否包含卡片统计信息
        :param card_stats: 卡片统计数据（如果已经查询过）
        """
        result = {
            "id": self.id,
            "name": self.name,
            "carrier": self.carrier.value if self.carrier else None,
            "carrier_name": CARRIER_NAMES.get(self.carrier.value, "") if self.carrier else None,
            "flow_size": self.flow_size,
            "flow_size_display": self._format_flow_size(),
            "period_type": self.period_type.value if self.period_type else None,
            "period_name": PERIOD_CONFIG.get(self.period_type.value, {}).get("name", "") if self.period_type else None,
            "spec_name": self.get_spec_name(),
            "sale_package_id": self.sale_package_id,
            "user_id": self.user_id,
            "card_count": self.card_count,
            "data_total": self.data_total,
            "data_used": self.data_used,
            "data_remaining": self.get_data_remain(),
            "package_flow": self.package_flow,
            "addon_flow": self.addon_flow,
            "addon_flow_month": self.addon_flow_month,
            "usage_percent": self.get_usage_percent(),
            "alert_threshold_1": self.alert_threshold_1,
            "alert_threshold_2": self.alert_threshold_2,
            "alert_threshold_3": self.alert_threshold_3,
            "is_alert": self.is_alert(),
            "is_exceed": self.is_exceed(),
            "status": self.status.value if self.status else None,
            "status_name": POOL_STATUS_NAMES.get(self.status.value, "") if self.status else None,
            "remark": self.remark,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # 如果需要包含卡片统计信息
        if include_card_stats and card_stats:
            result["card_stats"] = card_stats
        
        return result


class PoolCardLogModel(BaseModel):
    """流量池卡片变动记录"""
    __tablename__ = "pool_card_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    pool_id = Column(BigInteger, nullable=False, index=True, comment="流量池ID")
    card_id = Column(BigInteger, nullable=False, index=True, comment="卡片ID")
    iccid = Column(String(30), nullable=False, comment="ICCID")
    action = Column(String(20), nullable=False, comment="操作: add/remove")
    operator_id = Column(BigInteger, nullable=False, comment="操作人ID")
    remark = Column(String(200), nullable=True, comment="备注")

    def to_dict(self):
        return {
            "id": self.id,
            "pool_id": self.pool_id,
            "card_id": self.card_id,
            "iccid": self.iccid,
            "action": self.action,
            "operator_id": self.operator_id,
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
