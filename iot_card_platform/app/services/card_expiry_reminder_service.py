"""
物联网卡到期邮件提醒服务
"""
from calendar import monthrange
from collections import defaultdict
from datetime import date
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.iot_card import CardStatus, IotCardModel
from app.db.models.package import CARRIER_NAMES
from app.db.models.sys_log import SysConfigModel
from app.db.models.sys_user import SysUserModel
from app.services.notification_service import NotificationService
from app.utils.timezone import beijing_now


class CardExpiryReminderService:
    """到期卡汇总提醒"""

    REMINDER_DAYS = {10, 15}
    ACTIVE_STATUSES = [CardStatus.activated, CardStatus.testing, CardStatus.silent]

    @classmethod
    async def send_monthly_expiry_reminders(
        cls,
        db: AsyncSession,
        today: Optional[date] = None,
        force: bool = False
    ) -> Dict[str, int]:
        """发送本月到期卡提醒。默认仅每月 10 号、15 号执行。"""
        today = today or beijing_now().date()
        if not force and today.day not in cls.REMINDER_DAYS:
            return {"users": 0, "cards": 0, "sent": 0, "skipped": 0, "failed": 0}

        month_start = today.replace(day=1)
        month_end = today.replace(day=monthrange(today.year, today.month)[1])

        result = await db.execute(
            select(IotCardModel, SysUserModel)
            .join(SysUserModel, IotCardModel.user_id == SysUserModel.id)
            .where(
                IotCardModel.is_deleted == 0,
                IotCardModel.status.in_(cls.ACTIVE_STATUSES),
                IotCardModel.expired_at >= month_start,
                IotCardModel.expired_at <= month_end,
                SysUserModel.is_deleted == 0,
                SysUserModel.email.is_not(None),
                SysUserModel.email != "",
            )
            .order_by(SysUserModel.id.asc(), IotCardModel.expired_at.asc(), IotCardModel.iccid.asc())
        )

        grouped: Dict[int, Dict[str, Any]] = defaultdict(lambda: {"user": None, "cards": []})
        for card, user in result.all():
            grouped[user.id]["user"] = user
            grouped[user.id]["cards"].append(card)

        sent = 0
        skipped = 0
        failed = 0
        card_total = 0
        for item in grouped.values():
            user = item["user"]
            cards = item["cards"]
            card_total += len(cards)
            if not NotificationService._is_user_email_notify_enabled(user.alert_notify):
                skipped += 1
                continue
            marker_key = cls._marker_key(user.id, today)
            if not await cls._reserve_send_marker(db, marker_key):
                skipped += 1
                continue

            try:
                subject, content = cls._build_email_content(user, cards, today)
                filename = f"物联网卡到期明细_{cls._safe_filename(user.name or user.account)}_{today.strftime('%Y%m%d')}.xlsx"
                attachment = {
                    "filename": filename,
                    "data": cls._build_expiry_xlsx(user, cards),
                    "maintype": "application",
                    "subtype": "vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                }
                if await NotificationService.send_email(
                    db=db,
                    to_email=user.email,
                    subject=subject,
                    content=content,
                    attachments=[attachment]
                ):
                    await cls._mark_send_success(db, marker_key, len(cards))
                    sent += 1
                else:
                    await cls._release_send_marker(db, marker_key)
                    failed += 1
            except Exception:
                await cls._release_send_marker(db, marker_key)
                failed += 1

        return {"users": len(grouped), "cards": card_total, "sent": sent, "skipped": skipped, "failed": failed}

    @staticmethod
    def _marker_key(user_id: int, remind_date: date) -> str:
        return f"expiry_reminder_sent:{remind_date.strftime('%Y-%m')}:{remind_date.day}:{user_id}"

    @staticmethod
    async def _reserve_send_marker(db: AsyncSession, marker_key: str) -> bool:
        marker = SysConfigModel(
            config_key=marker_key,
            config_value="sending",
            config_type="string",
            description="到期卡邮件提醒发送标记",
            is_public=0,
        )
        db.add(marker)
        try:
            await db.commit()
            return True
        except IntegrityError:
            await db.rollback()
            return False

    @staticmethod
    async def _mark_send_success(db: AsyncSession, marker_key: str, card_count: int) -> None:
        result = await db.execute(
            select(SysConfigModel).where(
                SysConfigModel.config_key == marker_key,
                SysConfigModel.is_deleted == 0,
            )
        )
        marker = result.scalar_one_or_none()
        if marker:
            marker.config_value = f"sent:{card_count}:{beijing_now().strftime('%Y-%m-%d %H:%M:%S')}"
            await db.commit()

    @staticmethod
    async def _release_send_marker(db: AsyncSession, marker_key: str) -> None:
        result = await db.execute(
            select(SysConfigModel).where(
                SysConfigModel.config_key == marker_key,
                SysConfigModel.is_deleted == 0,
            )
        )
        marker = result.scalar_one_or_none()
        if marker:
            await db.delete(marker)
            await db.commit()

    @classmethod
    def _build_email_content(
        cls,
        user: SysUserModel,
        cards: List[IotCardModel],
        remind_date: date
    ) -> Tuple[str, str]:
        customer_name = user.name or user.account
        expire_dates = [card.expired_at for card in cards if card.expired_at]
        earliest = min(expire_dates).isoformat() if expire_dates else "-"
        latest = max(expire_dates).isoformat() if expire_dates else "-"
        expire_month = remind_date.strftime("%Y-%m")
        subject = f"物联网卡到期提醒：{customer_name} 本月有 {len(cards)} 张卡即将到期"
        content = (
            "您好，\n\n"
            f"您有 {len(cards)} 张物联网卡即将到期，详情请查看邮件附件"
            f"《物联网卡到期明细_{customer_name}_{remind_date.strftime('%Y%m%d')}.xlsx》。\n\n"
            "请及时处理续费，避免影响正常使用，并请在本月 20 号前反馈处理结果。\n\n"
            "本次提醒范围：\n"
            f"客户名称：{customer_name}\n"
            f"到期月份：{expire_month}\n"
            f"到期卡数量：{len(cards)} 张\n"
            f"最早到期日期：{earliest}\n"
            f"最晚到期日期：{latest}\n\n"
            "请在到期前完成续费或联系管理员处理。\n\n"
            "物联网卡管理平台"
        )
        return subject, content

    @classmethod
    def _build_expiry_xlsx(cls, user: SysUserModel, cards: List[IotCardModel]) -> bytes:
        headers = ["运营商", "IMSI", "ICCID", "电话号码", "套餐总量", "激活日期", "到期日期", "关联用户", "备注", "续费价格"]
        rows = []
        for card in cards:
            carrier_value = card.carrier.value if card.carrier else ""
            rows.append([
                CARRIER_NAMES.get(carrier_value, carrier_value),
                card.imsi or "",
                card.iccid or "",
                card.msisdn or "",
                card._format_flow_size(),
                card.activated_at.isoformat() if card.activated_at else "",
                card.expired_at.isoformat() if card.expired_at else "",
                user.name or user.account,
                card.remark or "",
                float(card.sale_price) if card.sale_price is not None else "",
            ])
        return cls._build_simple_xlsx(headers, rows)

    @staticmethod
    def _safe_filename(value: str) -> str:
        return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in value)[:60] or "客户"

    @staticmethod
    def _build_simple_xlsx(headers: List[str], rows: List[List[object]]) -> bytes:
        def column_name(index: int) -> str:
            name = ""
            current = index
            while current > 0:
                current, remainder = divmod(current - 1, 26)
                name = chr(65 + remainder) + name
            return name

        def cell_xml(row_index: int, col_index: int, value: object) -> str:
            cell_ref = f"{column_name(col_index)}{row_index}"
            if value is None:
                return f'<c r="{cell_ref}" t="inlineStr"><is><t></t></is></c>'
            if isinstance(value, bool):
                return f'<c r="{cell_ref}" t="b"><v>{1 if value else 0}</v></c>'
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return f'<c r="{cell_ref}"><v>{value}</v></c>'
            text = escape(str(value))
            return f'<c r="{cell_ref}" t="inlineStr"><is><t>{text}</t></is></c>'

        all_rows = [headers, *rows] if headers else rows
        sheet_rows = []
        for row_index, row in enumerate(all_rows, start=1):
            cells = "".join(cell_xml(row_index, col_index, value) for col_index, value in enumerate(row, start=1))
            sheet_rows.append(f'<row r="{row_index}">{cells}</row>')

        sheet_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetData>{"".join(sheet_rows)}</sheetData>'
            '</worksheet>'
        )
        workbook_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="到期明细" sheetId="1" r:id="rId1"/></sheets>'
            '</workbook>'
        )
        workbook_rels_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            'Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
            'Target="styles.xml"/>'
            '</Relationships>'
        )
        root_rels_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="xl/workbook.xml"/>'
            '</Relationships>'
        )
        styles_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
            '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
            '<borders count="1"><border/></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
            '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
            '</styleSheet>'
        )
        content_types_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/styles.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            '</Types>'
        )

        output = BytesIO()
        with ZipFile(output, "w", ZIP_DEFLATED) as zip_file:
            zip_file.writestr("[Content_Types].xml", content_types_xml)
            zip_file.writestr("_rels/.rels", root_rels_xml)
            zip_file.writestr("xl/workbook.xml", workbook_xml)
            zip_file.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
            zip_file.writestr("xl/styles.xml", styles_xml)
            zip_file.writestr("xl/worksheets/sheet1.xml", sheet_xml)
        return output.getvalue()


card_expiry_reminder_service = CardExpiryReminderService()
