"""
供应商模型
"""
from sqlalchemy import Column, String, Enum, BigInteger, Integer, Text, JSON
from enum import Enum as PyEnum
from app.db.models.base import BaseModel


class SupplierType(str, PyEnum):
    """供应商类型"""
    cmcc = "cmcc"       # 中国移动
    cucc = "cucc"       # 中国联通
    ctcc = "ctcc"       # 中国电信
    mvno = "mvno"       # 虚拟运营商
    other = "other"     # 其他


class SupplierStatus(str, PyEnum):
    """供应商状态"""
    enable = "enable"
    disable = "disable"


class SupplierModel(BaseModel):
    """供应商模型"""
    __tablename__ = "suppliers"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="供应商ID")
    name = Column(String(100), nullable=False, comment="供应商名称")
    code = Column(String(50), nullable=False, unique=True, comment="供应商编码")
    type = Column(Enum(SupplierType), default=SupplierType.other, comment="供应商类型")
    contact_name = Column(String(50), nullable=True, comment="联系人")
    contact_phone = Column(String(20), nullable=True, comment="联系电话")
    contact_email = Column(String(100), nullable=True, comment="联系邮箱")
    api_url = Column(String(255), nullable=True, comment="API地址")
    api_key = Column(String(255), nullable=True, comment="API Key")
    api_secret = Column(String(255), nullable=True, comment="API Secret")
    api_config = Column(JSON, nullable=True, comment="API配置")
    sync_interval = Column(Integer, nullable=True, default=60, comment="同步间隔(分钟)")
    remark = Column(String(500), nullable=True, comment="备注")
    status = Column(Enum(SupplierStatus), default=SupplierStatus.enable, comment="状态")
    created_by = Column(BigInteger, nullable=True, comment="创建人ID")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "type": self.type.value if self.type else None,
            "contact_name": self.contact_name,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "api_url": self.api_url,
            "has_api_key": bool(self.api_key),
            "has_api_secret": bool(self.api_secret),
            "api_config": self.api_config,
            "sync_interval": self.sync_interval,
            "remark": self.remark,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
