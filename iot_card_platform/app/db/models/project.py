"""
项目模型 - 账号内的卡片项目分组
"""
from sqlalchemy import Column, String, BigInteger, Integer
from app.db.models.base import BaseModel


class ProjectModel(BaseModel):
    __tablename__ = "projects"

    name = Column(String(100), nullable=False, comment="项目名称")
    user_id = Column(BigInteger, nullable=False, index=True, comment="所属用户ID")
    remark = Column(String(500), nullable=True, comment="备注")
    sort_order = Column(Integer, nullable=False, default=0, server_default="0", comment="账号内项目顺序")
