"""
通知服务
"""
import asyncio
import json
import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crud.system_crud import SysConfigCRUD, SysNotifyTemplateCRUD
from app.crud.suspend_crud import AlertLogCRUD
from app.db.models.iot_card import IotCardModel
from app.db.models.pool import TrafficPoolModel
from app.db.models.suspend import AlertLevel, AlertLogModel
from app.db.models.sys_user import SysUserModel

logger = logging.getLogger(__name__)


class NotificationService:
    """系统通知服务"""

    EMAIL_CONFIG_KEYS = {
        "enabled": "notify_email_enabled",
        "host": "notify_email_smtp_host",
        "port": "notify_email_smtp_port",
        "username": "notify_email_smtp_username",
        "password": "notify_email_smtp_password",
        "from_email": "notify_email_from_email",
        "from_name": "notify_email_from_name",
        "use_tls": "notify_email_use_tls",
        "use_ssl": "notify_email_use_ssl",
        "timeout": "notify_email_timeout",
    }

    CARD_ALERT_TEMPLATE_CODES = {
        AlertLevel.warning.value: "alert_warning",
        AlertLevel.critical.value: "alert_critical",
        AlertLevel.exceed.value: "alert_suspend",
    }

    POOL_ALERT_TEMPLATE_CODES = {
        AlertLevel.warning.value: "pool_warning",
        AlertLevel.critical.value: "pool_warning",
        AlertLevel.exceed.value: "pool_suspend",
    }

    @staticmethod
    async def _get_config_value(db: AsyncSession, config_key: str) -> Any:
        config = await SysConfigCRUD.get_by_key(db, config_key)
        return config.get_value() if config else None

    @classmethod
    async def get_email_settings(cls, db: AsyncSession) -> Dict[str, Any]:
        """读取邮件配置，优先系统配置，缺省回退到环境变量"""
        raw_values = {}
        for field_name, config_key in cls.EMAIL_CONFIG_KEYS.items():
            raw_values[field_name] = await cls._get_config_value(db, config_key)

        return {
            "enabled": cls._pick_bool(raw_values["enabled"], settings.smtp_enabled),
            "host": cls._pick_str(raw_values["host"], settings.smtp_host),
            "port": cls._pick_int(raw_values["port"], settings.smtp_port),
            "username": cls._pick_str(raw_values["username"], settings.smtp_username),
            "password": cls._pick_str(raw_values["password"], settings.smtp_password),
            "from_email": cls._pick_str(raw_values["from_email"], settings.smtp_from_email),
            "from_name": cls._pick_str(raw_values["from_name"], settings.smtp_from_name),
            "use_tls": cls._pick_bool(raw_values["use_tls"], settings.smtp_use_tls),
            "use_ssl": cls._pick_bool(raw_values["use_ssl"], settings.smtp_use_ssl),
            "timeout": cls._pick_int(raw_values["timeout"], settings.smtp_timeout),
        }

    @staticmethod
    def _pick_str(value: Any, default: str) -> str:
        if value is None:
            return default
        return str(value).strip()

    @staticmethod
    def _pick_int(value: Any, default: int) -> int:
        if value in (None, ""):
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _pick_bool(value: Any, default: bool) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    @classmethod
    async def send_email(
        cls,
        db: AsyncSession,
        to_email: str,
        subject: str,
        content: str
    ) -> bool:
        """发送邮件"""
        email_settings = await cls.get_email_settings(db)
        if not email_settings["enabled"]:
            logger.info("邮件通知未启用，跳过发送")
            return False

        required_fields = ("host", "port", "from_email")
        missing_fields = [field for field in required_fields if not email_settings.get(field)]
        if missing_fields:
            logger.warning("邮件配置不完整，缺少字段: %s", ", ".join(missing_fields))
            return False

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = formataddr((email_settings["from_name"], email_settings["from_email"]))
        message["To"] = to_email
        message.set_content(content)

        await asyncio.to_thread(cls._deliver_email, email_settings, message)
        return True

    @staticmethod
    def _deliver_email(email_settings: Dict[str, Any], message: EmailMessage) -> None:
        smtp_class = smtplib.SMTP_SSL if email_settings["use_ssl"] else smtplib.SMTP
        context = ssl.create_default_context()

        with smtp_class(
            email_settings["host"],
            email_settings["port"],
            timeout=email_settings["timeout"]
        ) as smtp:
            if not email_settings["use_ssl"]:
                smtp.ehlo()
                if email_settings["use_tls"]:
                    smtp.starttls(context=context)
                    smtp.ehlo()

            if email_settings["username"]:
                smtp.login(email_settings["username"], email_settings["password"])

            smtp.send_message(message)

    @classmethod
    async def send_alert_email(
        cls,
        db: AsyncSession,
        alert: AlertLogModel,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """按告警记录发送邮件"""
        auto_notify = await cls._get_config_value(db, "alert_auto_notify")
        if auto_notify is False:
            return False

        if not alert.user_id:
            return False

        user = await db.get(SysUserModel, alert.user_id)
        if not user or not user.email:
            return False

        if not cls._is_user_email_notify_enabled(user.alert_notify):
            return False

        subject, content = await cls._render_alert_message(db, alert, extra_context or {})
        if not subject or not content:
            return False

        try:
            sent = await cls.send_email(db, user.email, subject, content)
        except Exception as exc:
            logger.exception("发送告警邮件失败 alert_id=%s error=%s", alert.id, exc)
            return False

        if sent:
            await AlertLogCRUD.mark_notified(db, alert.id)
        return sent

    @classmethod
    async def _render_alert_message(
        cls,
        db: AsyncSession,
        alert: AlertLogModel,
        extra_context: Dict[str, Any]
    ) -> tuple[str, str]:
        template_code = cls._get_template_code(alert)
        if not template_code:
            return "", ""

        template = await SysNotifyTemplateCRUD.get_by_code(db, template_code)
        if template and template.is_enabled != 1:
            return "", ""

        context = await cls._build_alert_context(db, alert, extra_context)
        title = template.title if template and template.title else "IoT 卡片提醒"
        content = template.content if template else cls._default_alert_content(alert)

        return cls._safe_format(title, context), cls._safe_format(content, context)

    @classmethod
    async def _build_alert_context(
        cls,
        db: AsyncSession,
        alert: AlertLogModel,
        extra_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        context: Dict[str, Any] = {
            "alert_id": alert.id,
            "alert_level": alert.alert_level.value if alert.alert_level else "",
            "target_type": alert.target_type.value if alert.target_type else "",
            "target_name": alert.target_name or "",
            "usage_percent": alert.usage_percent,
            "threshold": alert.threshold,
            "iccid": alert.target_name or "",
        }

        if alert.target_type and alert.target_type.value == "card":
            card = await db.get(IotCardModel, alert.target_id)
            if card:
                context.update({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn or "",
                    "data_used": card.data_used,
                    "data_total": card.data_total,
                    "expire_date": card.expired_at.isoformat() if card.expired_at else "",
                })
        elif alert.target_type and alert.target_type.value == "pool":
            pool = await db.get(TrafficPoolModel, alert.target_id)
            if pool:
                context.update({
                    "pool_name": pool.name,
                    "card_count": pool.card_count,
                    "data_used": pool.data_used,
                    "data_total": pool.data_total,
                })

        context.update(extra_context)
        return context

    @classmethod
    def _get_template_code(cls, alert: AlertLogModel) -> str:
        alert_level = alert.alert_level.value if alert.alert_level else ""
        target_type = alert.target_type.value if alert.target_type else ""
        if target_type == "pool":
            return cls.POOL_ALERT_TEMPLATE_CODES.get(alert_level, "")
        return cls.CARD_ALERT_TEMPLATE_CODES.get(alert_level, "")

    @staticmethod
    def _default_alert_content(alert: AlertLogModel) -> str:
        level = alert.alert_level.value if alert.alert_level else "warning"
        if level == AlertLevel.critical.value:
            return "您的卡片 {iccid} 流量已使用 {usage_percent}%，即将触发停卡，请尽快处理。"
        if level == AlertLevel.exceed.value:
            return "您的卡片 {iccid} 已触发停卡告警，原因：{reason}。"
        return "您的卡片 {iccid} 流量已使用 {usage_percent}%，请及时关注。"

    @staticmethod
    def _safe_format(template: str, context: Dict[str, Any]) -> str:
        class SafeDict(dict):
            def __missing__(self, key: str) -> str:
                return ""

        return template.format_map(SafeDict({
            key: "" if value is None else value
            for key, value in context.items()
        }))

    @staticmethod
    def _is_user_email_notify_enabled(alert_notify: Any) -> bool:
        if alert_notify in (None, ""):
            return True
        if isinstance(alert_notify, str):
            try:
                alert_notify = json.loads(alert_notify)
            except json.JSONDecodeError:
                return True
        if isinstance(alert_notify, dict):
            return bool(alert_notify.get("email", True))
        return True
