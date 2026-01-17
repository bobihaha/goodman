"""
公共数据模型
"""
from typing import Any, Optional
from pydantic import BaseModel, Field


class ResponseModel(BaseModel):
    """统一返回体"""
    code: int = Field(200, description="状态码")
    msg: str = Field("success", description="提示信息")
    data: Optional[Any] = Field(None, description="业务数据")


class PageQuery(BaseModel):
    """分页查询"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页条数")


class PageResponse(BaseModel):
    """分页响应"""
    items: list = Field([], description="数据列表")
    total: int = Field(0, description="总条数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(10, description="每页条数")


class PageResponseModel(BaseModel):
    """分页返回体"""
    code: int = Field(200, description="状态码")
    msg: str = Field("success", description="提示信息")
    data: Optional[list] = Field(None, description="数据列表")
    total: int = Field(0, description="总条数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(10, description="每页条数")
