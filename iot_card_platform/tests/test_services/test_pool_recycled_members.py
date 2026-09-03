from datetime import datetime, timedelta

import pytest
import pytest_asyncio

from app.crud.pool_crud import AUTO_POOL_REMARK, pool_crud
from app.db.models.base import Base
from app.db.models.iot_card import CardStatus, CardType, IotCardModel, SuspendType
from app.db.models.package import CarrierType, PeriodType
from app.db.models.pool import PoolStatus, TrafficPoolModel
from app.flow_packages import get_current_flow_cycle_month
from app.services.dashboard_service import DashboardService
from tests.conftest import TestSessionLocal, test_engine


@pytest_asyncio.fixture
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as db:
        yield db
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def current_cycle_sync_time():
    return datetime.strptime(f"{get_current_flow_cycle_month()}-01", "%Y-%m-%d")


@pytest.mark.asyncio
async def test_recycled_pool_cards_do_not_keep_empty_auto_pool_visible(db_session):
    db = db_session
    empty_auto_pool = TrafficPoolModel(
        id=8801,
        name="移动-10GB-月-自动池",
        carrier=CarrierType.cmcc,
        flow_size=10240,
        period_type=PeriodType.monthly,
        sale_package_id=2001,
        user_id=1001,
        card_count=1,
        data_total=10240,
        data_used=512,
        package_flow=10240,
        status=PoolStatus.enable,
        remark=AUTO_POOL_REMARK,
    )
    active_auto_pool = TrafficPoolModel(
        id=8802,
        name="移动-10GB-月-自动池",
        carrier=CarrierType.cmcc,
        flow_size=10240,
        period_type=PeriodType.monthly,
        sale_package_id=2002,
        user_id=1001,
        card_count=1,
        data_total=10240,
        data_used=256,
        package_flow=10240,
        status=PoolStatus.enable,
        remark=AUTO_POOL_REMARK,
    )
    recycled_card = IotCardModel(
        id=9901,
        iccid="8986000000000009901",
        carrier=CarrierType.cmcc,
        flow_size=10240,
        period_type=PeriodType.monthly,
        period_count=1,
        card_type=CardType.pool,
        user_id=None,
        pool_id=empty_auto_pool.id,
        is_pool_member=0,
        data_total=10240,
        data_used=512,
        data_used_month=512,
        status=CardStatus.stock,
    )
    active_card = IotCardModel(
        id=9902,
        iccid="8986000000000009902",
        carrier=CarrierType.cmcc,
        flow_size=10240,
        period_type=PeriodType.monthly,
        period_count=1,
        card_type=CardType.pool,
        user_id=1001,
        pool_id=active_auto_pool.id,
        is_pool_member=1,
        data_total=10240,
        data_used=256,
        data_used_month=256,
        status=CardStatus.activated,
    )
    db.add_all([empty_auto_pool, active_auto_pool, recycled_card, active_card])
    await db.commit()

    refreshed = await pool_crud.update_stats(db, empty_auto_pool.id)
    items, total = await pool_crud.get_list(db)
    dashboard_stats = await DashboardService.get_pool_stats(db)
    dashboard_usage = await DashboardService.get_pools_usage_percent(db)

    assert refreshed.card_count == 0
    assert refreshed.data_total == 0
    assert total == 1
    assert [item.id for item in items] == [active_auto_pool.id]
    assert dashboard_stats.total_pools == 1
    assert [item["id"] for item in dashboard_usage] == [active_auto_pool.id]


@pytest.mark.asyncio
async def test_pool_flow_only_counts_activated_cards(db_session):
    db = db_session
    pool = TrafficPoolModel(
        id=8810,
        name="移动-200MB-月-自动池",
        carrier=CarrierType.cmcc,
        flow_size=200,
        period_type=PeriodType.monthly,
        user_id=1001,
        status=PoolStatus.enable,
        remark=AUTO_POOL_REMARK,
    )
    cards = [
        IotCardModel(
            id=9910 + index,
            iccid=f"898604031025D08556{48 + index}",
            carrier=CarrierType.cmcc,
            flow_size=200,
            period_type=PeriodType.monthly,
            period_count=1,
            card_type=CardType.pool,
            user_id=1001,
            pool_id=pool.id,
            is_pool_member=1,
            data_total=200,
            data_used=data_used,
            data_used_month=data_used,
            data_sync_at=current_cycle_sync_time(),
            status=status,
        )
        for index, (status, data_used) in enumerate([
            (CardStatus.silent, 0),
            (CardStatus.silent, 0),
            (CardStatus.activated, 54),
            (CardStatus.activated, 615),
        ])
    ]
    db.add_all([pool, *cards])
    await db.commit()

    refreshed = await pool_crud.update_stats(db, pool.id)

    assert refreshed.card_count == 4
    assert refreshed.package_flow == 400
    assert refreshed.data_total == 400
    assert refreshed.data_used == 669
    assert refreshed.get_usage_percent() == 167.25


@pytest.mark.asyncio
async def test_billed_suspended_cards_keep_flow_but_expired_card_does_not(db_session):
    db = db_session
    pool = TrafficPoolModel(
        id=8820,
        name="移动-200MB-月-超量停卡池",
        carrier=CarrierType.cmcc,
        flow_size=200,
        period_type=PeriodType.monthly,
        user_id=1002,
        status=PoolStatus.enable,
    )
    active_card = IotCardModel(
        id=9920,
        iccid="8986000000000009920",
        carrier=CarrierType.cmcc,
        flow_size=200,
        period_type=PeriodType.monthly,
        period_count=1,
        card_type=CardType.pool,
        user_id=1002,
        pool_id=pool.id,
        is_pool_member=1,
        data_total=200,
        data_used=250,
        data_used_month=250,
        data_sync_at=current_cycle_sync_time(),
        status=CardStatus.activated,
    )
    pool_exceed_card = IotCardModel(
        id=9921,
        iccid="8986000000000009921",
        carrier=CarrierType.cmcc,
        flow_size=200,
        period_type=PeriodType.monthly,
        period_count=1,
        card_type=CardType.pool,
        user_id=1002,
        pool_id=pool.id,
        is_pool_member=1,
        data_total=200,
        data_used=150,
        data_used_month=150,
        data_sync_at=current_cycle_sync_time(),
        status=CardStatus.suspended,
        suspend_type=SuspendType.pool_exceed,
    )
    manual_suspended_card = IotCardModel(
        id=9922,
        iccid="8986000000000009922",
        carrier=CarrierType.cmcc,
        flow_size=200,
        period_type=PeriodType.monthly,
        period_count=1,
        card_type=CardType.pool,
        user_id=1002,
        pool_id=pool.id,
        is_pool_member=1,
        data_total=200,
        data_used=100,
        data_used_month=100,
        data_sync_at=current_cycle_sync_time(),
        status=CardStatus.suspended,
        suspend_type=SuspendType.manual,
    )
    expired_suspended_card = IotCardModel(
        id=9923,
        iccid="8986000000000009923",
        carrier=CarrierType.cmcc,
        flow_size=200,
        period_type=PeriodType.monthly,
        period_count=1,
        card_type=CardType.pool,
        user_id=1002,
        pool_id=pool.id,
        is_pool_member=1,
        data_total=200,
        data_used=50,
        data_used_month=50,
        data_sync_at=current_cycle_sync_time(),
        status=CardStatus.suspended,
        suspend_type=SuspendType.expired,
    )
    db.add_all([
        pool,
        active_card,
        pool_exceed_card,
        manual_suspended_card,
        expired_suspended_card,
    ])
    await db.commit()

    refreshed = await pool_crud.update_stats(db, pool.id)

    assert refreshed.card_count == 4
    assert refreshed.package_flow == 600
    assert refreshed.data_total == 600
    assert refreshed.data_used == 500


@pytest.mark.asyncio
async def test_monthly_pool_ignores_previous_month_usage_during_cycle_switch(db_session):
    db = db_session
    cycle_start = current_cycle_sync_time()
    previous_month = (cycle_start - timedelta(days=1)).strftime("%Y-%m")
    pool = TrafficPoolModel(
        id=8830,
        name="移动-10GB-月-自动池",
        carrier=CarrierType.cmcc,
        flow_size=10240,
        period_type=PeriodType.monthly,
        user_id=1003,
        addon_flow=10240,
        addon_flow_month=previous_month,
        alert_threshold_1=80,
        alert_threshold_2=90,
        alert_threshold_3=95,
        status=PoolStatus.enable,
    )
    card = IotCardModel(
        id=9930,
        iccid="898604031025C0316837",
        carrier=CarrierType.cmcc,
        flow_size=10240,
        period_type=PeriodType.monthly,
        period_count=1,
        card_type=CardType.pool,
        user_id=1003,
        pool_id=pool.id,
        is_pool_member=1,
        data_total=10240,
        data_used=15040,
        data_used_month=15040,
        data_sync_at=cycle_start - timedelta(seconds=1),
        status=CardStatus.activated,
    )
    db.add_all([pool, card])
    await db.commit()

    refreshed = await pool_crud.update_stats(db, pool.id)
    await db.refresh(card)

    assert refreshed.addon_flow == 0
    assert refreshed.data_total == 10240
    assert refreshed.data_used == 0
    assert refreshed.get_usage_percent() == 0
    assert card.status == CardStatus.activated
    assert card.suspend_type == SuspendType.none


@pytest.mark.asyncio
async def test_yearly_pool_keeps_cumulative_usage_without_current_month_sync(db_session):
    db = db_session
    pool = TrafficPoolModel(
        id=8840,
        name="移动-10GB-年-自动池",
        carrier=CarrierType.cmcc,
        flow_size=10240,
        period_type=PeriodType.yearly,
        user_id=1004,
        status=PoolStatus.enable,
    )
    card = IotCardModel(
        id=9940,
        iccid="898604031025C0316840",
        carrier=CarrierType.cmcc,
        flow_size=10240,
        period_type=PeriodType.yearly,
        period_count=1,
        card_type=CardType.pool,
        user_id=1004,
        pool_id=pool.id,
        is_pool_member=1,
        data_total=10240,
        data_used=4096,
        data_used_month=512,
        data_sync_at=current_cycle_sync_time() - timedelta(seconds=1),
        status=CardStatus.activated,
    )
    db.add_all([pool, card])
    await db.commit()

    refreshed = await pool_crud.update_stats(db, pool.id, run_checks=False)

    assert refreshed.data_total == 10240
    assert refreshed.data_used == 4096
    assert refreshed.get_usage_percent() == 40
