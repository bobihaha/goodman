import pytest
import pytest_asyncio

from app.crud.pool_crud import AUTO_POOL_REMARK, pool_crud
from app.db.models.base import Base
from app.db.models.iot_card import CardStatus, CardType, IotCardModel
from app.db.models.package import CarrierType, PeriodType
from app.db.models.pool import PoolStatus, TrafficPoolModel
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
