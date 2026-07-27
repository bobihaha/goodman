from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import event, select

from app.db.models.base import Base
from app.db.models.iot_card import CardStatus, CardType, IotCardModel
from app.db.models.package import CarrierType, PackageStatus, PeriodType, SalePackageModel
from app.db.models.pool import PoolCardLogModel, PoolStatus, TrafficPoolModel
from app.db.models.sys_log import SysOperationLogModel
from app.flow_packages import get_current_flow_cycle_month
from app.schemas.package_period import BatchChangePackageRequest
from app.services.package_period_service import PackagePeriodService
from tests.conftest import TestSessionLocal, test_engine


@pytest_asyncio.fixture
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as db:
        next_ids = {TrafficPoolModel: 9600, PoolCardLogModel: 9700}

        def assign_sqlite_bigint_ids(session, flush_context, instances):
            for item in session.new:
                model = type(item)
                if model in next_ids and item.id is None:
                    next_ids[model] += 1
                    item.id = next_ids[model]

        event.listen(db.sync_session, "before_flush", assign_sqlite_bigint_ids)
        try:
            yield db
        finally:
            event.remove(db.sync_session, "before_flush", assign_sqlite_bigint_ids)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def make_package(package_id: int, name: str, flow_size: int, user_id=None):
    return SalePackageModel(
        id=package_id,
        user_id=user_id,
        name=name,
        code=f"PKG-{package_id}",
        carrier=CarrierType.cmcc,
        flow_size=flow_size,
        period_type=PeriodType.monthly,
        price_cost=Decimal("10.00"),
        price_sale=Decimal("20.00"),
        is_public=1,
        status=PackageStatus.enable,
    )


@pytest.mark.asyncio
async def test_batch_change_package_moves_card_to_target_pool_and_keeps_addon(db_session, monkeypatch):
    def fail_if_supplier_called(*args, **kwargs):
        raise AssertionError("本地修改套餐不应调用供应商客户端")

    monkeypatch.setattr(
        "app.services.package_period_service.get_supplier_client",
        fail_if_supplier_called,
    )
    old_package = make_package(9201, "移动1G/月", 1024)
    target_package = make_package(9202, "移动2G/月", 2048)
    old_pool = TrafficPoolModel(
        id=9301,
        name="移动-1GB-月-自动池",
        carrier=CarrierType.cmcc,
        flow_size=1024,
        period_type=PeriodType.monthly,
        user_id=5001,
        sale_package_id=old_package.id,
        card_count=1,
        data_total=1152,
        data_used=100,
        package_flow=1152,
        status=PoolStatus.enable,
    )
    card = IotCardModel(
        id=9401,
        iccid="8986000000000009401",
        user_id=5001,
        sale_package_id=old_package.id,
        sale_price=Decimal("12.00"),
        carrier=CarrierType.cmcc,
        flow_size=1024,
        period_type=PeriodType.monthly,
        period_count=12,
        card_type=CardType.pool,
        status=CardStatus.activated,
        data_total=1152,
        data_used=100,
        data_used_month=100,
        addon_flow=128,
        addon_flow_month=get_current_flow_cycle_month(),
        pool_id=old_pool.id,
        is_pool_member=1,
    )
    db_session.add_all([old_package, target_package, old_pool, card])
    await db_session.commit()

    result = await PackagePeriodService.batch_change_package(
        db=db_session,
        data=BatchChangePackageRequest(
            iccids=[card.iccid],
            target_sale_package_id=target_package.id,
            reason="客户升级套餐",
        ),
        operator_id=1,
        operator_name="超级管理员",
    )

    assert result["failed_list"] == []

    await db_session.refresh(card)
    await db_session.refresh(old_pool)
    new_pool_result = await db_session.execute(
        select(TrafficPoolModel).where(
            TrafficPoolModel.sale_package_id == target_package.id,
            TrafficPoolModel.user_id == card.user_id,
        )
    )
    new_pool = new_pool_result.scalar_one()
    pool_logs = (
        await db_session.execute(
            select(PoolCardLogModel).where(PoolCardLogModel.card_id == card.id)
        )
    ).scalars().all()
    operation_log = (
        await db_session.execute(
            select(SysOperationLogModel).where(
                SysOperationLogModel.action == "change_package",
                SysOperationLogModel.target_id == card.id,
            )
        )
    ).scalar_one()

    assert result["success"] == 1
    assert result["failed"] == 0
    assert result["supplier_synced"] is False
    assert card.sale_package_id == target_package.id
    assert card.sale_price == target_package.price_sale
    assert card.flow_size == 2048
    assert card.data_total == 2176
    assert card.pool_id == new_pool.id
    assert card.is_pool_member == 1
    assert old_pool.card_count == 0
    assert old_pool.data_total == 0
    assert new_pool.card_count == 1
    assert new_pool.data_total == 2176
    assert {log.action for log in pool_logs} == {"add", "remove"}
    assert "未调用供应商改套餐接口" in operation_log.detail


@pytest.mark.asyncio
async def test_batch_change_package_supports_monthly_downgrade(db_session):
    old_package = make_package(9221, "移动2G/月", 2048)
    target_package = make_package(9222, "移动1G/月", 1024)
    card = IotCardModel(
        id=9421,
        iccid="8986000000000009421",
        user_id=5001,
        sale_package_id=old_package.id,
        carrier=CarrierType.cmcc,
        flow_size=2048,
        period_type=PeriodType.monthly,
        period_count=12,
        card_type=CardType.single,
        status=CardStatus.activated,
        data_total=2048,
        data_used=900,
        data_used_month=900,
    )
    db_session.add_all([old_package, target_package, card])
    await db_session.commit()

    result = await PackagePeriodService.batch_change_package(
        db=db_session,
        data=BatchChangePackageRequest(
            iccids=[card.iccid],
            target_sale_package_id=target_package.id,
        ),
        operator_id=1,
        operator_name="超级管理员",
    )

    await db_session.refresh(card)
    assert result["success"] == 1
    assert result["failed"] == 0
    assert card.sale_package_id == target_package.id
    assert card.flow_size == 1024
    assert card.data_total == 1024
    assert card.data_used == 900


@pytest.mark.asyncio
async def test_batch_change_package_rejects_other_customers_private_package(db_session):
    old_package = make_package(9211, "移动1G/月", 1024)
    other_customer_package = make_package(9212, "其他客户移动2G/月", 2048, user_id=6002)
    card = IotCardModel(
        id=9411,
        iccid="8986000000000009411",
        user_id=5001,
        sale_package_id=old_package.id,
        carrier=CarrierType.cmcc,
        flow_size=1024,
        period_type=PeriodType.monthly,
        period_count=12,
        card_type=CardType.single,
        status=CardStatus.activated,
        data_total=1024,
        data_used=100,
        data_used_month=100,
    )
    db_session.add_all([old_package, other_customer_package, card])
    await db_session.commit()

    result = await PackagePeriodService.batch_change_package(
        db=db_session,
        data=BatchChangePackageRequest(
            iccids=[card.iccid],
            target_sale_package_id=other_customer_package.id,
        ),
        operator_id=1,
        operator_name="超级管理员",
    )

    await db_session.refresh(card)
    assert result["success"] == 0
    assert result["failed"] == 1
    assert result["failed_list"][0]["error"] == "目标套餐不属于该卡片客户"
    assert card.sale_package_id == old_package.id
    assert card.flow_size == 1024
