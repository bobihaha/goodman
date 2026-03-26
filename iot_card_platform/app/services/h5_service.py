"""
H5 自助服务
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.iot_card_crud import iot_card_crud
from app.crud.sys_user_crud import sys_user_crud
from app.db.models.iot_card import CardH5RemarkLogModel, IotCardModel
from app.db.models.sys_user import UserLevel
from app.schemas.h5 import H5PortalConfig, H5CardActionFlags
from app.services.iot_card_service import iot_card_service
from app.utils.const import sanitize_text
from app.utils.exceptions import BusinessException


class H5Service:
    @staticmethod
    def _mask_iccid(iccid: str) -> str:
        if len(iccid) <= 8:
            return iccid
        return f"{iccid[:4]}****{iccid[-4:]}"

    @staticmethod
    def _mask_msisdn(msisdn: Optional[str]) -> Optional[str]:
        if not msisdn or len(msisdn) < 7:
            return msisdn
        return f"{msisdn[:3]}****{msisdn[-4:]}"

    @staticmethod
    def _is_enabled(user) -> bool:
        return bool(user.h5_enabled) and (user.h5_status or "enabled") == "enabled"

    @staticmethod
    def _build_portal_config(user) -> H5PortalConfig:
        return H5PortalConfig(
            user_id=user.id,
            user_name=user.name,
            title=user.h5_title or f"{user.name}自助服务",
            logo=user.h5_logo,
            banner=user.h5_banner,
            notice=user.h5_notice,
            contact_phone=user.h5_contact_phone,
            contact_wechat=user.h5_contact_wechat,
            theme=user.h5_theme,
            allow_suspend=bool(user.h5_allow_suspend),
            allow_resume=bool(user.h5_allow_resume),
            allow_remark=bool(user.h5_allow_remark),
            require_verify=bool(user.h5_require_verify),
            status=user.h5_status or "enabled"
        )

    async def _get_h5_user(self, db: AsyncSession, slug: str):
        user = await sys_user_crud.get_by_h5_slug(db, slug)
        if not user or user.user_level == UserLevel.SUPER_ADMIN.value:
            raise BusinessException(code=404, msg="H5地址不存在")
        if not self._is_enabled(user):
            raise BusinessException(code=403, msg="该H5地址已停用")
        return user

    async def get_config(self, db: AsyncSession, slug: str) -> H5PortalConfig:
        user = await self._get_h5_user(db, slug)
        return self._build_portal_config(user)

    async def query_cards(self, db: AsyncSession, slug: str, keyword: str) -> dict:
        user = await self._get_h5_user(db, slug)
        normalized = keyword.strip()
        if not normalized:
            raise BusinessException(code=400, msg="请输入卡号或ICCID")

        items = await iot_card_crud.search(db, normalized, user_id=user.id, limit=20)
        if not items:
            return {"match_type": "none", "items": []}

        if len(items) == 1:
            detail = await self.get_card_detail(db, slug, items[0].id)
            return {"match_type": "exact" if len(normalized) > 6 else "fuzzy_single", "items": [detail]}

        candidates = [
            {
                "id": item.id,
                "iccid_masked": self._mask_iccid(item.iccid),
                "msisdn_masked": self._mask_msisdn(item.msisdn),
                "status": item.status.value if item.status else None,
                "status_name": item.to_dict().get("status_name"),
                "spec_name": item.get_spec_name(),
                "activated_at": item.to_dict().get("activated_at"),
                "expired_at": item.to_dict().get("expired_at")
            }
            for item in items
        ]
        return {"match_type": "fuzzy_multiple", "items": candidates}

    async def get_card_detail(self, db: AsyncSession, slug: str, card_id: int) -> dict:
        user = await self._get_h5_user(db, slug)
        card = await iot_card_service.get_card_detail(
            db=db,
            card_id=card_id,
            current_user_id=user.id,
            user_level=user.user_level
        )
        diagnostics = None
        try:
            diagnostics = await iot_card_service.get_card_diagnostics(
                db=db,
                card_id=card_id,
                current_user_id=user.id,
                user_level=user.user_level
            )
        except Exception:
            diagnostics = None

        return {
            "card": card,
            "diagnostics": diagnostics,
            "actions": H5CardActionFlags(
                allow_suspend=bool(user.h5_allow_suspend),
                allow_resume=bool(user.h5_allow_resume),
                allow_remark=bool(user.h5_allow_remark)
            ).model_dump()
        }

    async def suspend_card(
        self,
        db: AsyncSession,
        slug: str,
        card_id: int,
        reason: Optional[str] = None
    ) -> dict:
        user = await self._get_h5_user(db, slug)
        if not user.h5_allow_suspend:
            raise BusinessException(code=403, msg="当前账号H5未开通停机功能")

        card = await iot_card_crud.get_by_id(db, card_id, user_id=user.id)
        if not card:
            raise BusinessException(code=404, msg="卡片不存在")

        result = await iot_card_service.batch_suspend_by_iccids(
            db=db,
            iccids=[card.iccid],
            reason=reason,
            current_user_id=user.id,
            user_level=user.user_level
        )
        return result

    async def resume_card(self, db: AsyncSession, slug: str, card_id: int) -> dict:
        user = await self._get_h5_user(db, slug)
        if not user.h5_allow_resume:
            raise BusinessException(code=403, msg="当前账号H5未开通复机功能")

        card = await iot_card_crud.get_by_id(db, card_id, user_id=user.id)
        if not card:
            raise BusinessException(code=404, msg="卡片不存在")

        result = await iot_card_service.batch_resume_by_iccids(
            db=db,
            iccids=[card.iccid],
            current_user_id=user.id,
            user_level=user.user_level
        )
        return result

    async def update_remark(
        self,
        db: AsyncSession,
        slug: str,
        card_id: int,
        remark: str,
        client_ip: Optional[str] = None,
        operator_name: Optional[str] = None,
        operator_phone: Optional[str] = None
    ) -> dict:
        user = await self._get_h5_user(db, slug)
        if not user.h5_allow_remark:
            raise BusinessException(code=403, msg="当前账号H5未开通备注功能")

        card = await iot_card_crud.get_by_id(db, card_id, user_id=user.id)
        if not card:
            raise BusinessException(code=404, msg="卡片不存在")

        detail = await iot_card_service.get_card_detail(
            db=db,
            card_id=card_id,
            current_user_id=user.id,
            user_level=user.user_level
        )
        old_remark = detail.get("remark")
        sanitized_remark = sanitize_text(remark)
        updated = await iot_card_service.update_remark(
            db=db,
            card_id=card_id,
            remark=sanitized_remark,
            current_user_id=user.id,
            user_level=user.user_level
        )

        db.add(
            CardH5RemarkLogModel(
                user_id=user.id,
                card_id=card.id,
                iccid=card.iccid,
                old_remark=old_remark,
                new_remark=sanitized_remark,
                source="h5",
                operator_name=operator_name,
                operator_phone=operator_phone,
                client_ip=client_ip
            )
        )
        await db.commit()
        return updated


h5_service = H5Service()
