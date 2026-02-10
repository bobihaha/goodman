"""
出入库管理 Pydantic 模型
"""
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field
from enum import Enum


class CarrierType(str, Enum):
    cmcc = "cmcc"
    cucc = "cucc"
    ctcc = "ctcc"


class PeriodType(str, Enum):
    monthly = "monthly"
    yearly = "yearly"


class BatchStatus(str, Enum):
    pending = "pending"
    stocked = "stocked"
    completed = "completed"


# ============ 采购批次 ============

class BatchCreate(BaseModel):
    """创建采购批次"""
    supplier_id: int = Field(..., description="供应商ID")
    package_id: int = Field(..., description="底层套餐ID")
    test_expire_date: Optional[date] = Field(None, description="测试期到期日")
    silent_expire_date: date = Field(..., description="沉默期到期日")
    purchase_date: date = Field(..., description="采购日期")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class BatchInfo(BaseModel):
    """批次信息"""
    id: int
    batch_no: str
    supplier_id: int
    supplier_name: Optional[str] = None
    package_id: int
    package_name: Optional[str] = None
    carrier: Optional[str] = None
    carrier_name: Optional[str] = None
    flow_size: int
    period_type: Optional[str] = None
    period_name: Optional[str] = None
    test_expire_date: Optional[str] = None
    silent_expire_date: Optional[str] = None
    card_count: int = 0
    stocked_count: int = 0
    out_count: int = 0
    stock_remain: int = 0
    purchase_date: Optional[str] = None
    remark: Optional[str] = None
    status: Optional[str] = None
    status_name: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


# ============ 入库 ============

class CardImportItem(BaseModel):
    """单张卡导入数据"""
    iccid: str = Field(..., min_length=19, max_length=30, description="ICCID")
    imsi: Optional[str] = Field(None, max_length=20, description="IMSI")
    msisdn: Optional[str] = Field(None, max_length=20, description="号码")


class StockInCreate(BaseModel):
    """入库请求"""
    batch_id: int = Field(..., description="批次ID")
    cards: List[CardImportItem] = Field(..., min_length=1, description="卡片列表")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class StockInInfo(BaseModel):
    """入库记录信息"""
    id: int
    record_no: str
    batch_id: int
    batch_no: Optional[str] = None
    card_count: int = 0
    success_count: int = 0
    fail_count: int = 0
    remark: Optional[str] = None
    status: Optional[str] = None
    status_name: Optional[str] = None
    confirmed_at: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class StockInResult(BaseModel):
    """入库结果"""
    record_no: str
    total: int
    success: int
    failed: int
    fail_details: Optional[List[dict]] = None


# ============ 出库 ============

class StockOutCreate(BaseModel):
    """出库请求"""
    card_ids: List[int] = Field(..., min_length=1, description="卡片ID列表")
    to_user_id: int = Field(..., description="目标用户ID")
    sale_package_id: int = Field(..., description="销售套餐ID")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class StockOutInfo(BaseModel):
    """出库记录信息"""
    id: int
    record_no: str
    to_user_id: int
    to_user_name: Optional[str] = None
    sale_package_id: int
    sale_package_name: Optional[str] = None
    card_count: int = 0
    remark: Optional[str] = None
    status: Optional[str] = None
    status_name: Optional[str] = None
    confirmed_at: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class StockOutResult(BaseModel):
    """出库结果"""
    record_no: str
    total: int
    success: int
    failed: int


# ============ 库存统计 ============

class StockSummary(BaseModel):
    """库存统计"""
    total_cards: int = 0
    stock_cards: int = 0
    out_cards: int = 0
    by_carrier: Optional[dict] = None
    by_supplier: Optional[dict] = None


# ============ 入库记录 ============

class StockInRecordInfo(BaseModel):
    """入库记录详情"""
    id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    package_id: int
    package_name: Optional[str] = None
    card_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    test_expire_date: Optional[str] = None
    silent_expire_date: Optional[str] = None
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None
    remark: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class StockInRecordDetail(StockInRecordInfo):
    """入库记录详情（含卡片列表）"""
    cards: Optional[List[dict]] = None


# ============ 出库记录 ============

class StockOutRecordInfo(BaseModel):
    """出库记录详情"""
    id: int
    user_id: int
    user_name: Optional[str] = None
    sale_package_id: int
    sale_package_name: Optional[str] = None
    card_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    unit_price: Optional[float] = None
    total_amount: Optional[float] = None
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None
    remark: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class StockOutRecordDetail(StockOutRecordInfo):
    """出库记录详情（含卡片列表）"""
    cards: Optional[List[dict]] = None


# ============ 卡片回收 ============

class StockRecycleCreate(BaseModel):
    """卡片回收请求"""
    card_ids: List[int] = Field(..., min_length=1, description="卡片ID列表")
    recycle_reason: str = Field(..., min_length=1, max_length=500, description="回收原因")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class StockRecycleResult(BaseModel):
    """回收结果"""
    success: int
    failed: int
    record_id: int


class StockRecycleRecordInfo(BaseModel):
    """回收记录信息"""
    id: int
    card_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    recycle_reason: str
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None
    remark: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


# ============ 批量查询 ============

class BatchQueryRequest(BaseModel):
    """批量查询请求"""
    iccids: List[str] = Field(..., min_length=1, max_length=10000, description="ICCID列表")


class BatchQueryResult(BaseModel):
    """批量查询结果"""
    found: List[dict]
    not_found: List[str]
