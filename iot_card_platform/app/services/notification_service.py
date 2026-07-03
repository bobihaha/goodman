"""
通知服务
"""
import asyncio
import html
import json
import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crud.system_crud import SysConfigCRUD, SysNotifyTemplateCRUD
from app.crud.suspend_crud import AlertLogCRUD
from app.db.models.iot_card import IotCardModel
from app.db.models.package import CARRIER_NAMES
from app.db.models.pool import TrafficPoolModel
from app.db.models.suspend import AlertLevel, AlertLogModel, AlertTargetType
from app.db.models.sys_user import SysUserModel
from app.utils.timezone import beijing_now

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
        content: str,
        html_content: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
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
        if html_content:
            message.add_alternative(html_content, subtype="html")

        for attachment in attachments or []:
            data = attachment.get("data", b"")
            if hasattr(data, "getvalue"):
                data = data.getvalue()
            if isinstance(data, str):
                data = data.encode("utf-8")
            message.add_attachment(
                data,
                maintype=attachment.get("maintype", "application"),
                subtype=attachment.get("subtype", "octet-stream"),
                filename=attachment.get("filename", "attachment.bin")
            )

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

        if alert.target_type and alert.target_type.value in {"card", "pool"}:
            return await cls.send_pending_usage_alerts_for_user(db, alert.user_id)

        context = await cls._build_alert_context(db, alert, extra_context or {})
        subject, content = await cls._render_alert_message(db, alert, context)
        html_content = None
        if not subject or not content:
            return False

        try:
            sent = await cls.send_email(db, user.email, subject, content, html_content=html_content)
        except Exception as exc:
            logger.exception("发送告警邮件失败 alert_id=%s error=%s", alert.id, exc)
            return False

        if sent:
            await AlertLogCRUD.mark_notified(db, alert.id)
        return sent

    @classmethod
    async def send_pending_usage_alerts_for_user(cls, db: AsyncSession, user_id: int) -> bool:
        """按用户聚合发送未通知的流量池和非池单卡用量提醒。"""
        user = await db.get(SysUserModel, user_id)
        if not user or not user.email:
            return False
        if not cls._is_user_email_notify_enabled(user.alert_notify):
            return False

        result = await db.execute(
            select(AlertLogModel)
            .where(
                AlertLogModel.is_deleted == 0,
                AlertLogModel.user_id == user_id,
                AlertLogModel.notified == 0,
                AlertLogModel.target_type.in_([AlertTargetType.card, AlertTargetType.pool]),
            )
            .order_by(AlertLogModel.created_at.asc(), AlertLogModel.id.asc())
        )
        alerts = list(result.scalars().all())
        if not alerts:
            return False

        pool_alerts = []
        card_alerts = []
        for item in alerts:
            context = await cls._build_alert_context(db, item, {})
            if item.target_type and item.target_type.value == "pool":
                pool_alerts.append(context)
            elif item.target_type and item.target_type.value == "card":
                card_alerts.append(context)

        subject, content, html_content = cls._render_usage_summary_message(
            customer_name=user.name or user.account,
            pool_alerts=pool_alerts,
            card_alerts=card_alerts
        )
        try:
            sent = await cls.send_email(db, user.email, subject, content, html_content=html_content)
        except Exception as exc:
            logger.exception("发送用量汇总邮件失败 user_id=%s error=%s", user_id, exc)
            return False

        if sent:
            for item in alerts:
                await AlertLogCRUD.mark_notified(db, item.id)
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
                carrier_value = card.carrier.value if card.carrier else ""
                context.update({
                    "iccid": card.iccid,
                    "msisdn": card.msisdn or "",
                    "carrier": CARRIER_NAMES.get(carrier_value, carrier_value),
                    "package_name": card.get_spec_name(),
                    "data_used": card.data_used,
                    "data_total": card.data_total,
                    "data_remaining": max(0, (card.data_total or 0) - (card.data_used or 0)),
                    "expire_date": card.expired_at.isoformat() if card.expired_at else "",
                    "suspend_time": card.suspend_at.strftime("%Y-%m-%d %H:%M:%S") if card.suspend_at else "",
                    "status_text": cls._resolve_card_alert_status_text(alert, card),
                })
        elif alert.target_type and alert.target_type.value == "pool":
            pool = await db.get(TrafficPoolModel, alert.target_id)
            if pool:
                carrier_value = pool.carrier.value if pool.carrier else ""
                thresholds = [
                    item for item in [
                        pool.alert_threshold_1,
                        pool.alert_threshold_2,
                        pool.alert_threshold_3
                    ]
                    if item is not None
                ]
                context.update({
                    "pool_name": pool.name,
                    "carrier": CARRIER_NAMES.get(carrier_value, carrier_value),
                    "pool_specification": pool._format_flow_size(),
                    "card_count": pool.card_count,
                    "data_used": pool.data_used,
                    "data_total": pool.data_total,
                    "remaining_flow": pool.get_data_remain(),
                    "thresholds": " / ".join(f"{item}%" for item in thresholds),
                    "sync_time": pool.last_sync_at.strftime("%Y-%m-%d %H:%M:%S") if pool.last_sync_at else "",
                })

        context.update(extra_context)
        return context

    @classmethod
    async def send_usage_summary_email(
        cls,
        db: AsyncSession,
        to_email: str,
        customer_name: str,
        pool_alerts: Optional[List[Dict[str, Any]]] = None,
        card_alerts: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """发送流量池和非池单卡合并的用量提醒邮件"""
        subject, content, html_content = cls._render_usage_summary_message(
            customer_name=customer_name,
            pool_alerts=pool_alerts or [],
            card_alerts=card_alerts or []
        )
        return await cls.send_email(db, to_email, subject, content, html_content=html_content)

    @classmethod
    def _render_usage_summary_message(
        cls,
        customer_name: str,
        pool_alerts: List[Dict[str, Any]],
        card_alerts: List[Dict[str, Any]]
    ) -> tuple[str, str, str]:
        now = beijing_now()
        remind_time = now.strftime("%Y-%m-%d %H:%M:%S")
        subject = f"物联网卡用量提醒：{customer_name} {now.strftime('%Y-%m-%d')}"
        text_content = (
            "您好，\n\n"
            "以下为当前物联网卡用量提醒汇总，请及时关注并处理。\n\n"
            f"流量池提醒数量：{len(pool_alerts)}\n"
            f"非流量池单卡提醒数量：{len(card_alerts)}\n"
            f"提醒时间：{remind_time}\n\n"
            "物联网卡管理平台"
        )
        html_content = f"""<!doctype html>
<html>
<body style="font-family: Arial, 'Microsoft YaHei', sans-serif; color: #1f2933; line-height: 1.6;">
  <p>您好，</p>
  <p>以下为当前物联网卡用量提醒汇总，请及时关注并处理。</p>
  <h3 style="margin: 18px 0 8px;">一、流量池用量提醒</h3>
  {cls._render_pool_alert_table(pool_alerts)}
  <h3 style="margin: 18px 0 8px;">二、非流量池单卡用量提醒</h3>
  {cls._render_card_alert_table(card_alerts)}
  <p style="margin-top: 18px;">请根据实际业务情况及时补充流量、调整使用或联系管理员处理。</p>
  <p>物联网卡管理平台</p>
</body>
</html>"""
        return subject, text_content, html_content

    @classmethod
    def _render_pool_alert_table(cls, alerts: List[Dict[str, Any]]) -> str:
        headers = ["流量池", "运营商", "流量池规格", "已用流量", "总流量", "剩余流量", "当前使用率", "触发阈值", "全部阈值", "同步时间"]
        if not alerts:
            rows = '<tr><td colspan="10" style="text-align:center;color:#999;">暂无流量池用量提醒</td></tr>'
        else:
            rows = "".join(
                "<tr>"
                f"<td>{cls._html_value(item.get('pool_name') or item.get('target_name'))}</td>"
                f"<td>{cls._html_value(item.get('carrier'))}</td>"
                f"<td>{cls._html_value(item.get('pool_specification'))}</td>"
                f"<td>{cls._html_value(cls._format_flow_value(item.get('used_flow', item.get('data_used'))))}</td>"
                f"<td>{cls._html_value(cls._format_flow_value(item.get('total_flow', item.get('data_total'))))}</td>"
                f"<td>{cls._html_value(cls._format_flow_value(item.get('remaining_flow')))}</td>"
                f"<td>{cls._html_value(cls._format_percent(item.get('usage_percent')))}</td>"
                f"<td>{cls._html_value(cls._format_percent(item.get('threshold')))}</td>"
                f"<td>{cls._html_value(item.get('thresholds'))}</td>"
                f"<td>{cls._html_value(item.get('sync_time'))}</td>"
                "</tr>"
                for item in alerts
            )
        return cls._render_table(headers, rows)

    @classmethod
    def _render_card_alert_table(cls, alerts: List[Dict[str, Any]]) -> str:
        headers = ["ICCID", "电话号码", "运营商", "当前套餐", "已用流量", "总流量", "当前使用率", "触发阈值", "提醒级别", "处理状态"]
        if not alerts:
            rows = '<tr><td colspan="10" style="text-align:center;color:#999;">暂无非流量池单卡用量提醒</td></tr>'
        else:
            rows = "".join(
                "<tr>"
                f"<td>{cls._html_value(item.get('iccid') or item.get('target_name'))}</td>"
                f"<td>{cls._html_value(item.get('msisdn'))}</td>"
                f"<td>{cls._html_value(item.get('carrier'))}</td>"
                f"<td>{cls._html_value(item.get('package_name'))}</td>"
                f"<td>{cls._html_value(cls._format_flow_value(item.get('data_used')))}</td>"
                f"<td>{cls._html_value(cls._format_flow_value(item.get('data_total')))}</td>"
                f"<td>{cls._html_value(cls._format_percent(item.get('usage_percent')))}</td>"
                f"<td>{cls._html_value(cls._format_percent(item.get('threshold')))}</td>"
                f"<td>{cls._html_value(cls._alert_level_name(item.get('alert_level')))}</td>"
                f"<td>{cls._html_value(item.get('status_text') or cls._alert_status_text(item.get('alert_level'), item.get('threshold')))}</td>"
                "</tr>"
                for item in alerts
            )
        return cls._render_table(headers, rows)

    @staticmethod
    def _render_table(headers: List[str], rows: str) -> str:
        header_html = "".join(
            f'<th style="border:1px solid #d9d9d9;padding:6px;background:#f5f7fa;text-align:left;">{html.escape(header)}</th>'
            for header in headers
        )
        return (
            '<table border="0" cellspacing="0" cellpadding="0" style="border-collapse:collapse;width:100%;font-size:13px;">'
            f"<thead><tr>{header_html}</tr></thead>"
            f"<tbody>{rows}</tbody>"
            "</table>"
        )

    @staticmethod
    def _html_value(value: Any) -> str:
        if value in (None, ""):
            return "-"
        return html.escape(str(value))

    @staticmethod
    def _format_flow_value(value: Any) -> str:
        if value in (None, ""):
            return "-"
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        if number == int(number):
            return f"{int(number)} MB"
        return f"{number:.3f} MB"

    @staticmethod
    def _format_percent(value: Any) -> str:
        if value in (None, ""):
            return "-"
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        if number == int(number):
            return f"{int(number)}%"
        return f"{number:.2f}%"

    @staticmethod
    def _alert_level_name(value: Any) -> str:
        if value == AlertLevel.critical.value:
            return "紧急预警"
        if value == AlertLevel.exceed.value:
            return "已超限/已停卡"
        return "普通预警"

    @staticmethod
    def _alert_status_text(alert_level: Any, threshold: Any) -> str:
        try:
            threshold_value = int(float(threshold))
        except (TypeError, ValueError):
            threshold_value = 0
        if alert_level == AlertLevel.exceed.value or threshold_value >= 100:
            return "已超限，待停卡处理"
        return "待关注"

    @staticmethod
    def _resolve_card_alert_status_text(alert: AlertLogModel, card: IotCardModel) -> str:
        if not alert.alert_level or alert.alert_level.value != AlertLevel.exceed.value:
            return "待关注"
        suspend_type = card.suspend_type.value if card.suspend_type else ""
        if suspend_type == "card_exceed" and card.suspend_at:
            return "已按策略停卡"
        return "已超限，待停卡处理"

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
