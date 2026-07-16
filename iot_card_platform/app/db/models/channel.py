"""渠道伙伴与推广积分模型。"""
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    DECIMAL,
    Index,
    Integer,
    String,
    UniqueConstraint,
)

from app.db.models.base import BaseModel


class ChannelPartnerModel(BaseModel):
    __tablename__ = "channel_partners"

    name = Column(String(100), nullable=False, comment="渠道名称")
    contact_name = Column(String(50), nullable=False, comment="联系人")
    phone = Column(String(20), nullable=False, unique=True, index=True, comment="联系电话")
    account = Column(String(50), nullable=False, unique=True, index=True, comment="渠道登录账号")
    password = Column(String(128), nullable=False, comment="渠道登录密码哈希")
    h5_slug = Column(String(32), nullable=False, unique=True, index=True, comment="客户报备H5标识")
    registration_enabled = Column(Integer, nullable=False, default=1, comment="是否允许H5报备")
    status = Column(String(20), nullable=False, default="enable", index=True, comment="enable/disable")
    stock_out_rate_override = Column(DECIMAL(7, 4), nullable=True, comment="出库积分比例覆盖(%)")
    renewal_rate_override = Column(DECIMAL(7, 4), nullable=True, comment="续费积分比例覆盖(%)")
    last_login_at = Column(DateTime, nullable=True, comment="最近登录时间")
    created_by = Column(BigInteger, nullable=True, comment="创建人ID")
    remark = Column(String(500), nullable=True, comment="备注")


class ChannelCommissionSettingModel(BaseModel):
    __tablename__ = "channel_commission_settings"

    default_stock_out_rate = Column(DECIMAL(7, 4), nullable=False, default=0, comment="默认出库积分比例(%)")
    default_renewal_rate = Column(DECIMAL(7, 4), nullable=False, default=0, comment="默认续费积分比例(%)")
    updated_by = Column(BigInteger, nullable=True, comment="更新人ID")


class ChannelCustomerRelationModel(BaseModel):
    __tablename__ = "channel_customer_relations"
    __table_args__ = (
        UniqueConstraint("customer_phone", name="uk_channel_customer_phone"),
        UniqueConstraint("user_id", name="uk_channel_customer_user"),
        Index("idx_channel_customer_channel_status", "channel_id", "status"),
    )

    channel_id = Column(BigInteger, nullable=False, index=True, comment="渠道ID")
    user_id = Column(BigInteger, nullable=False, index=True, comment="平台用户ID")
    customer_name = Column(String(50), nullable=False, comment="客户姓名快照")
    customer_phone = Column(String(20), nullable=False, comment="客户手机号快照")
    customer_profile = Column(String(500), nullable=True, comment="用户情况：设备、场景、规模")
    status = Column(String(20), nullable=False, default="active", comment="active/inactive")
    source = Column(String(30), nullable=False, default="channel_h5", comment="归属来源")
    registered_ip = Column(String(50), nullable=True, comment="报备IP")
    registered_user_agent = Column(String(500), nullable=True, comment="报备User-Agent")
    registered_at = Column(DateTime, nullable=False, comment="报备时间")


class RenewalOrderModel(BaseModel):
    __tablename__ = "renewal_orders"

    order_no = Column(String(50), nullable=False, unique=True, index=True, comment="续费订单号")
    user_id = Column(BigInteger, nullable=False, index=True, comment="购买用户ID")
    card_id = Column(BigInteger, nullable=False, index=True, comment="卡片ID")
    iccid = Column(String(30), nullable=False, index=True, comment="ICCID")
    renew_months = Column(Integer, nullable=False, comment="续费月数")
    unit_price = Column(DECIMAL(12, 2), nullable=False, comment="续费单价(元/月)")
    total_amount = Column(DECIMAL(14, 2), nullable=False, comment="订单总额(元)")
    status = Column(String(20), nullable=False, default="completed", index=True, comment="completed/reversed")
    completed_at = Column(DateTime, nullable=False, comment="完成时间")
    operator_id = Column(BigInteger, nullable=False, comment="操作用户ID")


class ChannelPointLedgerModel(BaseModel):
    __tablename__ = "channel_point_ledger"
    __table_args__ = (
        UniqueConstraint(
            "entry_type",
            "order_type",
            "source_order_id",
            "card_id",
            name="uk_channel_point_source_card",
        ),
        Index("idx_channel_point_channel_status_time", "channel_id", "status", "created_at"),
        Index("idx_channel_point_user_time", "user_id", "created_at"),
    )

    channel_id = Column(BigInteger, nullable=False, index=True, comment="渠道ID")
    relation_id = Column(BigInteger, nullable=False, index=True, comment="渠道客户关系ID")
    user_id = Column(BigInteger, nullable=False, index=True, comment="平台客户ID")
    customer_name = Column(String(50), nullable=False, comment="客户姓名快照")
    customer_phone = Column(String(20), nullable=False, comment="客户手机号快照")
    entry_type = Column(String(20), nullable=False, default="credit", comment="credit/reversal")
    order_type = Column(String(20), nullable=False, index=True, comment="stock_out/renewal")
    source_order_id = Column(BigInteger, nullable=False, comment="来源订单ID")
    source_order_no = Column(String(50), nullable=False, index=True, comment="来源订单号")
    card_id = Column(BigInteger, nullable=False, index=True, comment="卡片ID")
    iccid = Column(String(30), nullable=False, comment="ICCID")
    base_amount = Column(DECIMAL(14, 2), nullable=False, comment="计佣基数(元)")
    rate_percent = Column(DECIMAL(7, 4), nullable=False, comment="比例快照(%)")
    points = Column(DECIMAL(14, 4), nullable=False, comment="推广积分")
    status = Column(String(20), nullable=False, default="pending", index=True, comment="pending/settled")
    related_entry_id = Column(BigInteger, nullable=True, index=True, comment="冲正关联的原积分ID")
    settled_by = Column(BigInteger, nullable=True, comment="结算人ID")
    settled_at = Column(DateTime, nullable=True, comment="结算时间")
