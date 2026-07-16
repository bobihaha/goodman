"""
系统用户管理接口
"""
from fastapi import APIRouter, Depends, Body, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.sys_user import (
    UserCreate, UserUpdate, UserInfo, UserQuery, UserPasswordUpdate,
    UserPasswordReset, UserStatus, UserBalanceGrantRequest,
    UserH5ConfigUpdate, UserH5StatusUpdate
)
from app.schemas.common import ResponseModel
from app.schemas.auth import CurrentUser
from app.services.sys_user_service import sys_user_service
from app.db.database import get_db
from app.utils.auth import get_current_user

router = APIRouter()


@router.post("", summary="创建用户", response_model=ResponseModel)
async def create_user(user_data: UserCreate = Body(...), db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    user_info = await sys_user_service.create_user(db, current_user, user_data)
    return ResponseModel(msg="创建成功", data=user_info.model_dump())


@router.get("", summary="用户列表", response_model=ResponseModel)
async def get_user_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query(None),
    status: UserStatus = Query(None),
    channel_id: int = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    query = UserQuery(page=page, page_size=page_size, keyword=keyword, status=status, channel_id=channel_id)
    users, total = await sys_user_service.get_user_list(db, current_user, query)
    return ResponseModel(data={"list": [u.model_dump() for u in users], "total": total, "page": page, "page_size": page_size})


@router.get("/{user_id}", summary="用户详情", response_model=ResponseModel)
async def get_user_detail(user_id: int = Path(...), db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    user_info = await sys_user_service.get_user_detail(db, current_user, user_id)
    return ResponseModel(data=user_info.model_dump())


@router.put("/{user_id}", summary="更新用户", response_model=ResponseModel)
async def update_user(user_id: int = Path(...), user_data: UserUpdate = Body(...), db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    user_info = await sys_user_service.update_user(db, current_user, user_id, user_data)
    return ResponseModel(msg="更新成功", data=user_info.model_dump())


@router.delete("/{user_id}", summary="删除用户", response_model=ResponseModel)
async def delete_user(user_id: int = Path(...), db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    await sys_user_service.delete_user(db, current_user, user_id)
    return ResponseModel(msg="删除成功")


@router.put("/{user_id}/status", summary="修改用户状态", response_model=ResponseModel)
async def change_user_status(user_id: int = Path(...), status: UserStatus = Body(..., embed=True), db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    user_info = await sys_user_service.change_status(db, current_user, user_id, status)
    return ResponseModel(msg="操作成功", data=user_info.model_dump())


@router.put("/{user_id}/password", summary="重置用户密码", response_model=ResponseModel)
async def reset_user_password(user_id: int = Path(...), password_data: UserPasswordReset = Body(...), db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    await sys_user_service.reset_password(db, current_user, user_id, password_data)
    return ResponseModel(msg="密码重置成功")


@router.post("/{user_id}/balance/grant", summary="给用户分配余额", response_model=ResponseModel)
async def grant_user_balance(
    user_id: int = Path(...),
    request: UserBalanceGrantRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    result = await sys_user_service.grant_balance(
        db=db,
        operator=current_user,
        user_id=user_id,
        amount=request.amount,
        remark=request.remark,
        request_id=request.request_id
    )
    return ResponseModel(data=result, msg="余额分配成功")


@router.post("/{user_id}/h5/generate", summary="生成用户H5地址", response_model=ResponseModel)
async def generate_user_h5(
    user_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    config = await sys_user_service.generate_h5(db, current_user, user_id)
    return ResponseModel(data=config.model_dump(), msg="H5地址生成成功")


@router.get("/{user_id}/h5/detail", summary="获取用户H5配置", response_model=ResponseModel)
async def get_user_h5_detail(
    user_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    config = await sys_user_service.get_h5_detail(db, current_user, user_id)
    return ResponseModel(data=config.model_dump())


@router.put("/{user_id}/h5/config", summary="更新用户H5配置", response_model=ResponseModel)
async def update_user_h5_config(
    user_id: int = Path(...),
    payload: UserH5ConfigUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    config = await sys_user_service.update_h5_config(db, current_user, user_id, payload)
    return ResponseModel(data=config.model_dump(), msg="H5配置更新成功")


@router.post("/{user_id}/h5/reset", summary="重置用户H5地址", response_model=ResponseModel)
async def reset_user_h5(
    user_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    config = await sys_user_service.reset_h5(db, current_user, user_id)
    return ResponseModel(data=config.model_dump(), msg="H5地址已重置")


@router.put("/{user_id}/h5/status", summary="修改用户H5状态", response_model=ResponseModel)
async def update_user_h5_status(
    user_id: int = Path(...),
    payload: UserH5StatusUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    config = await sys_user_service.change_h5_status(db, current_user, user_id, payload.status)
    return ResponseModel(data=config.model_dump(), msg="H5状态更新成功")


@router.get("/{user_id}/api-credentials", summary="获取开放API凭证", response_model=ResponseModel)
async def get_user_open_api_credentials(
    user_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    config = await sys_user_service.get_open_api_credentials(db, current_user, user_id)
    return ResponseModel(data=config.model_dump())


@router.post("/{user_id}/api-credentials/reset", summary="重置开放API凭证", response_model=ResponseModel)
async def reset_user_open_api_credentials(
    user_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    config = await sys_user_service.reset_open_api_credentials(db, current_user, user_id)
    return ResponseModel(data=config.model_dump(), msg="开放API凭证已重置")


@router.put("/password/change", summary="修改密码", response_model=ResponseModel)
async def change_password(password_data: UserPasswordUpdate = Body(...), db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    await sys_user_service.change_password(db, current_user, password_data)
    return ResponseModel(msg="密码修改成功")
