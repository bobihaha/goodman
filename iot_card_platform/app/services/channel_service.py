"""渠道伙伴、客户归属和推广积分服务。"""
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import secrets
from typing import Optional

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.sys_user_crud import sys_user_crud
from app.db.models.channel import (
    ChannelCommissionSettingModel,
    ChannelCustomerRelationModel,
    ChannelPartnerModel,
    ChannelPointLedgerModel,
    RenewalOrderModel,
)
from app.db.models.sys_user import SysUserModel, UserLevel, UserStatus
from app.schemas.channel import ChannelPartnerCreate, ChannelPartnerUpdate
from app.services.auth_service import AuthService
from app.services.sys_user_service import sys_user_service
from app.utils.const import validate_password
from app.utils.exceptions import BusinessException
from app.utils.timezone import beijing_now, format_china_datetime


TWOPLACES = Decimal("0.01")
FOURPLACES = Decimal("0.0001")


def _decimal(value, places: Decimal = FOURPLACES) -> Decimal:
    return Decimal(str(value or 0)).quantize(places, rounding=ROUND_HALF_UP)


class ChannelService:
    async def _get_settings(self, db: AsyncSession) -> ChannelCommissionSettingModel:
        result = await db.execute(
            select(ChannelCommissionSettingModel).where(
                ChannelCommissionSettingModel.is_deleted == 0
            ).order_by(ChannelCommissionSettingModel.id.asc()).limit(1)
        )
        settings = result.scalar_one_or_none()
        if settings:
            return settings
        settings = ChannelCommissionSettingModel(
            default_stock_out_rate=Decimal("0"),
            default_renewal_rate=Decimal("0"),
        )
        db.add(settings)
        await db.flush()
        return settings

    async def get_settings(self, db: AsyncSession) -> dict:
        settings = await self._get_settings(db)
        return {
            "default_stock_out_rate": float(settings.default_stock_out_rate or 0),
            "default_renewal_rate": float(settings.default_renewal_rate or 0),
        }

    async def update_settings(
        self,
        db: AsyncSession,
        default_stock_out_rate: float,
        default_renewal_rate: float,
        operator_id: int,
    ) -> dict:
        settings = await self._get_settings(db)
        settings.default_stock_out_rate = _decimal(default_stock_out_rate)
        settings.default_renewal_rate = _decimal(default_renewal_rate)
        settings.updated_by = operator_id
        await db.flush()
        return await self.get_settings(db)

    async def _unique_slug(self, db: AsyncSession) -> str:
        for _ in range(10):
            slug = secrets.token_urlsafe(8).replace("-", "").replace("_", "")[:12]
            exists = await db.scalar(
                select(ChannelPartnerModel.id).where(ChannelPartnerModel.h5_slug == slug)
            )
            if not exists:
                return slug
        raise BusinessException(code=500, msg="生成渠道H5地址失败，请重试")

    @staticmethod
    def _partner_dict(partner: ChannelPartnerModel, defaults: dict, customer_count: int = 0) -> dict:
        stock_rate = (
            partner.stock_out_rate_override
            if partner.stock_out_rate_override is not None
            else defaults["default_stock_out_rate"]
        )
        renewal_rate = (
            partner.renewal_rate_override
            if partner.renewal_rate_override is not None
            else defaults["default_renewal_rate"]
        )
        return {
            "id": partner.id,
            "name": partner.name,
            "contact_name": partner.contact_name,
            "phone": partner.phone,
            "account": partner.account,
            "h5_slug": partner.h5_slug,
            "h5_path": f"/channel/register/{partner.h5_slug}",
            "registration_enabled": bool(partner.registration_enabled),
            "status": partner.status,
            "stock_out_rate_override": float(partner.stock_out_rate_override) if partner.stock_out_rate_override is not None else None,
            "renewal_rate_override": float(partner.renewal_rate_override) if partner.renewal_rate_override is not None else None,
            "effective_stock_out_rate": float(stock_rate or 0),
            "effective_renewal_rate": float(renewal_rate or 0),
            "customer_count": customer_count,
            "last_login_at": format_china_datetime(partner.last_login_at),
            "remark": partner.remark,
            "created_at": format_china_datetime(partner.created_at),
        }

    async def create_partner(
        self,
        db: AsyncSession,
        payload: ChannelPartnerCreate,
        operator_id: int,
    ) -> dict:
        if not validate_password(payload.password):
            raise BusinessException(code=400, msg="密码必须包含大小写字母和数字，长度8-20位")
        duplicate = await db.execute(
            select(ChannelPartnerModel.id).where(
                or_(
                    ChannelPartnerModel.account == payload.account,
                    ChannelPartnerModel.phone == payload.phone,
                ),
            )
        )
        if duplicate.scalar_one_or_none():
            raise BusinessException(code=400, msg="渠道账号或手机号已存在")
        partner = ChannelPartnerModel(
            name=payload.name,
            contact_name=payload.contact_name,
            phone=payload.phone,
            account=payload.account,
            password=AuthService.hash_password(payload.password),
            h5_slug=await self._unique_slug(db),
            registration_enabled=int(payload.registration_enabled),
            status="enable",
            stock_out_rate_override=_decimal(payload.stock_out_rate_override) if payload.stock_out_rate_override is not None else None,
            renewal_rate_override=_decimal(payload.renewal_rate_override) if payload.renewal_rate_override is not None else None,
            created_by=operator_id,
            remark=payload.remark,
        )
        db.add(partner)
        await db.flush()
        defaults = await self.get_settings(db)
        await db.refresh(partner, attribute_names=["created_at"])
        return self._partner_dict(partner, defaults)

    async def update_partner(
        self,
        db: AsyncSession,
        partner_id: int,
        payload: ChannelPartnerUpdate,
    ) -> dict:
        partner = await self.get_partner(db, partner_id)
        values = payload.model_dump(exclude_unset=True)
        if "phone" in values and values["phone"] != partner.phone:
            exists = await db.scalar(
                select(ChannelPartnerModel.id).where(
                    ChannelPartnerModel.phone == values["phone"],
                    ChannelPartnerModel.id != partner.id,
                )
            )
            if exists:
                raise BusinessException(code=400, msg="渠道手机号已存在")
        for rate_field in ("stock_out_rate_override", "renewal_rate_override"):
            if rate_field in values and values[rate_field] is not None:
                values[rate_field] = _decimal(values[rate_field])
        for required_field in ("name", "contact_name", "phone", "status"):
            if required_field in values and values[required_field] is None:
                values.pop(required_field)
        if "registration_enabled" in values:
            values["registration_enabled"] = int(values["registration_enabled"])
        for key, value in values.items():
            setattr(partner, key, value)
        await db.flush()
        customer_count = await db.scalar(
            select(func.count(ChannelCustomerRelationModel.id)).where(
                ChannelCustomerRelationModel.channel_id == partner.id,
                ChannelCustomerRelationModel.status == "active",
                ChannelCustomerRelationModel.is_deleted == 0,
            )
        )
        return self._partner_dict(partner, await self.get_settings(db), customer_count or 0)

    async def reset_password(self, db: AsyncSession, partner_id: int, password: str) -> None:
        if not validate_password(password):
            raise BusinessException(code=400, msg="密码必须包含大小写字母和数字，长度8-20位")
        partner = await self.get_partner(db, partner_id)
        partner.password = AuthService.hash_password(password)
        await db.flush()

    async def get_partner(self, db: AsyncSession, partner_id: int) -> ChannelPartnerModel:
        result = await db.execute(
            select(ChannelPartnerModel).where(
                ChannelPartnerModel.id == partner_id,
                ChannelPartnerModel.is_deleted == 0,
            )
        )
        partner = result.scalar_one_or_none()
        if not partner:
            raise BusinessException(code=404, msg="渠道不存在")
        return partner

    async def list_partners(self, db: AsyncSession, keyword: Optional[str], status: Optional[str]) -> list[dict]:
        stmt = select(ChannelPartnerModel).where(ChannelPartnerModel.is_deleted == 0)
        if keyword:
            term = f"%{keyword.strip()}%"
            stmt = stmt.where(or_(
                ChannelPartnerModel.name.like(term),
                ChannelPartnerModel.contact_name.like(term),
                ChannelPartnerModel.phone.like(term),
                ChannelPartnerModel.account.like(term),
            ))
        if status:
            stmt = stmt.where(ChannelPartnerModel.status == status)
        partners = list((await db.execute(stmt.order_by(ChannelPartnerModel.id.desc()))).scalars().all())
        defaults = await self.get_settings(db)
        items = []
        for partner in partners:
            count = await db.scalar(
                select(func.count(ChannelCustomerRelationModel.id)).where(
                    ChannelCustomerRelationModel.channel_id == partner.id,
                    ChannelCustomerRelationModel.status == "active",
                    ChannelCustomerRelationModel.is_deleted == 0,
                )
            )
            items.append(self._partner_dict(partner, defaults, count or 0))
        return items

    async def login(self, db: AsyncSession, account: str, password: str) -> dict:
        result = await db.execute(
            select(ChannelPartnerModel).where(
                ChannelPartnerModel.account == account,
                ChannelPartnerModel.is_deleted == 0,
            )
        )
        partner = result.scalar_one_or_none()
        if not partner or not AuthService.verify_password(password, partner.password):
            raise BusinessException(code=400, msg="账号或密码错误")
        if partner.status != "enable":
            raise BusinessException(code=403, msg="渠道账号已停用")
        token = AuthService.create_access_token({
            "sub": str(partner.id),
            "account": partner.account,
            "principal_type": "channel",
        })
        partner.last_login_at = beijing_now()
        await db.flush()
        return {
            "access_token": token,
            "token_type": "Bearer",
            "partner": {
                "id": partner.id,
                "name": partner.name,
                "contact_name": partner.contact_name,
                "account": partner.account,
            },
        }

    async def public_config(self, db: AsyncSession, slug: str) -> dict:
        result = await db.execute(
            select(ChannelPartnerModel).where(
                ChannelPartnerModel.h5_slug == slug,
                ChannelPartnerModel.is_deleted == 0,
            )
        )
        partner = result.scalar_one_or_none()
        if not partner or partner.status != "enable" or not partner.registration_enabled:
            raise BusinessException(code=404, msg="该渠道报备页面不存在或已停用")
        return {"channel_name": partner.name, "registration_enabled": True}

    async def register_customer(
        self,
        db: AsyncSession,
        slug: str,
        customer_name: str,
        customer_phone: str,
        customer_profile: str,
        client_ip: Optional[str],
        user_agent: Optional[str],
    ) -> dict:
        partner_result = await db.execute(
            select(ChannelPartnerModel).where(
                ChannelPartnerModel.h5_slug == slug,
                ChannelPartnerModel.status == "enable",
                ChannelPartnerModel.registration_enabled == 1,
                ChannelPartnerModel.is_deleted == 0,
            )
        )
        partner = partner_result.scalar_one_or_none()
        if not partner:
            raise BusinessException(code=404, msg="该渠道报备页面不存在或已停用")

        relation_exists = await db.scalar(
            select(ChannelCustomerRelationModel.id).where(
                ChannelCustomerRelationModel.customer_phone == customer_phone,
                ChannelCustomerRelationModel.is_deleted == 0,
            )
        )
        if relation_exists:
            raise BusinessException(code=409, msg="该手机号已完成渠道登记，请勿重复提交")
        user_exists = await db.scalar(
            select(SysUserModel.id).where(
                SysUserModel.phone == customer_phone,
                SysUserModel.is_deleted == 0,
            )
        )
        if user_exists:
            raise BusinessException(code=409, msg="该手机号已是平台客户，请联系平台确认渠道归属")

        admin_result = await db.execute(
            select(SysUserModel).where(
                SysUserModel.user_level == UserLevel.SUPER_ADMIN.value,
                SysUserModel.status == UserStatus.enable,
                SysUserModel.is_deleted == 0,
            ).order_by(SysUserModel.id.asc()).limit(1)
        )
        admin = admin_result.scalar_one_or_none()
        if not admin:
            raise BusinessException(code=500, msg="平台暂未配置可用超级管理员")

        account = f"c{customer_phone}"
        if await sys_user_crud.check_account_exists(db, account):
            account = f"c{customer_phone}_{secrets.token_hex(2)}"
        generated_password = f"A{secrets.token_urlsafe(12)}a1"
        user = SysUserModel(
            parent_id=admin.id,
            user_level=UserLevel.USER.value,
            name=customer_name,
            account=account,
            password=AuthService.hash_password(generated_password),
            phone=customer_phone,
            alert_notify={"sms": True, "email": True},
            quota={
                "max_cards": 100,
                "max_sub_users": 5,
                "pool_stop_threshold": 100,
                "account_balance": 0,
                "balance_alert_threshold": 1000,
            },
            remark=f"渠道H5自动创建，来源渠道：{partner.name}",
            status=UserStatus.enable,
            created_by=admin.id,
        )
        db.add(user)
        await db.flush()

        from app.db.models.sys_log import SysOperationLogModel
        from app.db.models.sys_menu import SysMenuModel, SysUserMenuModel

        menu_ids = list((await db.execute(
            select(SysMenuModel.id).where(
                SysMenuModel.code.in_(sys_user_service.DEFAULT_USER_MENU_CODES),
                SysMenuModel.is_deleted == 0,
            )
        )).scalars().all())
        db.add_all([
            *(SysUserMenuModel(user_id=user.id, menu_id=item_id) for item_id in menu_ids),
        ])
        user, _ = await sys_user_service._ensure_open_api_credentials(db, user)

        relation = ChannelCustomerRelationModel(
            channel_id=partner.id,
            user_id=user.id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_profile=customer_profile,
            status="active",
            source="channel_h5",
            registered_ip=client_ip,
            registered_user_agent=(user_agent or "")[:500] or None,
            registered_at=beijing_now(),
        )
        db.add_all([
            relation,
            SysOperationLogModel(
                user_id=admin.id,
                user_name=admin.name,
                module="user",
                action="channel_h5_create",
                target_type="user",
                target_id=user.id,
                target_name=user.name,
                detail=f"渠道H5自动创建用户，来源渠道：{partner.name}",
                ip=client_ip,
                is_success=1,
            ),
        ])
        await db.flush()
        return {"success": True, "message": "客户登记成功，平台客户已创建"}

    async def _relation_for_user(
        self, db: AsyncSession, user_id: int
    ) -> Optional[ChannelCustomerRelationModel]:
        result = await db.execute(
            select(ChannelCustomerRelationModel)
            .join(
                ChannelPartnerModel,
                ChannelPartnerModel.id == ChannelCustomerRelationModel.channel_id,
            )
            .where(
                ChannelCustomerRelationModel.user_id == user_id,
                ChannelCustomerRelationModel.status == "active",
                ChannelCustomerRelationModel.is_deleted == 0,
                ChannelPartnerModel.status == "enable",
                ChannelPartnerModel.is_deleted == 0,
            )
        )
        return result.scalar_one_or_none()

    async def _rate_for(self, db: AsyncSession, channel_id: int, order_type: str) -> Decimal:
        partner = await self.get_partner(db, channel_id)
        settings = await self._get_settings(db)
        if order_type == "stock_out":
            value = partner.stock_out_rate_override
            return _decimal(value if value is not None else settings.default_stock_out_rate)
        value = partner.renewal_rate_override
        return _decimal(value if value is not None else settings.default_renewal_rate)

    async def create_stock_out_points(
        self,
        db: AsyncSession,
        source_order_id: int,
        source_order_no: str,
        user_id: int,
        cards: list[dict],
        unit_price_cents: int,
    ) -> int:
        relation = await self._relation_for_user(db, user_id)
        if not relation:
            return 0
        rate = await self._rate_for(db, relation.channel_id, "stock_out")
        base_amount = (Decimal(unit_price_cents) / Decimal("100")).quantize(TWOPLACES)
        points = (base_amount * rate / Decimal("100")).quantize(FOURPLACES, rounding=ROUND_HALF_UP)
        created = 0
        for card in cards:
            exists = await db.scalar(
                select(ChannelPointLedgerModel.id).where(
                    ChannelPointLedgerModel.entry_type == "credit",
                    ChannelPointLedgerModel.order_type == "stock_out",
                    ChannelPointLedgerModel.source_order_id == source_order_id,
                    ChannelPointLedgerModel.card_id == card["card_id"],
                )
            )
            if exists:
                continue
            db.add(ChannelPointLedgerModel(
                channel_id=relation.channel_id,
                relation_id=relation.id,
                user_id=relation.user_id,
                customer_name=relation.customer_name,
                customer_phone=relation.customer_phone,
                entry_type="credit",
                order_type="stock_out",
                source_order_id=source_order_id,
                source_order_no=source_order_no,
                card_id=card["card_id"],
                iccid=card["iccid"],
                base_amount=base_amount,
                rate_percent=rate,
                points=points,
                status="pending",
            ))
            created += 1
        if created:
            await db.flush()
        return created

    async def create_renewal_order_and_points(
        self,
        db: AsyncSession,
        user_id: int,
        card_id: int,
        iccid: str,
        renew_months: int,
        unit_price: Decimal,
        total_amount: Decimal,
        operator_id: int,
    ) -> RenewalOrderModel:
        now = beijing_now()
        order = RenewalOrderModel(
            order_no=f"RN{now.strftime('%Y%m%d%H%M%S')}{secrets.randbelow(100000):05d}",
            user_id=user_id,
            card_id=card_id,
            iccid=iccid,
            renew_months=renew_months,
            unit_price=_decimal(unit_price, TWOPLACES),
            total_amount=_decimal(total_amount, TWOPLACES),
            status="completed",
            completed_at=now,
            operator_id=operator_id,
        )
        db.add(order)
        await db.flush()

        relation = await self._relation_for_user(db, user_id)
        if not relation:
            return order
        rate = await self._rate_for(db, relation.channel_id, "renewal")
        points = (order.total_amount * rate / Decimal("100")).quantize(FOURPLACES, rounding=ROUND_HALF_UP)
        db.add(ChannelPointLedgerModel(
            channel_id=relation.channel_id,
            relation_id=relation.id,
            user_id=relation.user_id,
            customer_name=relation.customer_name,
            customer_phone=relation.customer_phone,
            entry_type="credit",
            order_type="renewal",
            source_order_id=order.id,
            source_order_no=order.order_no,
            card_id=card_id,
            iccid=iccid,
            base_amount=order.total_amount,
            rate_percent=rate,
            points=points,
            status="pending",
        ))
        await db.flush()
        return order

    async def reverse_stock_out_points(
        self,
        db: AsyncSession,
        recycled_cards: list[dict],
    ) -> int:
        created = 0
        for card in recycled_cards:
            original_result = await db.execute(
                select(ChannelPointLedgerModel).where(
                    ChannelPointLedgerModel.entry_type == "credit",
                    ChannelPointLedgerModel.order_type == "stock_out",
                    ChannelPointLedgerModel.card_id == card["card_id"],
                    ChannelPointLedgerModel.user_id == card["original_user_id"],
                    ChannelPointLedgerModel.is_deleted == 0,
                ).order_by(ChannelPointLedgerModel.id.desc()).limit(1)
            )
            original = original_result.scalar_one_or_none()
            if not original:
                continue
            exists = await db.scalar(
                select(ChannelPointLedgerModel.id).where(
                    ChannelPointLedgerModel.entry_type == "reversal",
                    ChannelPointLedgerModel.order_type == original.order_type,
                    ChannelPointLedgerModel.source_order_id == original.source_order_id,
                    ChannelPointLedgerModel.card_id == original.card_id,
                )
            )
            if exists:
                continue
            db.add(ChannelPointLedgerModel(
                channel_id=original.channel_id,
                relation_id=original.relation_id,
                user_id=original.user_id,
                customer_name=original.customer_name,
                customer_phone=original.customer_phone,
                entry_type="reversal",
                order_type=original.order_type,
                source_order_id=original.source_order_id,
                source_order_no=original.source_order_no,
                card_id=original.card_id,
                iccid=original.iccid,
                base_amount=-original.base_amount,
                rate_percent=original.rate_percent,
                points=-original.points,
                status="pending",
                related_entry_id=original.id,
            ))
            created += 1
        if created:
            await db.flush()
        return created

    @staticmethod
    def _point_dict(item: ChannelPointLedgerModel, channel_name: Optional[str] = None) -> dict:
        return {
            "id": item.id,
            "channel_id": item.channel_id,
            "channel_name": channel_name,
            "customer_name": item.customer_name,
            "customer_phone": item.customer_phone,
            "entry_type": item.entry_type,
            "order_type": item.order_type,
            "source_order_no": item.source_order_no,
            "card_id": item.card_id,
            "iccid": item.iccid,
            "base_amount": float(item.base_amount),
            "rate_percent": float(item.rate_percent),
            "points": float(item.points),
            "status": item.status,
            "settled_at": format_china_datetime(item.settled_at),
            "created_at": format_china_datetime(item.created_at),
        }

    async def list_points(
        self,
        db: AsyncSession,
        channel_id: Optional[int],
        keyword: Optional[str],
        order_type: Optional[str],
        status: Optional[str],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        page: int,
        page_size: int,
        include_channel_name: bool = False,
    ) -> dict:
        conditions = [ChannelPointLedgerModel.is_deleted == 0]
        if channel_id:
            conditions.append(ChannelPointLedgerModel.channel_id == channel_id)
        if keyword:
            term = f"%{keyword.strip()}%"
            conditions.append(or_(
                ChannelPointLedgerModel.customer_name.like(term),
                ChannelPointLedgerModel.customer_phone.like(term),
                ChannelPointLedgerModel.source_order_no.like(term),
                ChannelPointLedgerModel.iccid.like(term),
            ))
        if order_type:
            conditions.append(ChannelPointLedgerModel.order_type == order_type)
        if status:
            conditions.append(ChannelPointLedgerModel.status == status)
        if start_time:
            conditions.append(ChannelPointLedgerModel.created_at >= start_time)
        if end_time:
            conditions.append(ChannelPointLedgerModel.created_at <= end_time)
        total = await db.scalar(select(func.count(ChannelPointLedgerModel.id)).where(*conditions)) or 0
        result = await db.execute(
            select(ChannelPointLedgerModel)
            .where(*conditions)
            .order_by(ChannelPointLedgerModel.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = list(result.scalars().all())
        channel_map = {}
        if include_channel_name and rows:
            ids = {row.channel_id for row in rows}
            partners = (await db.execute(
                select(ChannelPartnerModel).where(ChannelPartnerModel.id.in_(ids))
            )).scalars().all()
            channel_map = {partner.id: partner.name for partner in partners}
        return {
            "items": [self._point_dict(row, channel_map.get(row.channel_id)) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def summary(self, db: AsyncSession, channel_id: int) -> dict:
        base = [
            ChannelPointLedgerModel.channel_id == channel_id,
            ChannelPointLedgerModel.is_deleted == 0,
        ]
        total_points = await db.scalar(
            select(func.coalesce(func.sum(ChannelPointLedgerModel.points), 0)).where(*base)
        )
        pending_points = await db.scalar(
            select(func.coalesce(func.sum(ChannelPointLedgerModel.points), 0)).where(
                *base, ChannelPointLedgerModel.status == "pending"
            )
        )
        settled_points = await db.scalar(
            select(func.coalesce(func.sum(ChannelPointLedgerModel.points), 0)).where(
                *base, ChannelPointLedgerModel.status == "settled"
            )
        )
        month_start = beijing_now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_points = await db.scalar(
            select(func.coalesce(func.sum(ChannelPointLedgerModel.points), 0)).where(
                *base, ChannelPointLedgerModel.created_at >= month_start
            )
        )
        customer_count = await db.scalar(
            select(func.count(ChannelCustomerRelationModel.id)).where(
                ChannelCustomerRelationModel.channel_id == channel_id,
                ChannelCustomerRelationModel.status == "active",
                ChannelCustomerRelationModel.is_deleted == 0,
            )
        )
        return {
            "customer_count": customer_count or 0,
            "total_points": float(total_points or 0),
            "pending_points": float(pending_points or 0),
            "settled_points": float(settled_points or 0),
            "remaining_points": float(pending_points or 0),
            "consumed_points": float(settled_points or 0),
            "month_points": float(month_points or 0),
        }

    async def list_customers(
        self,
        db: AsyncSession,
        channel_id: int,
        keyword: Optional[str],
        page: int,
        page_size: int,
    ) -> dict:
        relation = ChannelCustomerRelationModel
        ledger = ChannelPointLedgerModel
        conditions = [
            relation.channel_id == channel_id,
            relation.status == "active",
            relation.is_deleted == 0,
        ]
        if keyword:
            term = f"%{keyword.strip()}%"
            conditions.append(or_(
                relation.customer_name.like(term),
                relation.customer_phone.like(term),
                relation.customer_profile.like(term),
            ))
        total = await db.scalar(select(func.count(relation.id)).where(*conditions)) or 0
        result = await db.execute(
            select(
                relation.id,
                relation.user_id,
                relation.customer_name,
                relation.customer_phone,
                relation.customer_profile,
                relation.registered_at,
                func.count(ledger.id).label("point_count"),
                func.coalesce(func.sum(ledger.points), 0).label("total_points"),
                func.coalesce(func.sum(case(
                    (ledger.status == "settled", ledger.points), else_=0
                )), 0).label("consumed_points"),
                func.coalesce(func.sum(case(
                    (ledger.status == "pending", ledger.points), else_=0
                )), 0).label("remaining_points"),
            )
            .outerjoin(ledger, and_(
                ledger.relation_id == relation.id,
                ledger.is_deleted == 0,
            ))
            .where(*conditions)
            .group_by(
                relation.id,
                relation.user_id,
                relation.customer_name,
                relation.customer_phone,
                relation.customer_profile,
                relation.registered_at,
            )
            .order_by(relation.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return {
            "items": [{
                "id": row.id,
                "user_id": row.user_id,
                "customer_name": row.customer_name,
                "customer_phone": row.customer_phone,
                "customer_profile": row.customer_profile,
                "registered_at": format_china_datetime(row.registered_at),
                "point_count": row.point_count,
                "total_points": float(row.total_points or 0),
                "consumed_points": float(row.consumed_points or 0),
                "remaining_points": float(row.remaining_points or 0),
            } for row in result.all()],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def settle_points(self, db: AsyncSession, point_ids: list[int], operator_id: int) -> dict:
        result = await db.execute(
            select(ChannelPointLedgerModel).where(
                ChannelPointLedgerModel.id.in_(point_ids),
                ChannelPointLedgerModel.status == "pending",
                ChannelPointLedgerModel.is_deleted == 0,
            ).with_for_update()
        )
        rows = list(result.scalars().all())
        now = beijing_now()
        for row in rows:
            row.status = "settled"
            row.settled_by = operator_id
            row.settled_at = now
        await db.flush()
        return {"settled_count": len(rows)}


channel_service = ChannelService()
