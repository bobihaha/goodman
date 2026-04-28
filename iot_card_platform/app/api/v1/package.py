"""
套餐管理接口
规格三要素: 运营商 + 流量 + 周期类型
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.common import ResponseModel
from app.schemas.package import (
    SupplierPackageCreate, SupplierPackageUpdate, SupplierPackageQuery,
    SalePackageCreate, SalePackageUpdate, SalePackageQuery,
    CarrierType, PeriodType, PackageStatus
)
from app.schemas.auth import CurrentUser
from app.services.package_service import supplier_package_service, sale_package_service
from app.db.database import get_db
from app.utils.auth import get_current_user, require_super_admin

router = APIRouter()


# ========== 底层套餐接口 (仅超级管理员) ==========

@router.get("/supplier", summary="获取底层套餐列表", response_model=ResponseModel)
async def get_supplier_package_list(
    keyword: Optional[str] = Query(None, description="关键字搜索"),
    supplier_id: Optional[int] = Query(None, description="供应商ID"),
    carrier: Optional[CarrierType] = Query(None, description="运营商"),
    period_type: Optional[PeriodType] = Query(None, description="周期类型: 月包/年包"),
    status: Optional[PackageStatus] = Query(None, description="状态"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取底层套餐列表 (仅超级管理员)"""
    query = SupplierPackageQuery(
        keyword=keyword, supplier_id=supplier_id, carrier=carrier,
        period_type=period_type, status=status, page=page, page_size=page_size
    )
    result = await supplier_package_service.get_package_list(db, query)
    return ResponseModel(data=result)


@router.get("/supplier/options", summary="获取启用的底层套餐选项", response_model=ResponseModel)
async def get_enabled_supplier_packages(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取所有启用的底层套餐 (用于下拉选择)"""
    query = SupplierPackageQuery(status="enable", page=1, page_size=100)
    result = await supplier_package_service.get_package_list(db, query)
    return ResponseModel(data=result.get("list", []))


@router.get("/supplier/options/{supplier_id}", summary="获取供应商套餐选项", response_model=ResponseModel)
async def get_supplier_package_options(
    supplier_id: int = Path(..., description="供应商ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取供应商的套餐列表 (用于下拉选择)"""
    result = await supplier_package_service.get_by_supplier(db, supplier_id)
    return ResponseModel(data=result)


@router.post("/supplier", summary="创建底层套餐", response_model=ResponseModel)
async def create_supplier_package(
    data: SupplierPackageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    创建底层套餐 (仅超级管理员)
    
    规格三要素: carrier(运营商) + flow_size(流量MB) + period_type(周期类型)
    
    有效天数默认值:
    - 月包(monthly): 30天
    - 年包(yearly): 自激活后12个月，首月不足30天按一个月
    """
    result = await supplier_package_service.create_package(db, data, current_user.id)
    return ResponseModel(msg="创建成功", data=result)


@router.get("/supplier/{package_id}", summary="获取底层套餐详情", response_model=ResponseModel)
async def get_supplier_package(
    package_id: int = Path(..., description="套餐ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取底层套餐详情"""
    result = await supplier_package_service.get_package(db, package_id)
    return ResponseModel(data=result)


@router.put("/supplier/{package_id}", summary="更新底层套餐", response_model=ResponseModel)
async def update_supplier_package(
    data: SupplierPackageUpdate,
    package_id: int = Path(..., description="套餐ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """更新底层套餐 (仅超级管理员)"""
    result = await supplier_package_service.update_package(db, package_id, data)
    return ResponseModel(msg="更新成功", data=result)


@router.delete("/supplier/{package_id}", summary="删除底层套餐", response_model=ResponseModel)
async def delete_supplier_package(
    package_id: int = Path(..., description="套餐ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """删除底层套餐 (仅超级管理员)"""
    await supplier_package_service.delete_package(db, package_id)
    return ResponseModel(msg="删除成功")


# ========== 销售套餐接口 ==========

@router.get("/sale", summary="获取销售套餐列表", response_model=ResponseModel)
async def get_sale_package_list(
    keyword: Optional[str] = Query(None, description="关键字搜索"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    carrier: Optional[CarrierType] = Query(None, description="运营商"),
    period_type: Optional[PeriodType] = Query(None, description="周期类型"),
    is_public: Optional[bool] = Query(None, description="是否公开"),
    status: Optional[PackageStatus] = Query(None, description="状态"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取销售套餐列表"""
    query = SalePackageQuery(
        keyword=keyword, user_id=user_id, carrier=carrier,
        period_type=period_type, is_public=is_public, status=status,
        page=page, page_size=page_size
    )
    result = await sale_package_service.get_package_list(db, query, current_user)
    return ResponseModel(data=result)


@router.get("/sale/options", summary="获取销售套餐选项", response_model=ResponseModel)
async def get_sale_package_options(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取当前用户可用的套餐列表 (用于下拉选择)"""
    result = await sale_package_service.get_user_packages(db, current_user.id)
    return ResponseModel(data=result)


@router.post("/sale", summary="创建销售套餐", response_model=ResponseModel)
async def create_sale_package(
    data: SalePackageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """创建销售套餐"""
    result = await sale_package_service.create_package(db, data, current_user)
    return ResponseModel(msg="创建成功", data=result)


@router.get("/sale/{package_id}", summary="获取销售套餐详情", response_model=ResponseModel)
async def get_sale_package(
    package_id: int = Path(..., description="套餐ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取销售套餐详情"""
    result = await sale_package_service.get_package(db, package_id, current_user)
    return ResponseModel(data=result)


@router.put("/sale/{package_id}", summary="更新销售套餐", response_model=ResponseModel)
async def update_sale_package(
    data: SalePackageUpdate,
    package_id: int = Path(..., description="套餐ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """更新销售套餐"""
    result = await sale_package_service.update_package(db, package_id, data, current_user)
    return ResponseModel(msg="更新成功", data=result)


@router.delete("/sale/{package_id}", summary="删除销售套餐", response_model=ResponseModel)
async def delete_sale_package(
    package_id: int = Path(..., description="套餐ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """删除销售套餐"""
    await sale_package_service.delete_package(db, package_id, current_user)
    return ResponseModel(msg="删除成功")
