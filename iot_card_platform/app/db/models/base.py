"""
ORM 基础模型
"""
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BaseModel(Base):
    """ORM 基础模型"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    is_deleted = Column(Integer, default=0, comment="删除标记：0=未删除，1=已删除")
