from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace
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
from app.db.models.sys_user import SysUserModel, UserLevel, UserStatus
from app.crud.pool_crud import TrafficPoolCRUD
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


@pytest.mark.asyncio
async def test_send_email_bccs_enabled_super_admins_without_exposing_or_duplicating(db_session):
    db = db_session
    db.add_all([
        SysUserModel(
            id=21,
            name="启用管理员",
            account="enabled-admin",
            password="test-password",
            email="admin@example.com",
            user_level=UserLevel.SUPER_ADMIN.value,
            status=UserStatus.enable,
        ),
        SysUserModel(
            id=22,
            name="停用管理员",
            account="disabled-admin",
            password="test-password",
            email="disabled-admin@example.com",
            user_level=UserLevel.SUPER_ADMIN.value,
            status=UserStatus.disable,
        ),
        SysUserModel(
            id=23,
            name="客户",
            account="customer-recipient",
            password="test-password",
            email="customer@example.com",
            user_level=UserLevel.USER.value,
            status=UserStatus.enable,
        ),
    ])
    await db.commit()

    email_settings = {
        "enabled": True,
        "host": "smtp.example.com",
        "port": 465,
        "username": "",
        "password": "",
        "from_email": "sender@example.com",
        "from_name": "IoT Card Platform",
        "use_tls": False,
        "use_ssl": True,
        "timeout": 30,
    }
    to_thread = AsyncMock()
    with patch.object(NotificationService, "get_email_settings", AsyncMock(return_value=email_settings)), \
         patch("app.services.notification_service.asyncio.to_thread", to_thread):
        sent = await NotificationService.send_email(
            db=db,
            to_email="customer@example.com",
            subject="告警测试",
            content="测试内容",
            copy_super_admins=True,
        )

    assert sent is True
    message = to_thread.await_args.args[2]
    assert message["To"] == "customer@example.com"
    assert message["Bcc"] == "admin@example.com"
    assert "admin@example.com" not in message["To"]
    assert "disabled-admin@example.com" not in message["Bcc"]
    assert await NotificationService.get_super_admin_emails(
        db,
        exclude_emails=["ADMIN@example.com"]
    ) == []


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
    assert send_email.await_args.kwargs["copy_super_admins"] is True


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
        data_used=6000,
        data_total=10240,
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
        notified=1,
        handled=0,
        created_at=datetime(2026, 9, 2, 1, 0, 1),
    )
    pool_alert = AlertLogModel(
        id=4104,
        target_type=AlertTargetType.pool,
        target_id=4102,
        target_name=pool.name,
        alert_level=AlertLevel.warning,
        usage_percent=80,
        threshold=80,
        data_used_snapshot=8192,
        data_total_snapshot=10240,
        remaining_flow_snapshot=0,
        user_id=41,
        notified=1,
        handled=0,
        created_at=datetime(2026, 9, 2, 1, 0, 1),
    )
    pool_critical_alert = AlertLogModel(
        id=4105,
        target_type=AlertTargetType.pool,
        target_id=4102,
        target_name=pool.name,
        alert_level=AlertLevel.critical,
        usage_percent=90,
        threshold=90,
        data_used_snapshot=9216,
        data_total_snapshot=10240,
        remaining_flow_snapshot=0,
        user_id=41,
        notified=0,
        handled=0,
        created_at=datetime(2026, 9, 3, 1, 0, 1),
    )
    stale_pool_alert = AlertLogModel(
        id=4107,
        target_type=AlertTargetType.pool,
        target_id=4102,
        target_name=pool.name,
        alert_level=AlertLevel.exceed,
        usage_percent=255,
        threshold=100,
        user_id=41,
        notified=0,
        handled=0,
        created_at=datetime(2026, 8, 19, 10, 35, 8),
    )
    db.add_all([
        user,
        card,
        pool,
        card_alert,
        pool_alert,
        pool_critical_alert,
        stale_pool_alert,
    ])
    await db.commit()

    send_email = AsyncMock(return_value=True)
    with patch(
        "app.services.notification_service.NotificationService.send_email",
        send_email,
    ), patch(
        "app.services.notification_service.beijing_now",
        return_value=datetime(2026, 9, 3, 2, 0, 0),
    ):
        sent = await NotificationService.send_pending_usage_alerts_for_user(
            db,
            41,
            [4105],
        )

    assert sent is True
    send_email.assert_awaited_once()
    assert send_email.await_args.kwargs["copy_super_admins"] is True
    html_content = send_email.await_args.kwargs["html_content"]
    assert "客户C流量池" in html_content
    assert html_content.count("<td>客户C流量池</td>") == 2
    assert "89860000000000000041" in html_content
    assert "已超限，待停卡处理" in html_content
    assert "8192 MB" in html_content
    assert "9216 MB" in html_content
    assert "80%" in html_content
    assert "90%" in html_content
    assert "2026-09-02 01:00:01" in html_content
    assert "2026-09-03 01:00:01" in html_content
    assert "255%" not in html_content
    assert "1024 MB" not in html_content

    result = await db.execute(select(AlertLogModel).where(AlertLogModel.user_id == 41))
    alerts = {item.id: item for item in result.scalars().all()}
    assert all(alerts[item_id].notified == 1 for item_id in [4103, 4104, 4105])
    assert alerts[4107].notified == 0


@pytest.mark.asyncio
async def test_pool_alert_email_is_scoped_to_new_snapshot_alert_ids():
    db = AsyncMock()
    pool = TrafficPoolModel(
        id=4201,
        name="客户D流量池",
        user_id=42,
        carrier=CarrierType.cmcc,
        flow_size=10240,
        period_type=PeriodType.monthly,
        card_count=3,
        data_used=13569,
        data_total=10240,
        alert_threshold_1=80,
        alert_threshold_2=90,
        alert_threshold_3=100,
    )

    with patch(
        "app.crud.suspend_crud.AlertLogCRUD.check_exists",
        AsyncMock(return_value=False),
    ), patch(
        "app.crud.suspend_crud.AlertLogCRUD.create",
        AsyncMock(return_value=SimpleNamespace(id=4204)),
    ) as create_alert, patch(
        "app.services.notification_service.NotificationService.send_pending_usage_alerts_for_user",
        AsyncMock(return_value=True),
    ) as send_alerts:
        await TrafficPoolCRUD()._check_pool_alert_thresholds(db, pool)

    create_alert.assert_awaited_once()
    assert create_alert.await_args.kwargs["alert_level"] == AlertLevel.exceed
    assert create_alert.await_args.kwargs["threshold"] == 100
    assert create_alert.await_args.kwargs["data_used_snapshot"] == 13569
    assert create_alert.await_args.kwargs["data_total_snapshot"] == 10240
    assert create_alert.await_args.kwargs["remaining_flow_snapshot"] == 0
    send_alerts.assert_awaited_once_with(db, 42, [4204])
