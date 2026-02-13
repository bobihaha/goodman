"""
权限管理模型
"""
from sqlalchemy import Column, BigInteger, String, Integer, SmallInteger
from app.db.models.base import BaseModel


class PermissionModel(BaseModel):
    """权限表"""
    __tablename__ = "sys_permissions"

    code = Column(String(100), nullable=False, unique=True, index=True, comment="权限代码")
    name = Column(String(100), nullable=False, comment="权限名称")
    module = Column(String(50), nullable=False, index=True, comment="所属模块")
    description = Column(String(500), nullable=True, comment="权限描述")
    sort_order = Column(Integer, default=0, comment="排序")

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "module": self.module,
            "description": self.description,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class UserPermissionModel(BaseModel):
    """用户权限关联表"""
    __tablename__ = "sys_user_permissions"

    user_id = Column(BigInteger, nullable=False, index=True, comment="用户ID")
    permission_id = Column(BigInteger, nullable=False, index=True, comment="权限ID")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "permission_id": self.permission_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }





