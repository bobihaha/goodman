"""
项目模块数据模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    remark: Optional[str] = Field(None, max_length=500, description="备注")

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("项目名称不能为空")
        return value.strip()


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="项目名称")
    remark: Optional[str] = Field(None, max_length=500, description="备注")

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: Optional[str]) -> Optional[str]:
        return ProjectCreate.trim_name(value) if value is not None else None


class ProjectOrderRequest(BaseModel):
    project_ids: list[int] = Field(..., min_length=1, max_length=10000)


class ProjectMoveRequest(BaseModel):
    iccids: list[str] = Field(..., min_length=1, max_length=10000)
    project_id: Optional[int] = Field(..., gt=0, description="目标项目，null 表示移出项目")
    source_project_id: Optional[int] = Field(None, gt=0, description="限制来源项目")
    source_ungrouped: bool = False


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
