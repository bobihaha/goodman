"""
供应商回调 API
"""
import hmac
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.config import settings
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
    configured_token = settings.upiot_callback_token.strip()
    provided_token = (
        request.headers.get("X-UPIOT-Callback-Token")
        or request.query_params.get("token")
        or ""
    ).strip()
    if not configured_token:
        logger.error("UPIOT 停复机回调已禁用：未配置回调令牌")
        return PlainTextResponse("callback disabled", status_code=503)
    if not provided_token or not hmac.compare_digest(configured_token, provided_token):
        logger.warning("拒绝未通过鉴权的 UPIOT 停复机回调")
        return PlainTextResponse("forbidden", status_code=403)

    payload = await _parse_callback_payload(request)
    payload.pop("token", None)

    try:
        await SupplierCallbackService.handle_upiot_sor_callback(db, payload)
    except Exception as exc:
        logger.error("UPIOT 停复机回调处理失败: %s", exc, exc_info=True)

    return PlainTextResponse("success")
