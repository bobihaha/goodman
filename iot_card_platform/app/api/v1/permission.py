"""
权限管理 API
"""
from typing import List
from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.permission_service import permission_service
from app.utils.auth import get_current_user
from app.schemas.common import ResponseModel
from app.schemas.auth import CurrentUser
from app.schemas.permission import (
    PermissionCreate, PermissionUpdate, PermissionQuery, 
    UserPermissionAssign
)

router = APIRouter(tags=["权限管理"])


# ============ 权限管理 ============

@router.get("", summary="获取权限列表", response_model=ResponseModel)
async def get_permissions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    module: str = Query(None, description="模块筛选"),
    keyword: str = Query(None, description="关键词搜索"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取权限列表"""
    query = PermissionQuery(page=page, page_size=page_size, module=module, keyword=keyword)
    items, total = await permission_service.get_permission_list(db, query)
    return ResponseModel(data={"total": total, "page": page, "page_size": page_size, "items": items})


@router.get("/all", summary="获取所有权限", response_model=ResponseModel)
async def get_all_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取所有权限（不分页）"""
    permissions = await permission_service.get_all_permissions(db)
    return ResponseModel(data=permissions)


@router.get("/modules", summary="按模块分组获取权限", response_model=ResponseModel)
async def get_permissions_by_module(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    按模块分组获取权限
    返回格式：[{module, module_name, permissions: [...]}]
    """
    modules = await permission_service.get_permissions_by_module(db)
    return ResponseModel(data=modules)


@router.get("/{permission_id}", summary="获取权限详情", response_model=ResponseModel)
async def get_permission(
    permission_id: int = Path(..., description="权限ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取权限详情"""
    permission = await permission_service.get_permission(db, permission_id)
    return ResponseModel(data=permission)


@router.post("", summary="创建权限", response_model=ResponseModel)
async def create_permission(
    data: PermissionCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """创建权限（仅超级管理员）"""
    if not current_user.is_super_admin():
        return ResponseModel(code=403, msg="没有权限")
    
    permission = await permission_service.create_permission(db, data)
    return ResponseModel(data=permission, msg="创建成功")


@router.put("/{permission_id}", summary="更新权限", response_model=ResponseModel)
async def update_permission(
    permission_id: int = Path(..., description="权限ID"),
    data: PermissionUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """更新权限（仅超级管理员）"""
    if not current_user.is_super_admin():
        return ResponseModel(code=403, msg="没有权限")
    
    permission = await permission_service.update_permission(db, permission_id, data)
    return ResponseModel(data=permission, msg="更新成功")


@router.delete("/{permission_id}", summary="删除权限", response_model=ResponseModel)
async def delete_permission(
    permission_id: int = Path(..., description="权限ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """删除权限（仅超级管理员）"""
    if not current_user.is_super_admin():
        return ResponseModel(code=403, msg="没有权限")
    
    await permission_service.delete_permission(db, permission_id)
    return ResponseModel(msg="删除成功")


# ============ 用户权限管理 ============

@router.get("/user/{user_id}", summary="获取用户权限", response_model=ResponseModel)
async def get_user_permissions(
    user_id: int = Path(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取用户的所有权限"""
    permissions = await permission_service.get_user_permissions(db, user_id)
    return ResponseModel(data=permissions)


@router.get("/user/{user_id}/ids", summary="获取用户权限ID列表", response_model=ResponseModel)
async def get_user_permission_ids(
    user_id: int = Path(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取用户的权限ID列表"""
    permission_ids = await permission_service.get_user_permission_ids(db, user_id)
    return ResponseModel(data=permission_ids)


@router.get("/user/{user_id}/codes", summary="获取用户权限代码列表", response_model=ResponseModel)
async def get_user_permission_codes(
    user_id: int = Path(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """获取用户的权限代码列表"""
    permission_codes = await permission_service.get_user_permission_codes(db, user_id)
    return ResponseModel(data=permission_codes)


@router.post("/user/{user_id}/assign", summary="分配用户权限", response_model=ResponseModel)
async def assign_user_permissions(
    user_id: int = Path(..., description="用户ID"),
    data: UserPermissionAssign = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    为用户分配权限（覆盖式）
    会清空用户现有权限，然后分配新权限
    """
    result = await permission_service.assign_user_permissions(db, user_id, data.permission_ids)
    return ResponseModel(data=result, msg="权限分配成功")


@router.post("/user/{user_id}/add", summary="添加用户权限", response_model=ResponseModel)
async def add_user_permissions(
    user_id: int = Path(..., description="用户ID"),
    data: UserPermissionAssign = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    为用户添加权限（追加式）
    不会清空现有权限，只添加新权限
    """
    result = await permission_service.add_user_permissions(db, user_id, data.permission_ids)
    return ResponseModel(data=result, msg="权限添加成功")


@router.post("/user/{user_id}/remove", summary="移除用户权限", response_model=ResponseModel)
async def remove_user_permissions(
    user_id: int = Path(..., description="用户ID"),
    data: UserPermissionAssign = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """移除用户权限"""
    result = await permission_service.remove_user_permissions(db, user_id, data.permission_ids)
    return ResponseModel(data=result, msg="权限移除成功")


@router.get("/user/{user_id}/check/{permission_code}", summary="检查用户权限", response_model=ResponseModel)
async def check_user_permission(
    user_id: int = Path(..., description="用户ID"),
    permission_code: str = Path(..., description="权限代码"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """检查用户是否拥有指定权限"""
    has_permission = await permission_service.check_user_permission(db, user_id, permission_code)
    return ResponseModel(data={"has_permission": has_permission})





