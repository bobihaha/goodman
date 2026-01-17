"""
系统设置相关的 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# ============ 系统配置 ============

class ConfigCreate(BaseModel):
    """创建配置"""
    config_key: str = Field(..., min_length=1, max_length=100, description="配置键")
    config_value: Optional[str] = Field(None, description="配置值")
    config_type: str = Field("string", description="配置类型: string/number/json/boolean")
    description: Optional[str] = Field(None, max_length=200, description="配置描述")
    is_public: bool = Field(False, description="是否公开")


class ConfigUpdate(BaseModel):
    """更新配置"""
    config_value: Optional[str] = Field(None, description="配置值")
    description: Optional[str] = Field(None, max_length=200, description="配置描述")
    is_public: Optional[bool] = Field(None, description="是否公开")


class ConfigBatchUpdate(BaseModel):
    """批量更新配置"""
    configs: List[dict] = Field(..., description="配置列表 [{key: value}, ...]")


class ConfigInfo(BaseModel):
    """配置信息"""
    id: int
    config_key: str
    config_value: Optional[str]
    config_type: str
    description: Optional[str]
    is_public: bool
    created_at: Optional[str]
    updated_at: Optional[str]


# ============ 登录日志 ============

class LoginLogInfo(BaseModel):
    """登录日志信息"""
    id: int
    user_id: Optional[int]
    account: Optional[str]
    login_type: Optional[str]
    login_type_name: Optional[str]
    operator_id: Optional[int]
    is_success: bool
    fail_reason: Optional[str]
    ip: Optional[str]
    user_agent: Optional[str]
    created_at: Optional[str]


# ============ 操作日志 ============

class OperationLogInfo(BaseModel):
    """操作日志信息"""
    id: int
    user_id: Optional[int]
    user_name: Optional[str]
    module: str
    action: str
    target_type: Optional[str]
    target_id: Optional[int]
    target_name: Optional[str]
    detail: Optional[str]
    ip: Optional[str]
    is_success: bool
    error_msg: Optional[str]
    created_at: Optional[str]
