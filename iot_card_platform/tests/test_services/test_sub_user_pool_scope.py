from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.api.v1.dashboard import get_pool_stats, get_pools_usage_percent
from app.db.models.base import Base
from app.db.models.iot_card import IotCardModel, CardStatus, CardType, SuspendType
from app.db.models.package import CarrierType, PeriodType
from app.db.models.pool import TrafficPoolModel
from app.db.models.sys_user import SysUserModel
from app.flow_packages import get_current_flow_cycle_month
from app.services.pool_service import pool_service
from app.services.dashboard_service import DashboardService
from app.utils.exceptions import BusinessException


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        month = get_current_flow_cycle_month()
        session.add_all([
            SysUserModel(id=1, name="主账号", account="parent", password="test", user_level=2),
            SysUserModel(id=2, name="子账号", account="child", password="test", user_level=3, parent_id=1),
            SysUserModel(id=3, name="其他子账号", account="sibling", password="test", user_level=3, parent_id=1),
        ])
        for pool_id in (10, 20, 30):
            session.add(TrafficPoolModel(
                id=pool_id, user_id=1, name=f"共享池{pool_id}", carrier=CarrierType.cmcc,
                flow_size=100, period_type=PeriodType.monthly,
                card_count=999, data_total=99999, data_used=99998,
                addon_flow=0, package_flow=99111, alert_threshold_1=80,
                remark="不可展示的备注",
            ))
        def card(card_id, user_id, pool_id, **values):
            fields = dict(
                id=card_id, iccid=f"898600000000{card_id:08d}", user_id=user_id,
                pool_id=pool_id, is_pool_member=1, carrier=CarrierType.cmcc,
                card_type=CardType.pool, flow_size=100, period_type=PeriodType.monthly,
                period_count=1, status=CardStatus.activated, data_total=100, data_used=20,
                data_usage_month=month, data_source_at=datetime.strptime(f"{month}-01", "%Y-%m-%d"),
            )
            fields.update(values)
            return IotCardModel(**fields)
        session.add_all([
            card(1, 2, 10), card(2, 3, 10, data_used=99), card(3, 1, 10),
            card(4, 2, 20, data_used=90), card(5, 3, 30),
            card(6, 2, 10, is_deleted=1), card(7, 2, 10, is_pool_member=0),
            card(8, None, 10),
        ])
        await session.commit()
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_assigned_pool_read_scope_and_no_shared_totals(db):
    with patch("app.crud.pool_crud.pool_crud.update_stats", side_effect=AssertionError("只读接口禁止重算全池")):
        items, total = await pool_service.get_pools(db, 2, 3)
        assert total == 2
        assert [p["id"] for p in items] == [20, 10]
        detail = await pool_service.get_pool(db, 10, 2, 3)
        assert detail["card_count"] == 1
        assert detail["data_total"] == 100
        assert detail["data_used"] == 20
        assert detail["package_flow"] == 100
        assert detail["addon_flow"] == 0
        assert detail["remark"] is None
        assert detail["card_stats"]["activated"] == 1
        assert detail["read_only"] and not detail["can_self_topup"]
        assert not detail["is_alert"]
        cards, count = await pool_service.get_pool_cards(db, 10, 2, 3)
        assert count == 1 and [c["id"] for c in cards] == [1]
        usage = await pool_service.get_pool_usage(db, 10, 2, 3)
        assert usage["data_used"] == 20 and usage["card_count"] == 1
        assert [c["card_id"] for c in usage["cards"]] == [1]
    source = await db.get(TrafficPoolModel, 10)
    assert (source.card_count, source.data_total, source.data_used, source.addon_flow) == (999, 99999, 99998, 0)
    assert not db.dirty


@pytest.mark.asyncio
async def test_filters_pagination_stats_and_dashboard_use_own_cards(db):
    items, total = await pool_service.get_pools(db, 2, 3, is_alert=False)
    assert total == 1 and items[0]["id"] == 10
    items, total = await pool_service.get_pools(db, 2, 3, is_alert=True)
    assert total == 1 and items[0]["id"] == 20
    items, total = await pool_service.get_pools(db, 2, 3, page=2, page_size=1)
    assert total == 2 and items[0]["id"] == 10
    assert (await pool_service.get_pools(db, 2, 3, customer_name="不存在")) == ([], 0)
    assert (await pool_service.get_pools(db, 2, 3, carrier="cucc")) == ([], 0)
    stats = await pool_service.get_pool_stats(db, 2, 3)
    assert stats == dict(total=2, enabled=2, disabled=0, alert_count=1,
                         total_cards=2, total_flow=200, used_flow=110,
                         by_carrier={"cmcc": 2, "cucc": 0, "ctcc": 0})
    user = SimpleNamespace(id=2, user_level=3)
    assert (await get_pool_stats(db, user)).data["total_data"] == 200
    chart = (await get_pools_usage_percent(db, user)).data
    assert sum(p["data_used"] for p in chart) == 110
    overview = await DashboardService.get_overview(db, user_id=2, user_level=3)
    assert overview.pools.total_pools == 2
    assert overview.pools.total_data == 200 and overview.pools.used_data == 110


@pytest.mark.asyncio
async def test_association_never_grants_write_log_or_unrelated_pool_access(db):
    for action in (
        pool_service.get_pool(db, 30, 2, 3),
        pool_service.get_pool_cards(db, 30, 2, 3),
        pool_service.get_pool_usage(db, 30, 2, 3),
        pool_service.update_pool(db, 10, 2, 3, name="越权"),
        pool_service.delete_pool(db, 10, 2, 3),
        pool_service.get_pool_logs(db, 10, 2, 3),
        pool_service.add_cards(db, 10, [1], 2, 3, 2),
        pool_service.remove_cards(db, 10, [1], 2, 3, 2),
        pool_service.recharge_pool(db, 10, 100, 2, 3),
        pool_service.repair_pool_suspend_status(db, 10, 2, 3, 2),
    ):
        with pytest.raises(BusinessException):
            await action
    # 划走后立即失去访问权，兄弟子账号仍只能看自己的卡。
    card = await db.get(IotCardModel, 1)
    card.user_id = 3
    await db.commit()
    with pytest.raises(BusinessException):
        await pool_service.get_pool(db, 10, 2, 3)
    sibling = await pool_service.get_pool(db, 10, 3, 3)
    assert sibling["card_count"] == 2 and sibling["data_used"] == 119


@pytest.mark.asyncio
async def test_month_boundary_and_non_contributing_cards(db):
    card = await db.get(IotCardModel, 1)
    card.data_usage_month = "2020-01"
    await db.commit()
    detail = await pool_service.get_pool(db, 10, 2, 3)
    assert detail["data_total"] == 100 and detail["data_used"] == 0
    card.status = CardStatus.suspended
    card.suspend_type = SuspendType.expired
    await db.commit()
    detail = await pool_service.get_pool(db, 10, 2, 3)
    assert detail["card_count"] == 1
    assert detail["data_total"] == 0 and detail["data_used"] == 0
    assert detail["card_stats"]["suspended"] == 1


@pytest.mark.asyncio
async def test_no_members_deleted_pool_and_card_pagination(db):
    assert (await pool_service.get_pools(db, 999, 3)) == ([], 0)
    stats = await pool_service.get_pool_stats(db, 999, 3)
    assert stats["total"] == 0 and stats["total_flow"] == 0
    cards, total = await pool_service.get_pool_cards(db, 10, 2, 3, page=2, page_size=1)
    assert cards == [] and total == 1
    pool = await db.get(TrafficPoolModel, 10)
    pool.is_deleted = 1
    await db.commit()
    with pytest.raises(BusinessException):
        await pool_service.get_pool_cards(db, 10, 2, 3)


@pytest.mark.asyncio
@pytest.mark.parametrize("month,expected", [(None, 100), ("current", 100), ("2020-01", 0)])
async def test_pool_addon_counted_once_and_only_in_effective_month(db, month, expected):
    pool = await db.get(TrafficPoolModel, 20)
    pool.addon_flow = 100
    pool.addon_flow_month = get_current_flow_cycle_month() if month == "current" else month
    await db.commit()
    detail = await pool_service.get_pool(db, 20, 2, 3)
    assert detail["addon_flow"] == expected
    assert detail["package_flow"] == 100 and detail["data_total"] == 100 + expected
    assert detail["data_remaining"] == 10 + expected
    assert detail["is_alert"] == (expected == 0)
    stats = await pool_service.get_pool_stats(db, 2, 3)
    assert stats["total_flow"] == 200 + expected
    assert stats["alert_count"] == (1 if expected == 0 else 0)
    usage = await pool_service.get_pool_usage(db, 20, 2, 3)
    assert usage["data_total"] == 100 + expected
    dashboard = await get_pool_stats(db, SimpleNamespace(id=2, user_level=3))
    assert dashboard.data["total_data"] == 200 + expected
    # 读投影不清理或改写生产池上的补量。
    assert pool.addon_flow == 100 and not db.dirty
