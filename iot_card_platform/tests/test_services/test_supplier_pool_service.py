"""
供应商流量池同步服务回归测试
"""
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.db.models.base import Base
from app.db.models.supplier import SupplierModel, SupplierStatus
from app.db.models.supplier_pool import SupplierTrafficPoolHistoryModel, SupplierTrafficPoolModel
from app.services.supplier_pool_service import supplier_traffic_pool_service
from tests.conftest import TestSessionLocal, test_engine


class FakeSupplierClient:
    def __init__(self, rows=None, error=None):
        self.rows = rows or []
        self.error = error

    async def get_traffic_pool_usage(self):
        if self.error:
            raise self.error
        return self.rows


@pytest_asyncio.fixture
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as db:
        yield db
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_sync_keeps_pool_success_when_alert_email_fails(db_session):
    db = db_session
    try:
        supplier = SupplierModel(
            id=1,
            name="LX",
            code="001",
            status=SupplierStatus.enable,
            contact_email="ops@example.com",
        )
        pool = SupplierTrafficPoolModel(
            supplier_id=1,
            supplier_name="LX",
            supplier_pool_code="P1",
            supplier_pool_name="旧池",
            total_flow=100,
            used_flow=85,
            remaining_flow=15,
            usage_percent=85,
            alert_threshold=80,
            alert_emails="bad@example.com",
            sync_status="success",
        )
        db.add_all([supplier, pool])
        await db.commit()

        client = FakeSupplierClient(rows=[
            {
                "supplier_pool_code": "P1",
                "supplier_pool_name": "测试池",
                "carrier": "cmcc",
                "pool_specification": 5120,
                "total_flow": 100,
                "used_flow": 90,
                "remaining_flow": 10,
                "usage_percent": 90,
            }
        ])

        with patch("app.services.supplier_pool_service.get_supplier_client", return_value=client), \
             patch(
                 "app.services.supplier_pool_service.NotificationService.send_email",
                 AsyncMock(side_effect=RuntimeError("smtp down")),
             ):
            result = await supplier_traffic_pool_service.sync_supplier_pools(db)

        assert result["success_pools"] == 1
        assert result["failed_pools"] == 0
        assert result["failed_suppliers"] == 0

        refreshed = (
            await db.execute(
                select(SupplierTrafficPoolModel).where(SupplierTrafficPoolModel.supplier_pool_code == "P1")
            )
        ).scalar_one()
        assert refreshed.sync_status == "success"
        assert refreshed.sync_error.startswith("邮件提醒失败")
        assert refreshed.last_alert_at is None
        assert refreshed.last_alert_threshold is None

        history = (
            await db.execute(
                select(SupplierTrafficPoolHistoryModel).where(
                    SupplierTrafficPoolHistoryModel.supplier_pool_id == refreshed.id
                )
            )
        ).scalar_one()
        assert history.record_month == refreshed.last_sync_at.strftime("%Y-%m")
        assert history.usage_percent == 90
        assert history.used_flow == 90
    finally:
        await db.rollback()


@pytest.mark.asyncio
async def test_sync_marks_existing_supplier_pools_failed_on_supplier_error(db_session):
    db = db_session
    try:
        supplier = SupplierModel(
            id=2,
            name="LX",
            code="001",
            status=SupplierStatus.enable,
        )
        pool = SupplierTrafficPoolModel(
            supplier_id=2,
            supplier_name="LX",
            supplier_pool_code="P2",
            supplier_pool_name="旧池",
            total_flow=100,
            used_flow=20,
            remaining_flow=80,
            usage_percent=20,
            sync_status="success",
        )
        db.add_all([supplier, pool])
        await db.commit()

        client = FakeSupplierClient(error=RuntimeError("supplier timeout"))

        with patch("app.services.supplier_pool_service.get_supplier_client", return_value=client):
            result = await supplier_traffic_pool_service.sync_supplier_pools(db)

        assert result["success_pools"] == 0
        assert result["failed_pools"] == 1
        assert result["failed_suppliers"] == 1

        refreshed = (
            await db.execute(
                select(SupplierTrafficPoolModel).where(SupplierTrafficPoolModel.supplier_pool_code == "P2")
            )
        ).scalar_one()
        assert refreshed.sync_status == "failed"
        assert refreshed.sync_error == "supplier timeout"
        assert refreshed.last_sync_at is not None
    finally:
        await db.rollback()


@pytest.mark.asyncio
async def test_sync_sends_highest_reached_threshold_and_escalates(db_session):
    db = db_session
    try:
        supplier = SupplierModel(
            id=4,
            name="SIMBOSS",
            code="002",
            status=SupplierStatus.enable,
            contact_email="ops@example.com",
        )
        pool = SupplierTrafficPoolModel(
            supplier_id=4,
            supplier_name="SIMBOSS",
            supplier_pool_code="P4",
            supplier_pool_name="三级池",
            total_flow=100,
            used_flow=65,
            remaining_flow=35,
            usage_percent=65,
            alert_thresholds="60,80,100",
            alert_emails="ops@example.com",
            last_alert_at=datetime.now(),
            last_alert_threshold=60,
            sync_status="success",
        )
        db.add_all([supplier, pool])
        await db.commit()

        client = FakeSupplierClient(rows=[
            {
                "supplier_pool_code": "P4",
                "supplier_pool_name": "三级池",
                "carrier": "cucc",
                "pool_specification": 51200,
                "total_flow": 100,
                "used_flow": 85,
                "remaining_flow": 15,
                "usage_percent": 85,
            }
        ])
        send_email = AsyncMock(return_value=True)

        with patch("app.services.supplier_pool_service.get_supplier_client", return_value=client), \
             patch("app.services.supplier_pool_service.NotificationService.send_email", send_email):
            result = await supplier_traffic_pool_service.sync_supplier_pools(db)

        assert result["success_pools"] == 1
        send_email.assert_awaited_once()
        content = send_email.await_args.args[3]
        assert "触发阈值：80%" in content

        refreshed = (
            await db.execute(
                select(SupplierTrafficPoolModel).where(SupplierTrafficPoolModel.supplier_pool_code == "P4")
            )
        ).scalar_one()
        assert refreshed.last_alert_threshold == 80
        assert refreshed.last_alert_usage_percent == 85
    finally:
        await db.rollback()


@pytest.mark.asyncio
async def test_update_alert_thresholds_and_sorting(db_session):
    db = db_session
    try:
        db.add_all([
            SupplierTrafficPoolModel(
                supplier_id=5,
                supplier_name="A",
                supplier_pool_code="A",
                supplier_pool_name="低用量",
                carrier="cmcc",
                pool_specification=1024,
                total_flow=100,
                used_flow=20,
                remaining_flow=80,
                usage_percent=20,
                alert_thresholds="60,80,100",
                sync_status="success",
            ),
            SupplierTrafficPoolModel(
                supplier_id=5,
                supplier_name="A",
                supplier_pool_code="B",
                supplier_pool_name="高规格",
                carrier="cmcc",
                pool_specification=40960,
                total_flow=100,
                used_flow=70,
                remaining_flow=30,
                usage_percent=70,
                alert_thresholds="60,80,100",
                sync_status="success",
            ),
        ])
        await db.commit()

        items, _ = await supplier_traffic_pool_service.get_list(
            db,
            order_by="pool_specification",
            order_dir="desc",
        )
        assert [item["supplier_pool_code"] for item in items] == ["B", "A"]

        updated = await supplier_traffic_pool_service.update_alert(
            db,
            pool_id=items[0]["id"],
            alert_threshold=None,
            alert_thresholds=[100, 60, 80, 80],
            alert_emails="ops@example.com",
        )
        assert updated["alert_thresholds"] == "60,80,100"
    finally:
        await db.rollback()


@pytest.mark.asyncio
async def test_get_detail_returns_pool_and_monthly_histories(db_session):
    db = db_session
    try:
        pool = SupplierTrafficPoolModel(
            id=10,
            supplier_id=3,
            supplier_name="SIMBOSS",
            supplier_pool_code="SB-P1",
            supplier_pool_name="测试池",
            total_flow=1000,
            used_flow=600,
            remaining_flow=400,
            usage_percent=60,
            sync_status="success",
        )
        db.add(pool)
        db.add_all([
            SupplierTrafficPoolHistoryModel(
                supplier_pool_id=10,
                supplier_id=3,
                supplier_name="SIMBOSS",
                supplier_pool_code="SB-P1",
                supplier_pool_name="测试池",
                record_month="2026-04",
                total_flow=1000,
                used_flow=500,
                remaining_flow=500,
                usage_percent=50,
            ),
            SupplierTrafficPoolHistoryModel(
                supplier_pool_id=10,
                supplier_id=3,
                supplier_name="SIMBOSS",
                supplier_pool_code="SB-P1",
                supplier_pool_name="测试池",
                record_month="2026-05",
                total_flow=1000,
                used_flow=600,
                remaining_flow=400,
                usage_percent=60,
            ),
        ])
        await db.commit()

        detail = await supplier_traffic_pool_service.get_detail(db, pool_id=10, months=12)

        assert detail["pool"]["supplier_pool_code"] == "SB-P1"
        assert [item["record_month"] for item in detail["histories"]] == ["2026-04", "2026-05"]
        assert [item["usage_percent"] for item in detail["histories"]] == [50, 60]
    finally:
        await db.rollback()
