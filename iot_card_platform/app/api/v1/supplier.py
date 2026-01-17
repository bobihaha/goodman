"""
供应商管理接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.common import ResponseModel
from app.schemas.supplier import (
    SupplierCreate, SupplierUpdate, SupplierQuery,
    SupplierType, SupplierStatus
)
from app.schemas.auth import CurrentUser
from app.services.supplier_service import supplier_service
from app.db.database import get_db
from app.utils.auth import get_current_user, require_super_admin

router = APIRouter()


@router.get("", summary="获取供应商列表", response_model=ResponseModel)
async def get_supplier_list(
    keyword: Optional[str] = Query(None, description="关键字搜索"),
    type: Optional[SupplierType] = Query(None, description="供应商类型"),
    status: Optional[SupplierStatus] = Query(None, description="状态"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取供应商列表 (仅超级管理员)"""
    query = SupplierQuery(
        keyword=keyword, type=type, status=status,
        page=page, page_size=page_size
    )
    result = await supplier_service.get_supplier_list(db, query)
    return ResponseModel(data=result)


@router.get("/options", summary="获取供应商选项", response_model=ResponseModel)
async def get_supplier_options(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取所有启用的供应商 (用于下拉选择)"""
    result = await supplier_service.get_all_suppliers(db)
    return ResponseModel(data=result)


@router.post("", summary="创建供应商", response_model=ResponseModel)
async def create_supplier(
    data: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """创建供应商 (仅超级管理员)"""
    result = await supplier_service.create_supplier(db, data, current_user.id)
    return ResponseModel(msg="创建成功", data=result)


@router.get("/{supplier_id}", summary="获取供应商详情", response_model=ResponseModel)
async def get_supplier(
    supplier_id: int = Path(..., description="供应商ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """获取供应商详情"""
    result = await supplier_service.get_supplier(db, supplier_id)
    return ResponseModel(data=result)


@router.put("/{supplier_id}", summary="更新供应商", response_model=ResponseModel)
async def update_supplier(
    data: SupplierUpdate,
    supplier_id: int = Path(..., description="供应商ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """更新供应商 (仅超级管理员)"""
    result = await supplier_service.update_supplier(db, supplier_id, data)
    return ResponseModel(msg="更新成功", data=result)


@router.delete("/{supplier_id}", summary="删除供应商", response_model=ResponseModel)
async def delete_supplier(
    supplier_id: int = Path(..., description="供应商ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """删除供应商 (仅超级管理员)"""
    await supplier_service.delete_supplier(db, supplier_id)
    return ResponseModel(msg="删除成功")


@router.post("/{supplier_id}/test", summary="测试API连接", response_model=ResponseModel)
async def test_api_connection(
    supplier_id: int = Path(..., description="供应商ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """测试供应商 API 连通性"""
    result = await supplier_service.test_api_connection(db, supplier_id)
    return ResponseModel(data=result)
