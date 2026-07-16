"""渠道伙伴独立认证依赖。"""
from typing import Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models.channel import ChannelPartnerModel
from app.services.auth_service import AuthService
from app.utils.exceptions import AuthException, BusinessException


channel_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/channels/auth/login",
    auto_error=False,
)


async def get_current_channel(
    token: Optional[str] = Depends(channel_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> ChannelPartnerModel:
    if not token:
        raise AuthException()
    payload = AuthService.verify_token(token)
    if payload.get("principal_type") != "channel":
        raise AuthException()
    channel_id = payload.get("sub")
    if not channel_id:
        raise AuthException()
    result = await db.execute(
        select(ChannelPartnerModel).where(
            ChannelPartnerModel.id == int(channel_id),
            ChannelPartnerModel.is_deleted == 0,
        )
    )
    partner = result.scalar_one_or_none()
    if not partner:
        raise AuthException()
    if partner.status != "enable":
        raise BusinessException(code=403, msg="渠道账号已停用")
    return partner
