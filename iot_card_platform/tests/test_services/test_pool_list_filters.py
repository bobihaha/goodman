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


@pytest.mark.asyncio
@pytest.mark.parametrize('user_level', [1, 2])
async def test_direct_child_scope_and_customer_search(db_session, user_level):
    from app.db.models.sys_user import SysUserModel
    from app.services.pool_service import pool_service
    from app.utils.exceptions import BusinessException

    users = [
        SysUserModel(id=9201, name='本人', account='scope-owner', password='test', user_level=user_level),
        SysUserModel(id=9202, name='目标客户甲', account='scope-child-a', password='test', parent_id=9201),
        SysUserModel(id=9203, name='目标客户乙', account='scope-child-b', password='test', parent_id=9201),
        SysUserModel(id=9204, name='目标客户下下级', account='scope-grandchild', password='test', parent_id=9202),
        SysUserModel(id=9205, name='目标客户其他', account='scope-other', password='test'),
        SysUserModel(id=9206, name='目标客户已删', account='scope-deleted', password='test', parent_id=9201, is_deleted=1),
    ]
    pools = []
    for user in users:
        pool = make_pool(user.id, data_used=80, threshold=80)
        pool.user_id = user.id
        pools.append(pool)
    db_session.add_all([*users, *pools])
    await db_session.commit()

    scope = await pool_service._get_accessible_user_ids(db_session, 9201, user_level)
    assert set(scope) == {9201, 9202, 9203}
    items, total = await pool_service.get_pools(
        db_session, 9201, user_level, customer_name=' 目标客户 ', is_alert=True, page_size=1,
    )
    next_items, next_total = await pool_service.get_pools(
        db_session, 9201, user_level, customer_name='目标客户', is_alert=True, page=2, page_size=1,
    )
    assert total == next_total == 2
    assert items[0]['id'] == 9203
    assert items[0]['user_name'] == '目标客户乙'
    assert next_items[0]['id'] == 9202
    assert (await pool_service.get_pool_stats(db_session, 9201, user_level))['total'] == 3
    assert (await pool_service._get_pool_in_scope(db_session, 9202, 9201, user_level)).id == 9202
    for hidden_id in [9204, 9205, 9206]:
        with pytest.raises(BusinessException):
            await pool_service.get_pool_usage(db_session, hidden_id, 9201, user_level)
        hidden, count = await pool_service.get_pools(
            db_session, 9201, user_level, customer_name=users[hidden_id - 9201].name,
        )
        assert hidden == [] and count == 0
    assert await pool_service._get_accessible_user_ids(db_session, 9202, 3) == [9202]
    from types import SimpleNamespace
    from app.api.v1.dashboard import get_pool_stats, get_pools_usage_percent
    from app.services.dashboard_service import DashboardService

    current_user = SimpleNamespace(id=9201, user_level=user_level)
    dashboard_stats = await get_pool_stats(db_session, current_user)
    dashboard_usage = await get_pools_usage_percent(db_session, current_user)
    assert dashboard_stats.data['total_pools'] == 3
    assert {pool['id'] for pool in dashboard_usage.data} == {9201, 9202, 9203}
    overview = await DashboardService.get_overview(
        db_session, user_id=9201, is_admin=user_level == 1, user_level=user_level,
    )
    assert overview.pools.total_pools == 3


@pytest.mark.asyncio
async def test_customer_search_treats_wildcards_literally(db_session):
    from app.db.models.sys_user import SysUserModel

    user = SysUserModel(id=9301, name='客户100%_A', account='literal-customer', password='test')
    other = SysUserModel(id=9302, name='客户100XXA', account='other-customer', password='test')
    pools = [make_pool(user.id, 10, 80), make_pool(other.id, 10, 80)]
    pools[0].user_id, pools[1].user_id = user.id, other.id
    db_session.add_all([user, other, *pools])
    await db_session.commit()
    items, total = await pool_crud.get_list(db_session, user_ids=[9301, 9302], customer_name='%_')
    assert total == 1
    assert [pool.id for pool in items] == [9301]
    assert (await pool_crud.get_list(db_session, user_ids=[], customer_name='%_')) == ([], 0)


@pytest.mark.asyncio
async def test_shared_card_does_not_expose_out_of_scope_pool(db_session):
    from app.db.models.iot_card import IotCardModel, CardStatus, CardType

    hidden_pool = make_pool(9401, 80, 80)
    hidden_pool.user_id = 9402
    card = IotCardModel(
        id=9401, iccid='8986000000000009401', user_id=9403,
        pool_id=hidden_pool.id, is_pool_member=1, carrier=CarrierType.cmcc,
        flow_size=100, period_type=PeriodType.monthly, period_count=1,
        card_type=CardType.pool, status=CardStatus.activated, data_total=100,
    )
    db_session.add_all([hidden_pool, card])
    await db_session.commit()
    assert await pool_crud.get_list(db_session, user_ids=[9403]) == ([], 0)
    assert await pool_crud.get_by_id_in_scope(db_session, hidden_pool.id, [9403]) is None
    assert (await pool_crud.get_stats(db_session, user_ids=[9403]))['total'] == 0
