"""
H5 自助服务相关模型
"""
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class H5PortalConfig(BaseModel):
    user_id: int
    user_name: str
    title: Optional[str] = None
    logo: Optional[str] = None
    banner: Optional[str] = None
    notice: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_wechat: Optional[str] = None
    theme: Optional[Dict[str, Any]] = None
    allow_suspend: bool = True
    allow_resume: bool = True
    allow_remark: bool = True
    require_verify: bool = False
    status: str = "enabled"


class H5CardQueryRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=30, description="卡号/ICCID/后6位")


class H5CardCandidate(BaseModel):
    id: int
    iccid_masked: str
    msisdn_masked: Optional[str] = None
    status: Optional[str] = None
    status_name: Optional[str] = None
    spec_name: Optional[str] = None
    activated_at: Optional[str] = None
    expired_at: Optional[str] = None


class H5CardActionFlags(BaseModel):
    allow_suspend: bool = False
    allow_resume: bool = False
    allow_remark: bool = False


class H5CardDetail(BaseModel):
    card: Dict[str, Any]
    diagnostics: Optional[Dict[str, Any]] = None
    actions: H5CardActionFlags


class H5CardQueryResponse(BaseModel):
    match_type: str
    items: List[Union[Dict[str, Any], H5CardCandidate]]


class H5CardRemarkRequest(BaseModel):
    remark: str = Field(..., max_length=500)
    operator_name: Optional[str] = Field(None, max_length=50)
    operator_phone: Optional[str] = Field(None, max_length=20)


class H5CardSuspendRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=200)
    verify_code: Optional[str] = Field(None, max_length=20)


class H5CardResumeRequest(BaseModel):
    verify_code: Optional[str] = Field(None, max_length=20)
