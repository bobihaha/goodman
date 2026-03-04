"""
项目模块数据模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="项目名称")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class ProjectInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    user_id: int
    remark: Optional[str] = None
    card_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProjectQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    keyword: Optional[str] = None
