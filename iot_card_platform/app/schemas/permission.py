"""
权限管理数据模型
"""
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class PermissionBase(BaseModel):
    """权限基础模型"""
    code: str = Field(..., min_length=1, max_length=100, description="权限代码")
    name: str = Field(..., min_length=1, max_length=100, description="权限名称")
    module: str = Field(..., min_length=1, max_length=50, description="所属模块")
    description: Optional[str] = Field(None, max_length=500, description="权限描述")
    sort_order: int = Field(default=0, description="排序")


class PermissionCreate(PermissionBase):
    """创建权限"""
    pass


class PermissionUpdate(BaseModel):
    """更新权限"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    sort_order: Optional[int] = None


class PermissionInfo(PermissionBase):
    """权限信息"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PermissionQuery(BaseModel):
    """权限查询参数"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    module: Optional[str] = None
    keyword: Optional[str] = None


class UserPermissionAssign(BaseModel):
    """用户权限分配"""
    permission_ids: List[int] = Field(..., description="权限ID列表")


class PermissionModule(BaseModel):
    """权限模块"""
    module: str = Field(..., description="模块名称")
    module_name: str = Field(..., description="模块显示名称")
    permissions: List[PermissionInfo] = Field(default_factory=list, description="权限列表")




