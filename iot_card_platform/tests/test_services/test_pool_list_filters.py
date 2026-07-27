from typing import Optional

import pytest
import pytest_asyncio

from app.crud.pool_crud import pool_crud
from app.db.models.base import Base
from app.db.models.package import CarrierType, PeriodType
from app.db.models.pool import PoolStatus, TrafficPoolModel
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


def make_pool(pool_id: int, data_used: int, threshold: Optional[int]) -> TrafficPoolModel:
    return TrafficPoolModel(
        id=pool_id,
        name=f"测试流量池-{pool_id}",
        carrier=CarrierType.cmcc,
        flow_size=100,
        period_type=PeriodType.monthly,
        card_count=1,
        data_total=100,
        data_used=data_used,
        package_flow=100,
        alert_threshold_1=threshold,
        status=PoolStatus.enable,
    )


@pytest.mark.asyncio
async def test_pool_list_filters_alert_status_and_keeps_pagination(db_session):
    alert_pool = make_pool(9103, data_used=80, threshold=80)
    normal_pool = make_pool(9102, data_used=79, threshold=80)
    no_threshold_pool = make_pool(9101, data_used=100, threshold=None)
    db_session.add_all([alert_pool, normal_pool, no_threshold_pool])
    await db_session.commit()

    alert_items, alert_total = await pool_crud.get_list(
        db_session,
        is_alert=True,
        page=1,
        page_size=1,
    )
    normal_page_1, normal_total = await pool_crud.get_list(
        db_session,
        is_alert=False,
        page=1,
        page_size=1,
    )
    normal_page_2, _ = await pool_crud.get_list(
        db_session,
        is_alert=False,
        page=2,
        page_size=1,
    )

    assert alert_total == 1
    assert [pool.id for pool in alert_items] == [alert_pool.id]
    assert normal_total == 2
    assert [pool.id for pool in normal_page_1] == [normal_pool.id]
    assert [pool.id for pool in normal_page_2] == [no_threshold_pool.id]
