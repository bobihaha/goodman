"""
项目模型 - 三级用户用于管理卡片分组
"""
from sqlalchemy import Column, String, BigInteger
from app.db.models.base import BaseModel


class ProjectModel(BaseModel):
    __tablename__ = "projects"

    name = Column(String(100), nullable=False, comment="项目名称")
    user_id = Column(BigInteger, nullable=False, index=True, comment="所属用户ID")
    remark = Column(String(500), nullable=True, comment="备注")
