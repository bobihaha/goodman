"""
H5 自助服务
"""
import asyncio
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.iot_card_crud import iot_card_crud
from app.crud.sys_user_crud import sys_user_crud
from app.crud.sys_user_crud_enhanced import SysUserCRUDEnhanced
from app.db.models.suspend import SupplierSuspendOperationModel, SuspendActionType
from app.db.models.iot_card import CardStatus, SuspendType
from app.db.models.iot_card import CardH5RemarkLogModel, IotCardModel
from app.db.models.sys_user import UserLevel
from app.schemas.h5 import H5PortalConfig, H5CardActionFlags, H5CardActionResult
from app.config import settings
from app.clients.supplier_api import get_supplier_client
from app.services.iot_card_service import iot_card_service
from app.services.suspend_service import SuspendActionService
from app.utils.const import sanitize_text
from app.utils.exceptions import BusinessException


class H5Service:
    REFRESH_ACTIVE_STATUSES = {
        CardStatus.activated.value,
        CardStatus.testing.value,
        CardStatus.silent.value,
    }
    REFRESH_PROTECTED_SUSPEND_TYPES = {
        SuspendType.expired,
        SuspendType.card_exceed,
        SuspendType.pool_exceed,
    }

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

    async def _get_accessible_user_ids(self, db: AsyncSession, user) -> Optional[List[int]]:
        if user.user_level == UserLevel.SUPER_ADMIN.value:
            return None

        if user.user_level == UserLevel.SUB_USER.value:
            return [user.id]

        sys_user_crud = SysUserCRUDEnhanced()
        child_ids = await sys_user_crud.get_children_ids(db, user.id)
        return [user.id, *child_ids]

    async def _get_card_in_scope(self, db: AsyncSession, user, card_id: int) -> Optional[IotCardModel]:
        user_ids = await self._get_accessible_user_ids(db, user)
        return await iot_card_crud.get_by_id_in_scope(db, card_id, user_ids)

    async def _has_refresh_history(self, db: AsyncSession, card_id: int) -> bool:
        result = await db.execute(
            select(SupplierSuspendOperationModel.id).where(
                SupplierSuspendOperationModel.card_id == card_id,
                SupplierSuspendOperationModel.action == SuspendActionType.suspend,
                SupplierSuspendOperationModel.request_result.like('%"refresh_resume_pending": true%'),
                SupplierSuspendOperationModel.is_deleted == 0
            ).order_by(SupplierSuspendOperationModel.id.desc()).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def _get_supplier_lifecycle_status(
        self,
        card: IotCardModel,
        supplier
    ) -> str:
        supplier_client = get_supplier_client(
            supplier_id=card.supplier_id,
            api_url=supplier.api_url or "",
            api_key=supplier.api_key or "",
            api_secret=supplier.api_secret or "",
            supplier_code=supplier.code,
            api_config=supplier.api_config,
        )
        lifecycle = await supplier_client.get_card_lifecycle(card.iccid)
        return str(lifecycle.get('status') or '').strip()

    async def _wait_for_supplier_status(
        self,
        db: AsyncSession,
        card: IotCardModel,
        supplier,
        expected_statuses: set[str],
        timeout_seconds: int
    ) -> Optional[str]:
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        latest_status = None

        while True:
            latest_status = await self._get_supplier_lifecycle_status(card, supplier)
            if latest_status:
                SuspendActionService.normalize_card_suspend_state(card, latest_status)
                await db.commit()
                await db.refresh(card)

            if latest_status in expected_statuses:
                return latest_status

            if asyncio.get_running_loop().time() >= deadline:
                return latest_status

            await asyncio.sleep(settings.refresh_status_poll_interval_seconds)

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
        if not user:
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

        user_ids = await self._get_accessible_user_ids(db, user)
        items = await iot_card_crud.search(db, normalized, user_ids=user_ids, limit=20)
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

        card = await self._get_card_in_scope(db, user, card_id)
        if not card:
            raise BusinessException(code=404, msg="卡片不存在")
        if card.status == CardStatus.suspended:
            raise BusinessException(code=400, msg="卡片已停机")
        if card.status not in [CardStatus.activated, CardStatus.testing, CardStatus.silent]:
            raise BusinessException(code=400, msg=f"卡片状态不支持停机: {card.status.value}")

        supplier_map = await SuspendActionService._load_supplier_map(db, [card])
        supplier = supplier_map.get(card.supplier_id)
        api_success, callback_no, _ = await SuspendActionService._call_supplier_suspend(
            db=db,
            card=card,
            supplier=supplier,
            reason=reason,
            operator_id=user.id
        )
        if not api_success:
            raise BusinessException(code=502, msg="供应商停机请求提交失败")

        return H5CardActionResult(
            card_id=card.id,
            iccid=card.iccid,
            action="suspend",
            status="processing",
            callback_no=callback_no,
            message="停机请求已提交，处理中"
        ).model_dump()

    async def resume_card(self, db: AsyncSession, slug: str, card_id: int) -> dict:
        user = await self._get_h5_user(db, slug)
        if not user.h5_allow_resume:
            raise BusinessException(code=403, msg="当前账号H5未开通复机功能")

        card = await self._get_card_in_scope(db, user, card_id)
        if not card:
            raise BusinessException(code=404, msg="卡片不存在")
        if card.status != CardStatus.suspended:
            raise BusinessException(code=400, msg="卡片未处于停机状态")

        can_resume, fail_reason = await SuspendActionService._check_resume_eligibility(
            db=db,
            card=card,
            force=False
        )
        if not can_resume:
            raise BusinessException(code=400, msg=fail_reason or "当前不允许复机")

        supplier_map = await SuspendActionService._load_supplier_map(db, [card])
        supplier = supplier_map.get(card.supplier_id)
        api_success, callback_no, _ = await SuspendActionService._call_supplier_resume(
            db=db,
            card=card,
            supplier=supplier,
            operator_id=user.id
        )
        if not api_success:
            raise BusinessException(code=502, msg="供应商复机请求提交失败")

        return H5CardActionResult(
            card_id=card.id,
            iccid=card.iccid,
            action="resume",
            status="processing",
            callback_no=callback_no,
            message="复机请求已提交，处理中"
        ).model_dump()

    async def refresh_card(self, db: AsyncSession, slug: str, card_id: int) -> dict:
        user = await self._get_h5_user(db, slug)
        if not user.h5_allow_suspend or not user.h5_allow_resume:
            raise BusinessException(code=403, msg="当前账号H5未同时开通停机和复机功能")

        card = await self._get_card_in_scope(db, user, card_id)
        if not card:
            raise BusinessException(code=404, msg="卡片不存在")

        supplier_map = await SuspendActionService._load_supplier_map(db, [card])
        supplier = supplier_map.get(card.supplier_id)
        if not supplier:
            raise BusinessException(code=404, msg="供应商不存在")

        current_supplier_status = await self._get_supplier_lifecycle_status(card, supplier)
        has_refresh_history = await self._has_refresh_history(db, card.id)

        if card.suspend_type in self.REFRESH_PROTECTED_SUSPEND_TYPES:
            raise BusinessException(code=400, msg="当前卡片处于业务停卡状态，不支持刷新重启")
        if card.suspend_type == SuspendType.manual and current_supplier_status == CardStatus.suspended.value and not has_refresh_history:
            raise BusinessException(code=400, msg="当前卡片处于人工停卡状态，不支持刷新重启")

        if current_supplier_status in self.REFRESH_ACTIVE_STATUSES:
            suspend_callback_no = None
            suspend_success, suspend_callback_no, _ = await SuspendActionService._call_supplier_suspend(
                db=db,
                card=card,
                supplier=supplier,
                reason="H5刷新操作-停机",
                operator_id=user.id
            )
            if not suspend_success:
                raise BusinessException(code=502, msg="供应商停机请求提交失败")
            if suspend_callback_no:
                await SuspendActionService.mark_refresh_resume_pending(db, suspend_callback_no)
            return H5CardActionResult(
                card_id=card.id,
                iccid=card.iccid,
                action="refresh",
                status="processing",
                suspend_callback_no=suspend_callback_no,
                message="刷新请求已提交，处理中"
            ).model_dump()

        if current_supplier_status != CardStatus.suspended.value:
            raise BusinessException(code=400, msg=f"当前卡片状态不支持刷新: {current_supplier_status or card.status.value}")

        resume_success, resume_callback_no, _ = await SuspendActionService._call_supplier_resume(
            db=db,
            card=card,
            supplier=supplier,
            operator_id=user.id
        )
        if not resume_success:
            raise BusinessException(code=502, msg="供应商复机请求提交失败")

        return H5CardActionResult(
            card_id=card.id,
            iccid=card.iccid,
            action="refresh",
            status="processing",
            resume_callback_no=resume_callback_no,
            message="刷新请求已提交，处理中"
        ).model_dump()

    async def detect_device_separation(self, db: AsyncSession, slug: str, card_id: int) -> dict:
        user = await self._get_h5_user(db, slug)
        card = await self._get_card_in_scope(db, user, card_id)
        if not card:
            raise BusinessException(code=404, msg="卡片不存在")

        supplier_map = await SuspendActionService._load_supplier_map(db, [card])
        supplier = supplier_map.get(card.supplier_id)
        if not supplier or not card.iccid:
            return H5CardActionResult(
                card_id=card.id,
                iccid=card.iccid or "",
                action="device_separation",
                status="unsupported",
                device_separation_detection_status="unsupported",
                device_separation_detection_message="请联系客服",
                message="请联系客服"
            ).model_dump()

        client = get_supplier_client(
            supplier_id=card.supplier_id,
            api_url=supplier.api_url or "",
            api_key=supplier.api_key or "",
            api_secret=supplier.api_secret or "",
            supplier_code=supplier.code,
            api_config=supplier.api_config,
        )

        try:
            imei_info = await client.get_card_imei_info(card.iccid)
        except Exception:
            imei_info = {
                "detection_status": "unsupported",
                "detection_message": "请联系客服"
            }

        detection_status = (imei_info.get("detection_status") or "").strip() or "unsupported"
        detection_message = (imei_info.get("detection_message") or "").strip()

        if detection_status == "detected":
            final_message = "机卡分离停机"
            final_status = "success"
        elif detection_status == "clear":
            final_message = "未机卡分离"
            final_status = "success"
        elif detection_status == "pending":
            final_message = detection_message or "正在查询..."
            final_status = "processing"
        else:
            detection_status = "unsupported"
            final_message = detection_message or "请联系客服"
            final_status = "unsupported"

        return H5CardActionResult(
            card_id=card.id,
            iccid=card.iccid,
            action="device_separation",
            status=final_status,
            device_separation_detection_status=detection_status,
            device_separation_detection_message=final_message,
            message=final_message
        ).model_dump()

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

        card = await self._get_card_in_scope(db, user, card_id)
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
