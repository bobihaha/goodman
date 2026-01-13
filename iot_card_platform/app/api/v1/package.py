"""
套餐模块接口
"""
from fastapi import APIRouter, Depends, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.package import PackageCreate, PackageUpdate, PackageInfo
from app.schemas.common import ResponseModel
from app.services.package_service import PackageService
from app.db.database import get_db
from app.utils.auth import get_current_user, RoleChecker

router = APIRouter()
admin_checker = RoleChecker(["admin"])


@router.post("/create", summary="创建套餐", response_model=ResponseModel)
async def create_package(
    data: PackageCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(admin_checker)
):
    package_info = await PackageService.create_package(db, data)
    return ResponseModel(data=package_info.model_dump())


@router.get("/list", summary="套餐列表", response_model=ResponseModel)
async def get_package_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    packages, total = await PackageService.get_package_list(db, page, page_size)
    return ResponseModel(data={
        "list": [p.model_dump() for p in packages],
        "total": total,
        "page": page,
        "page_size": page_size
    })


@router.get("/detail/{package_id}", summary="套餐详情", response_model=ResponseModel)
async def get_package_detail(
    package_id: int,
    db: AsyncSession = Depends(get_db)
):
    package_info = await PackageService.get_package_by_id(db, package_id)
    return ResponseModel(data=package_info.model_dump())


@router.put("/update/{package_id}", summary="更新套餐", response_model=ResponseModel)
async def update_package(
    package_id: int,
    data: PackageUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(admin_checker)
):
    package_info = await PackageService.update_package(db, package_id, data)
    return ResponseModel(data=package_info.model_dump())


@router.delete("/delete/{package_id}", summary="删除套餐", response_model=ResponseModel)
async def delete_package(
    package_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(admin_checker)
):
    await PackageService.delete_package(db, package_id)
    return ResponseModel(msg="删除成功")
