"""
H5 自助服务接口
"""
from fastapi import APIRouter, Depends, Body, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.common import ResponseModel
from app.schemas.h5 import (
    H5CardQueryRequest,
    H5CardSuspendRequest,
    H5CardResumeRequest,
    H5CardRemarkRequest
)
from app.services.h5_service import h5_service

router = APIRouter(prefix="/h5", tags=["H5自助服务"])


@router.get("/{slug}/config", summary="获取H5配置", response_model=ResponseModel)
async def get_h5_config(
    slug: str = Path(...),
    db: AsyncSession = Depends(get_db)
):
    result = await h5_service.get_config(db, slug)
    return ResponseModel(data=result.model_dump())


@router.post("/{slug}/card/query", summary="H5查询卡片", response_model=ResponseModel)
async def query_h5_card(
    slug: str = Path(...),
    request: H5CardQueryRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    result = await h5_service.query_cards(db, slug, request.keyword)
    return ResponseModel(data=result)


@router.get("/{slug}/card/{card_id}", summary="获取H5卡片详情", response_model=ResponseModel)
async def get_h5_card_detail(
    slug: str = Path(...),
    card_id: int = Path(...),
    db: AsyncSession = Depends(get_db)
):
    result = await h5_service.get_card_detail(db, slug, card_id)
    return ResponseModel(data=result)


@router.post("/{slug}/card/{card_id}/suspend", summary="H5停机", response_model=ResponseModel)
async def suspend_h5_card(
    slug: str = Path(...),
    card_id: int = Path(...),
    request: H5CardSuspendRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    result = await h5_service.suspend_card(db, slug, card_id, request.reason)
    return ResponseModel(data=result, msg="停机成功")


@router.post("/{slug}/card/{card_id}/resume", summary="H5复机", response_model=ResponseModel)
async def resume_h5_card(
    slug: str = Path(...),
    card_id: int = Path(...),
    request: H5CardResumeRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    result = await h5_service.resume_card(db, slug, card_id)
    return ResponseModel(data=result, msg="复机成功")


@router.put("/{slug}/card/{card_id}/remark", summary="H5修改备注", response_model=ResponseModel)
async def update_h5_card_remark(
    slug: str = Path(...),
    card_id: int = Path(...),
    payload: H5CardRemarkRequest = Body(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    client_ip = request.client.host if request and request.client else None
    result = await h5_service.update_remark(
        db=db,
        slug=slug,
        card_id=card_id,
        remark=payload.remark,
        client_ip=client_ip,
        operator_name=payload.operator_name,
        operator_phone=payload.operator_phone
    )
    return ResponseModel(data=result, msg="备注更新成功")
