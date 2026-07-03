from datetime import date
from decimal import Decimal
from io import BytesIO
from unittest.mock import AsyncMock, patch
from zipfile import ZipFile

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.db.models.base import Base
from app.db.models.iot_card import CardStatus, IotCardModel
from app.db.models.pool import TrafficPoolModel
from app.db.models.package import CarrierType, PeriodType
from app.db.models.suspend import AlertLevel, AlertLogModel, AlertTargetType
from app.db.models.sys_user import SysUserModel
from app.services.card_expiry_reminder_service import CardExpiryReminderService
from app.services.notification_service import NotificationService
from tests.conftest import TestSessionLocal, test_engine


@pytest_asyncio.fixture
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as db:
        yield db
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def test_usage_summary_email_renders_empty_pool_and_card_threshold():
    _, text_content, html_content = NotificationService._render_usage_summary_message(
        customer_name="测试客户",
        pool_alerts=[],
        card_alerts=[
            {
                "iccid": "89860000000000000001",
                "msisdn": "14700000001",
                "carrier": "移动",
                "package_name": "移动1G/月",
                "data_used": 820,
                "data_total": 1024,
                "usage_percent": 80,
                "threshold": 80,
                "alert_level": AlertLevel.warning.value,
            }
        ],
    )

    assert "流量池提醒数量：0" in text_content
    assert "暂无流量池用量提醒" in html_content
    assert "89860000000000000001" in html_content
    assert "80%" in html_content
    assert "普通预警" in html_content
    assert "待关注" in html_content


def test_expiry_reminder_xlsx_contains_required_columns_and_card_values():
    user = SysUserModel(id=12, name="客户A", account="customer-a", email="customer@example.com")
    card = IotCardModel(
        iccid="89860000000000000002",
        imsi="460001234567890",
        msisdn="14700000002",
        carrier=CarrierType.cmcc,
        flow_size=1024,
        period_type=PeriodType.monthly,
        period_count=1,
        data_total=1024,
        activated_at=date(2026, 7, 1),
        expired_at=date(2026, 7, 31),
        remark="测试备注",
        sale_price=Decimal("12.34"),
    )

    content = CardExpiryReminderService._build_expiry_xlsx(user, [card])
    with ZipFile(BytesIO(content)) as xlsx:
        sheet_xml = xlsx.read("xl/worksheets/sheet1.xml").decode("utf-8")

    assert "运营商" in sheet_xml
    assert "续费价格" in sheet_xml
    assert "89860000000000000002" in sheet_xml
    assert "460001234567890" in sheet_xml
    assert "14700000002" in sheet_xml
    assert "客户A" in sheet_xml
    assert "测试备注" in sheet_xml


@pytest.mark.asyncio
async def test_expiry_reminder_skips_duplicate_send_marker(db_session):
    db = db_session
    user = SysUserModel(
        id=31,
        name="客户B",
        account="customer-b",
        password="test-password",
        email="customer-b@example.com",
    )
    card = IotCardModel(
        id=3101,
        iccid="89860000000000000031",
        imsi="460001234567831",
        msisdn="14700000031",
        user_id=31,
        carrier=CarrierType.cmcc,
        flow_size=1024,
        period_type=PeriodType.monthly,
        period_count=1,
        data_total=1024,
        status=CardStatus.activated,
        activated_at=date(2026, 7, 1),
        expired_at=date(2026, 7, 31),
    )
    db.add_all([user, card])
    await db.commit()

    send_email = AsyncMock(return_value=True)
    with patch("app.services.card_expiry_reminder_service.NotificationService.send_email", send_email):
        first = await CardExpiryReminderService.send_monthly_expiry_reminders(db, today=date(2026, 7, 10))
        second = await CardExpiryReminderService.send_monthly_expiry_reminders(db, today=date(2026, 7, 10))

    assert first["sent"] == 1
    assert second["sent"] == 0
    assert second["skipped"] == 1
    send_email.assert_awaited_once()


@pytest.mark.asyncio
async def test_pending_usage_alerts_are_aggregated_and_marked_notified(db_session):
    db = db_session
    user = SysUserModel(
        id=41,
        name="客户C",
        account="customer-c",
        password="test-password",
        email="customer-c@example.com",
    )
    card = IotCardModel(
        id=4101,
        iccid="89860000000000000041",
        imsi="460001234567841",
        msisdn="14700000041",
        user_id=41,
        carrier=CarrierType.cmcc,
        flow_size=1024,
        period_type=PeriodType.monthly,
        period_count=1,
        data_used=1024,
        data_total=1024,
        status=CardStatus.activated,
    )
    pool = TrafficPoolModel(
        id=4102,
        name="客户C流量池",
        user_id=41,
        carrier=CarrierType.cmcc,
        flow_size=1024,
        period_type=PeriodType.monthly,
        card_count=10,
        data_used=8500,
        data_total=10000,
        alert_threshold_1=60,
        alert_threshold_2=80,
        alert_threshold_3=100,
    )
    card_alert = AlertLogModel(
        id=4103,
        target_type=AlertTargetType.card,
        target_id=4101,
        target_name=card.iccid,
        alert_level=AlertLevel.exceed,
        usage_percent=100,
        threshold=100,
        user_id=41,
        notified=0,
        handled=0,
    )
    pool_alert = AlertLogModel(
        id=4104,
        target_type=AlertTargetType.pool,
        target_id=4102,
        target_name=pool.name,
        alert_level=AlertLevel.critical,
        usage_percent=85,
        threshold=80,
        user_id=41,
        notified=0,
        handled=0,
    )
    db.add_all([user, card, pool, card_alert, pool_alert])
    await db.commit()

    send_email = AsyncMock(return_value=True)
    with patch("app.services.notification_service.NotificationService.send_email", send_email):
        sent = await NotificationService.send_pending_usage_alerts_for_user(db, 41)

    assert sent is True
    send_email.assert_awaited_once()
    html_content = send_email.await_args.kwargs["html_content"]
    assert "客户C流量池" in html_content
    assert "89860000000000000041" in html_content
    assert "已超限，待停卡处理" in html_content

    result = await db.execute(select(AlertLogModel).where(AlertLogModel.user_id == 41))
    assert all(item.notified == 1 for item in result.scalars().all())
