"""
供应商回调 API
"""
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.suspend_service import SupplierCallbackService
from app.utils.logger import logger

router = APIRouter()


async def _parse_callback_payload(request: Request) -> Dict[str, Any]:
    content_type = request.headers.get("content-type", "").lower()

    if "application/json" in content_type:
        payload = await request.json()
        return payload if isinstance(payload, dict) else {}

    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        return dict(form)

    try:
        payload = await request.json()
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass

    try:
        form = await request.form()
        return dict(form)
    except Exception:
        return dict(request.query_params)


@router.post("/upiot/sor", summary="UPIOT 停复机回调")
async def upiot_sor_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    payload = await _parse_callback_payload(request)

    try:
        await SupplierCallbackService.handle_upiot_sor_callback(db, payload)
    except Exception as exc:
        logger.error("UPIOT 停复机回调处理失败: %s payload=%s", exc, payload, exc_info=True)

    return PlainTextResponse("success")
