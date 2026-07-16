from decimal import Decimal

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models.channel import (
    ChannelCommissionSettingModel,
    ChannelCustomerRelationModel,
    ChannelPartnerModel,
    ChannelPointLedgerModel,
    RenewalOrderModel,
)
from app.db.models.sys_user import SysUserModel, UserLevel, UserStatus
from app.schemas.auth import CurrentUser
from app.schemas.channel import ChannelPartnerCreate
from app.schemas.sys_user import UserQuery
from app.services.auth_service import AuthService
from app.services.channel_service import channel_service
from app.services.sys_user_service import sys_user_service
from app.utils.exceptions import AuthException
from app.main import app
from tests.conftest import TestSessionLocal


async def _seed_channel_context(db, *, stock_rate=Decimal("5"), renewal_rate=Decimal("3")):
    partner = ChannelPartnerModel(
        name="测试渠道",
        contact_name="渠道联系人",
        phone="13900000001",
        account="channel_test",
        password=AuthService.hash_password("ChannelA1"),
        h5_slug="testslug",
        registration_enabled=1,
        status="enable",
    )
    user = SysUserModel(
        parent_id=1,
        user_level=UserLevel.USER.value,
        name="渠道客户",
        account="c13800000001",
        password=AuthService.hash_password("CustomerA1"),
        phone="13800000001",
        status=UserStatus.enable,
    )
    settings = ChannelCommissionSettingModel(
        default_stock_out_rate=stock_rate,
        default_renewal_rate=renewal_rate,
    )
    db.add_all([partner, user, settings])
    await db.flush()
    relation = ChannelCustomerRelationModel(
        channel_id=partner.id,
        user_id=user.id,
        customer_name=user.name,
        customer_phone=user.phone,
        customer_profile="4G定位设备，车辆管理场景，预计100台",
        status="active",
        source="channel_h5",
        registered_at=__import__("datetime").datetime.now(),
    )
    db.add(relation)
    await db.flush()
    return partner, user, relation


@pytest.mark.asyncio
async def test_create_partner_refreshes_server_generated_created_at(setup_database, monkeypatch):
    refresh_calls = []
    original_refresh = AsyncSession.refresh

    async def tracked_refresh(self, instance, attribute_names=None, **kwargs):
        refresh_calls.append((instance, attribute_names))
        return await original_refresh(self, instance, attribute_names=attribute_names, **kwargs)

    monkeypatch.setattr(AsyncSession, "refresh", tracked_refresh)
    async with TestSessionLocal() as db:
        created = await channel_service.create_partner(
            db,
            ChannelPartnerCreate(
                name="新增渠道",
                contact_name="渠道联系人",
                phone="13900000003",
                account="new_channel",
                password="ChannelA1",
                stock_out_rate_override=15,
                renewal_rate_override=10,
            ),
            operator_id=1,
        )

    assert created["created_at"]
    assert len(refresh_calls) == 1
    assert refresh_calls[0][1] == ["created_at"]


@pytest.mark.asyncio
async def test_stock_out_points_are_created_per_card_with_rate_snapshot(setup_database):
    async with TestSessionLocal() as db:
        partner, user, _ = await _seed_channel_context(db)

        created = await channel_service.create_stock_out_points(
            db=db,
            source_order_id=88,
            source_order_no="OUT202607150001",
            user_id=user.id,
            cards=[
                {"card_id": 101, "iccid": "89860000000000000101"},
                {"card_id": 102, "iccid": "89860000000000000102"},
            ],
            unit_price_cents=10000,
        )
        await db.commit()

        rows = list((await db.execute(
            select(ChannelPointLedgerModel).order_by(ChannelPointLedgerModel.card_id)
        )).scalars().all())
        assert created == 2
        assert [row.points for row in rows] == [Decimal("5.0000"), Decimal("5.0000")]
        assert all(row.base_amount == Decimal("100.00") for row in rows)
        assert all(row.rate_percent == Decimal("5.0000") for row in rows)
        assert all(row.channel_id == partner.id for row in rows)


@pytest.mark.asyncio
async def test_stock_out_points_are_idempotent(setup_database):
    async with TestSessionLocal() as db:
        _, user, _ = await _seed_channel_context(db)
        payload = dict(
            db=db,
            source_order_id=89,
            source_order_no="OUT202607150002",
            user_id=user.id,
            cards=[{"card_id": 103, "iccid": "89860000000000000103"}],
            unit_price_cents=5000,
        )
        assert await channel_service.create_stock_out_points(**payload) == 1
        assert await channel_service.create_stock_out_points(**payload) == 0


@pytest.mark.asyncio
async def test_renewal_creates_structured_order_and_points(setup_database):
    async with TestSessionLocal() as db:
        _, user, _ = await _seed_channel_context(db)
        order = await channel_service.create_renewal_order_and_points(
            db=db,
            user_id=user.id,
            card_id=201,
            iccid="89860000000000000201",
            renew_months=3,
            unit_price=Decimal("20"),
            total_amount=Decimal("60"),
            operator_id=user.id,
        )
        await db.commit()

        saved_order = await db.scalar(select(RenewalOrderModel).where(RenewalOrderModel.id == order.id))
        point = await db.scalar(select(ChannelPointLedgerModel).where(
            ChannelPointLedgerModel.order_type == "renewal"
        ))
        assert saved_order.order_no.startswith("RN")
        assert saved_order.total_amount == Decimal("60.00")
        assert point.source_order_no == saved_order.order_no
        assert point.points == Decimal("1.8000")


@pytest.mark.asyncio
async def test_recycle_creates_negative_reversal_once(setup_database):
    async with TestSessionLocal() as db:
        _, user, _ = await _seed_channel_context(db)
        await channel_service.create_stock_out_points(
            db=db,
            source_order_id=90,
            source_order_no="OUT202607150003",
            user_id=user.id,
            cards=[{"card_id": 104, "iccid": "89860000000000000104"}],
            unit_price_cents=8000,
        )
        recycled = [{"card_id": 104, "iccid": "89860000000000000104", "original_user_id": user.id}]
        assert await channel_service.reverse_stock_out_points(db, recycled) == 1
        assert await channel_service.reverse_stock_out_points(db, recycled) == 0

        rows = list((await db.execute(
            select(ChannelPointLedgerModel).order_by(ChannelPointLedgerModel.id)
        )).scalars().all())
        assert rows[0].points == Decimal("4.0000")
        assert rows[1].points == Decimal("-4.0000")
        assert rows[1].related_entry_id == rows[0].id


def test_channel_token_carries_separate_principal_type():
    token = AuthService.create_access_token({"sub": "1", "principal_type": "channel"})
    payload = AuthService.verify_token(token)
    assert payload["principal_type"] == "channel"


@pytest.mark.asyncio
async def test_channel_token_cannot_be_used_as_platform_user(setup_database):
    async with TestSessionLocal() as db:
        db.add(SysUserModel(
            id=1,
            user_level=UserLevel.SUPER_ADMIN.value,
            name="平台管理员",
            account="admin_test",
            password=AuthService.hash_password("AdminTestA1"),
            status=UserStatus.enable,
        ))
        await db.commit()
        token = AuthService.create_access_token({
            "sub": "1",
            "principal_type": "channel",
        })
        with pytest.raises(AuthException):
            await AuthService.get_current_user(db, token)


@pytest.mark.asyncio
async def test_public_h5_registration_creates_platform_user_and_locks_phone(async_client):
    async def committing_get_db():
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = committing_get_db
    async with TestSessionLocal() as db:
        admin = SysUserModel(
            user_level=UserLevel.SUPER_ADMIN.value,
            name="平台管理员",
            account="admin_channel",
            password=AuthService.hash_password("AdminTestA1"),
            status=UserStatus.enable,
        )
        partner = ChannelPartnerModel(
            name="公开报备渠道",
            contact_name="渠道联系人",
            phone="13900000002",
            account="public_channel",
            password=AuthService.hash_password("ChannelA1"),
            h5_slug="publicslug",
            registration_enabled=1,
            status="enable",
        )
        db.add_all([admin, partner])
        await db.commit()
        await db.execute(text("DROP TABLE IF EXISTS sys_user_permissions"))
        await db.execute(text("DROP TABLE IF EXISTS sys_permissions"))
        await db.commit()

    payload = {
        "customer_name": "新客户",
        "customer_phone": "13800000002",
        "customer_profile": "4G工业网关，智慧工厂数据采集，预计首批80台",
        "consent": True,
    }
    missing_profile = await async_client.post(
        "/api/v1/channels/public/publicslug/register",
        json={key: value for key, value in payload.items() if key != "customer_profile"},
    )
    assert missing_profile.status_code == 422

    response = await async_client.post("/api/v1/channels/public/publicslug/register", json=payload)
    assert response.json()["code"] == 200

    duplicate = await async_client.post("/api/v1/channels/public/publicslug/register", json=payload)
    assert duplicate.json()["code"] == 409

    async with TestSessionLocal() as db:
        user = await db.scalar(select(SysUserModel).where(SysUserModel.phone == payload["customer_phone"]))
        relation = await db.scalar(select(ChannelCustomerRelationModel).where(
            ChannelCustomerRelationModel.customer_phone == payload["customer_phone"]
        ))
        assert user is not None
        assert user.user_level == UserLevel.USER.value
        assert relation.user_id == user.id
        assert relation.customer_profile == payload["customer_profile"]


@pytest.mark.asyncio
async def test_channel_customer_list_aggregates_consumed_and_remaining_points(setup_database):
    async with TestSessionLocal() as db:
        _, user, relation = await _seed_channel_context(db)
        await channel_service.create_stock_out_points(
            db=db,
            source_order_id=201,
            source_order_no="OUT202607150201",
            user_id=user.id,
            cards=[{"card_id": 301, "iccid": "89860000000000000301"}],
            unit_price_cents=10000,
        )
        await channel_service.create_stock_out_points(
            db=db,
            source_order_id=202,
            source_order_no="OUT202607150202",
            user_id=user.id,
            cards=[{"card_id": 302, "iccid": "89860000000000000302"}],
            unit_price_cents=20000,
        )
        settled = await db.scalar(select(ChannelPointLedgerModel).where(
            ChannelPointLedgerModel.source_order_id == 201
        ))
        settled.status = "settled"
        await db.flush()

        result = await channel_service.list_customers(db, relation.channel_id, "定位设备", 1, 20)

    assert result["total"] == 1
    customer = result["items"][0]
    assert customer["customer_profile"] == relation.customer_profile
    assert customer["point_count"] == 2
    assert customer["total_points"] == 15
    assert customer["consumed_points"] == 5
    assert customer["remaining_points"] == 10


@pytest.mark.asyncio
async def test_super_admin_user_list_shows_and_filters_recommended_channel(setup_database):
    async with TestSessionLocal() as db:
        partner, referred_user, _ = await _seed_channel_context(db)
        ordinary_user = SysUserModel(
            parent_id=1,
            user_level=UserLevel.USER.value,
            name="普通客户",
            account="ordinary_customer",
            password=AuthService.hash_password("CustomerA1"),
            phone="13800000003",
            status=UserStatus.enable,
        )
        db.add(ordinary_user)
        await db.flush()
        operator = CurrentUser(
            id=1,
            user_level=UserLevel.SUPER_ADMIN.value,
            name="平台管理员",
            account="admin",
            status="enable",
        )

        users, total = await sys_user_service.get_user_list(db, operator, UserQuery(page_size=20))
        channel_by_user = {user.id: user.recommended_channel_name for user in users}
        assert total == 2
        assert channel_by_user[referred_user.id] == partner.name
        assert channel_by_user[ordinary_user.id] is None

        filtered, filtered_total = await sys_user_service.get_user_list(
            db, operator, UserQuery(page_size=20, channel_id=partner.id)
        )
        assert filtered_total == 1
        assert filtered[0].id == referred_user.id


@pytest.mark.asyncio
async def test_first_level_user_sub_user_list_ignores_channel_display_and_filter(setup_database):
    async with TestSessionLocal() as db:
        db.add(SysUserModel(
            user_level=UserLevel.SUPER_ADMIN.value,
            name="平台管理员",
            account="admin_for_child_test",
            password=AuthService.hash_password("AdminTestA1"),
            status=UserStatus.enable,
        ))
        await db.flush()
        partner, parent_user, _ = await _seed_channel_context(db)
        child = SysUserModel(
            parent_id=parent_user.id,
            user_level=UserLevel.SUB_USER.value,
            name="下级用户",
            account="child_customer",
            password=AuthService.hash_password("CustomerA1"),
            phone="13800000004",
            status=UserStatus.enable,
        )
        db.add(child)
        await db.flush()
        operator = CurrentUser(
            id=parent_user.id,
            parent_id=parent_user.parent_id,
            user_level=UserLevel.USER.value,
            name=parent_user.name,
            account=parent_user.account,
            phone=parent_user.phone,
            status="enable",
        )

        users, total = await sys_user_service.get_user_list(
            db, operator, UserQuery(page_size=20, channel_id=partner.id)
        )
        assert total == 1
        assert users[0].id == child.id
        assert users[0].recommended_channel_name is None
