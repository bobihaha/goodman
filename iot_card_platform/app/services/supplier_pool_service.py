"""
供应商侧流量池管理服务
"""
import logging
from calendar import monthrange
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.supplier_api import get_supplier_client
from app.db.models.supplier import SupplierModel, SupplierStatus
from app.db.models.supplier_pool import SupplierTrafficPoolHistoryModel, SupplierTrafficPoolModel
from app.services.notification_service import NotificationService
from app.utils.exceptions import BusinessException
from app.utils.timezone import beijing_now

logger = logging.getLogger(__name__)


class SupplierTrafficPoolService:
    """供应商侧流量池管理"""

    DEFAULT_ALERT_THRESHOLDS = "60,80,100"
    SORT_FIELDS = {
        "usage_percent": SupplierTrafficPoolModel.usage_percent,
        "pool_specification": SupplierTrafficPoolModel.pool_specification,
        "used_flow": SupplierTrafficPoolModel.used_flow,
        "total_flow": SupplierTrafficPoolModel.total_flow,
        "remaining_flow": SupplierTrafficPoolModel.remaining_flow,
        "updated_at": SupplierTrafficPoolModel.updated_at,
        "last_sync_at": SupplierTrafficPoolModel.last_sync_at,
    }

    @staticmethod
    def _as_int(value: Any) -> Optional[int]:
        if value in (None, ""):
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _truncate_error(value: Any, limit: int = 500) -> str:
        message = str(value)
        return message if len(message) <= limit else f"{message[:limit - 3]}..."

    @classmethod
    def _parse_alert_thresholds(cls, raw_value: Any) -> List[int]:
        if raw_value in (None, ""):
            raw_value = cls.DEFAULT_ALERT_THRESHOLDS
        if isinstance(raw_value, int):
            values = [raw_value]
        elif isinstance(raw_value, list):
            values = raw_value
        else:
            values = str(raw_value).replace(";", ",").split(",")

        thresholds = set()
        for item in values:
            try:
                threshold = int(float(str(item).strip()))
            except (TypeError, ValueError):
                continue
            if 0 <= threshold <= 100:
                thresholds.add(threshold)
        return sorted(thresholds)

    @classmethod
    def _serialize_alert_thresholds(cls, values: Optional[List[int]]) -> str:
        thresholds = cls._parse_alert_thresholds(values)
        return ",".join(str(item) for item in thresholds) if thresholds else ""

    @staticmethod
    def _month_estimate_fields(
        used_flow: Any,
        total_flow: Any,
        sync_at: Optional[datetime] = None,
        record_month: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = datetime.now()
        current_month = now.strftime("%Y-%m")
        estimate_base = sync_at or now
        if (record_month and record_month != current_month) or (
            not record_month and sync_at and estimate_base.strftime("%Y-%m") != current_month
        ):
            return {
                "estimated_monthly_used_flow": None,
                "estimated_month_end_remaining_flow": None,
                "estimated_usage_percent": None,
                "estimate_used_days": None,
                "estimate_month_days": None,
            }

        month_days = monthrange(estimate_base.year, estimate_base.month)[1]
        used_days = max(1, min(estimate_base.day, month_days))
        used_value = float(used_flow or 0)
        total_value = float(total_flow or 0)
        estimated_used = used_value / used_days * month_days
        estimated_remaining = total_value - estimated_used
        estimated_percent = (estimated_used / total_value * 100) if total_value else 0
        return {
            "estimated_monthly_used_flow": round(estimated_used, 3),
            "estimated_month_end_remaining_flow": round(estimated_remaining, 3),
            "estimated_usage_percent": round(estimated_percent, 2),
            "estimate_used_days": used_days,
            "estimate_month_days": month_days,
        }

    def _enrich_pool_usage_estimate(self, item: Dict[str, Any]) -> Dict[str, Any]:
        item.update(
            self._month_estimate_fields(
                item.get("used_flow"),
                item.get("total_flow"),
                item.get("last_sync_at_raw"),
            )
        )
        item.pop("last_sync_at_raw", None)
        return item

    def _enrich_history_usage_estimate(self, item: Dict[str, Any]) -> Dict[str, Any]:
        item.update(
            self._month_estimate_fields(
                item.get("used_flow"),
                item.get("total_flow"),
                item.get("sync_at_raw"),
                item.get("record_month"),
            )
        )
        item.pop("sync_at_raw", None)
        return item

    def _get_sort_expression(self, order_by: str):
        if order_by == "estimated_monthly_used_flow":
            now = datetime.now()
            month_days = monthrange(now.year, now.month)[1]
            used_days = max(1, now.day)
            return SupplierTrafficPoolModel.used_flow * month_days / used_days
        if order_by == "estimated_month_end_remaining_flow":
            now = datetime.now()
            month_days = monthrange(now.year, now.month)[1]
            used_days = max(1, now.day)
            return SupplierTrafficPoolModel.total_flow - (SupplierTrafficPoolModel.used_flow * month_days / used_days)
        return self.SORT_FIELDS.get(order_by, SupplierTrafficPoolModel.usage_percent)

    async def get_list(
        self,
        db: AsyncSession,
        supplier_name: Optional[str] = None,
        carrier: Optional[str] = None,
        pool_specification: Optional[int] = None,
        order_by: str = "usage_percent",
        order_dir: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        conditions = [SupplierTrafficPoolModel.is_deleted == 0]
        if supplier_name:
            like_value = f"%{supplier_name.strip()}%"
            conditions.append(SupplierTrafficPoolModel.supplier_name.like(like_value))
        if carrier:
            conditions.append(SupplierTrafficPoolModel.carrier == carrier)
        if pool_specification is not None:
            conditions.append(SupplierTrafficPoolModel.pool_specification == pool_specification)

        total_result = await db.execute(
            select(func.count()).select_from(SupplierTrafficPoolModel).where(*conditions)
        )
        total = total_result.scalar() or 0

        sort_column = self._get_sort_expression(order_by)
        sort_expr = sort_column.asc() if order_dir == "asc" else sort_column.desc()
        result = await db.execute(
            select(SupplierTrafficPoolModel)
            .where(*conditions)
            .order_by(
                sort_expr,
                SupplierTrafficPoolModel.updated_at.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = []
        for pool in result.scalars().all():
            item = pool.to_dict()
            item["last_sync_at_raw"] = pool.last_sync_at
            items.append(self._enrich_pool_usage_estimate(item))
        return items, total

    async def update_alert(
        self,
        db: AsyncSession,
        pool_id: int,
        alert_threshold: Optional[int],
        alert_thresholds: Optional[List[int]],
        alert_emails: Optional[str],
    ) -> Dict[str, Any]:
        pool = await db.get(SupplierTrafficPoolModel, pool_id)
        if not pool or pool.is_deleted:
            raise BusinessException(code=404, msg="供应商流量池不存在")

        pool.alert_threshold = alert_threshold
        pool.alert_thresholds = self._serialize_alert_thresholds(alert_thresholds)
        pool.alert_emails = alert_emails
        if not pool.alert_thresholds:
            pool.last_alert_at = None
            pool.last_alert_usage_percent = None
            pool.last_alert_threshold = None
        await db.commit()
        await db.refresh(pool)
        return pool.to_dict()

    async def get_detail(
        self,
        db: AsyncSession,
        pool_id: int,
        months: int = 12,
    ) -> Dict[str, Any]:
        pool = await db.get(SupplierTrafficPoolModel, pool_id)
        if not pool or pool.is_deleted:
            raise BusinessException(code=404, msg="供应商流量池不存在")

        normalized_months = min(max(months, 1), 36)
        result = await db.execute(
            select(SupplierTrafficPoolHistoryModel)
            .where(
                SupplierTrafficPoolHistoryModel.supplier_pool_id == pool.id,
                SupplierTrafficPoolHistoryModel.is_deleted == 0,
            )
            .order_by(SupplierTrafficPoolHistoryModel.record_month.desc())
            .limit(normalized_months)
        )
        histories = []
        for history in reversed(result.scalars().all()):
            item = history.to_dict()
            item["sync_at_raw"] = history.sync_at
            histories.append(self._enrich_history_usage_estimate(item))
        pool_dict = pool.to_dict()
        pool_dict["last_sync_at_raw"] = pool.last_sync_at
        return {
            "pool": self._enrich_pool_usage_estimate(pool_dict),
            "histories": histories,
        }

    async def export_history(
        self,
        db: AsyncSession,
        pool_id: int,
        months: int = 36,
    ) -> List[Dict[str, Any]]:
        detail = await self.get_detail(db, pool_id, months)
        pool = detail["pool"]
        rows = []
        for item in detail["histories"]:
            estimated_used = item.get("estimated_monthly_used_flow")
            estimated_remaining = item.get("estimated_month_end_remaining_flow")
            estimated_percent = item.get("estimated_usage_percent")
            rows.append({
                "供应商": item.get("supplier_name") or pool.get("supplier_name") or "",
                "运营商": item.get("carrier") or pool.get("carrier") or "",
                "流量池编码": item.get("supplier_pool_code") or "",
                "流量池名称": item.get("supplier_pool_name") or "",
                "月份": item.get("record_month") or "",
                "规格(MB)": item.get("pool_specification"),
                "总量(MB)": round(float(item.get("total_flow") or 0), 3),
                "已用(MB)": round(float(item.get("used_flow") or 0), 3),
                "剩余(MB)": round(float(item.get("remaining_flow") or 0), 3),
                "使用率(%)": round(float(item.get("usage_percent") or 0), 2),
                "本月预估使用量(MB)": estimated_used if estimated_used is not None else "",
                "预计月底剩余(MB)": estimated_remaining if estimated_remaining is not None else "",
                "预估使用率(%)": estimated_percent if estimated_percent is not None else "",
                "总卡数": item.get("total_card_count") or 0,
                "激活卡数": item.get("active_card_count") or 0,
                "同步时间": item.get("sync_at") or "",
            })
        return rows

    async def sync_supplier_pools(
        self,
        db: AsyncSession,
        supplier_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        suppliers = await self._get_suppliers(db, supplier_id)
        total_pools = 0
        success_pools = 0
        failed_pools = 0
        success_suppliers = 0
        failed_suppliers = 0
        details = []

        for supplier in suppliers:
            try:
                client = get_supplier_client(
                    supplier_id=supplier.id,
                    api_url=supplier.api_url or "",
                    api_key=supplier.api_key or "",
                    api_secret=supplier.api_secret or "",
                    supplier_code=supplier.code,
                    api_config=supplier.api_config,
                )
                rows = await client.get_traffic_pool_usage()
                total_pools += len(rows)
                alert_failed_count = 0
                for row in rows:
                    pool = await self._upsert_pool(db, supplier, row)
                    await self._upsert_monthly_history(db, pool)
                    alert_error = await self._send_threshold_alert_if_needed(db, pool, supplier)
                    if alert_error:
                        alert_failed_count += 1
                        pool.sync_error = self._truncate_error(f"邮件提醒失败：{alert_error}")
                    success_pools += 1
                success_suppliers += 1
                details.append({
                    "supplier_id": supplier.id,
                    "supplier_name": supplier.name,
                    "count": len(rows),
                    "success_pools": len(rows),
                    "alert_failed_count": alert_failed_count,
                    "status": "success",
                })
            except Exception as exc:
                failed_suppliers += 1
                logger.exception("同步供应商流量池失败 supplier_id=%s error=%s", supplier.id, exc)
                marked_count = await self._mark_supplier_pools_failed(db, supplier, exc)
                failed_pools += marked_count
                details.append({
                    "supplier_id": supplier.id,
                    "supplier_name": supplier.name,
                    "status": "failed",
                    "reason": str(exc),
                    "failed_pools": marked_count,
                })

        await db.commit()
        return {
            "total": total_pools,
            "success": success_pools,
            "failed": failed_pools,
            "total_pools": total_pools,
            "success_pools": success_pools,
            "failed_pools": failed_pools,
            "total_suppliers": len(suppliers),
            "success_suppliers": success_suppliers,
            "failed_suppliers": failed_suppliers,
            "details": details,
        }

    async def _get_suppliers(self, db: AsyncSession, supplier_id: Optional[int]) -> List[SupplierModel]:
        conditions = [
            SupplierModel.is_deleted == 0,
            SupplierModel.status == SupplierStatus.enable,
        ]
        if supplier_id:
            conditions.append(SupplierModel.id == supplier_id)
        result = await db.execute(select(SupplierModel).where(*conditions).order_by(SupplierModel.id.asc()))
        suppliers = list(result.scalars().all())
        if supplier_id and not suppliers:
            raise BusinessException(code=404, msg="供应商不存在或未启用")
        return suppliers

    async def _upsert_pool(
        self,
        db: AsyncSession,
        supplier: SupplierModel,
        row: Dict[str, Any],
    ) -> SupplierTrafficPoolModel:
        supplier_pool_code = str(row.get("supplier_pool_code") or "").strip()
        if not supplier_pool_code:
            supplier_pool_code = f"{supplier.id}:{row.get('supplier_pool_name') or row.get('carrier') or 'unknown'}"

        result = await db.execute(
            select(SupplierTrafficPoolModel).where(
                SupplierTrafficPoolModel.supplier_id == supplier.id,
                SupplierTrafficPoolModel.supplier_pool_code == supplier_pool_code,
                SupplierTrafficPoolModel.is_deleted == 0,
            )
        )
        pool = result.scalar_one_or_none()
        if not pool:
            pool = SupplierTrafficPoolModel(
                supplier_id=supplier.id,
                supplier_pool_code=supplier_pool_code,
                alert_threshold=None,
                alert_thresholds=self.DEFAULT_ALERT_THRESHOLDS,
                alert_emails=supplier.contact_email,
            )
            db.add(pool)

        now = datetime.now()
        pool.supplier_name = supplier.name
        pool.supplier_pool_name = row.get("supplier_pool_name")
        pool.carrier = row.get("carrier")
        pool.pool_specification = self._as_int(row.get("pool_specification"))
        pool.total_flow = float(row.get("total_flow") or 0)
        pool.used_flow = float(row.get("used_flow") or 0)
        pool.remaining_flow = float(row.get("remaining_flow") or max(0, pool.total_flow - pool.used_flow))
        pool.package_flow = float(row.get("package_flow") or 0)
        pool.usage_percent = float(row.get("usage_percent") or 0)
        pool.total_card_count = int(row.get("total_card_count") or 0)
        pool.active_card_count = int(row.get("active_card_count") or 0)
        pool.suspended_card_count = int(row.get("suspended_card_count") or 0)
        pool.stock_card_count = int(row.get("stock_card_count") or 0)
        pool.testing_card_count = int(row.get("testing_card_count") or 0)
        pool.cancelled_card_count = int(row.get("cancelled_card_count") or 0)
        pool.activation_ready_count = int(row.get("activation_ready_count") or 0)
        pool.last_sync_at = now
        pool.sync_status = "success"
        pool.sync_error = None
        pool.raw_data = row.get("raw_data") or row
        await db.flush()
        return pool

    async def _upsert_monthly_history(
        self,
        db: AsyncSession,
        pool: SupplierTrafficPoolModel,
    ) -> SupplierTrafficPoolHistoryModel:
        sync_at = pool.last_sync_at or datetime.now()
        record_month = sync_at.strftime("%Y-%m")
        result = await db.execute(
            select(SupplierTrafficPoolHistoryModel).where(
                SupplierTrafficPoolHistoryModel.supplier_pool_id == pool.id,
                SupplierTrafficPoolHistoryModel.record_month == record_month,
                SupplierTrafficPoolHistoryModel.is_deleted == 0,
            )
        )
        history = result.scalar_one_or_none()
        if not history:
            history = SupplierTrafficPoolHistoryModel(
                supplier_pool_id=pool.id,
                record_month=record_month,
            )
            db.add(history)

        history.supplier_id = pool.supplier_id
        history.supplier_name = pool.supplier_name
        history.supplier_pool_code = pool.supplier_pool_code
        history.supplier_pool_name = pool.supplier_pool_name
        history.carrier = pool.carrier
        history.pool_specification = pool.pool_specification
        history.total_flow = pool.total_flow
        history.used_flow = pool.used_flow
        history.remaining_flow = pool.remaining_flow
        history.package_flow = pool.package_flow
        history.usage_percent = pool.usage_percent
        history.total_card_count = pool.total_card_count
        history.active_card_count = pool.active_card_count
        history.sync_at = sync_at
        await db.flush()
        return history

    async def _mark_supplier_pools_failed(
        self,
        db: AsyncSession,
        supplier: SupplierModel,
        exc: Exception,
    ) -> int:
        error = self._truncate_error(exc)
        result = await db.execute(
            select(SupplierTrafficPoolModel).where(
                SupplierTrafficPoolModel.supplier_id == supplier.id,
                SupplierTrafficPoolModel.is_deleted == 0,
            )
        )
        pools = list(result.scalars().all())
        now = datetime.now()
        for pool in pools:
            pool.supplier_name = supplier.name
            pool.sync_status = "failed"
            pool.sync_error = error
            pool.last_sync_at = now
        await db.flush()
        return len(pools)

    async def _send_threshold_alert_if_needed(
        self,
        db: AsyncSession,
        pool: SupplierTrafficPoolModel,
        supplier: SupplierModel,
    ) -> Optional[str]:
        thresholds = self._parse_alert_thresholds(pool.alert_thresholds or pool.alert_threshold)
        if not thresholds:
            return None
        reached_thresholds = [item for item in thresholds if pool.usage_percent >= item]
        if not reached_thresholds:
            return None
        alert_threshold = max(reached_thresholds)
        if (
            pool.last_alert_at
            and pool.last_alert_at >= beijing_now() - timedelta(hours=12)
            and (pool.last_alert_threshold or 0) >= alert_threshold
        ):
            return None

        recipients = self._resolve_recipients(pool.alert_emails or supplier.contact_email)
        if not recipients:
            return None

        pool_alert = {
            "pool_name": pool.supplier_pool_name or pool.supplier_pool_code,
            "carrier": pool.carrier or "-",
            "pool_specification": f"{pool.pool_specification} MB" if pool.pool_specification is not None else "-",
            "used_flow": pool.used_flow,
            "total_flow": pool.total_flow,
            "remaining_flow": pool.remaining_flow,
            "usage_percent": pool.usage_percent,
            "threshold": alert_threshold,
            "thresholds": " / ".join(f"{item}%" for item in thresholds),
            "sync_time": pool.last_sync_at.strftime("%Y-%m-%d %H:%M:%S") if pool.last_sync_at else "-",
        }

        sent_any = False
        errors = []
        for email in recipients:
            try:
                sent = await NotificationService.send_usage_summary_email(
                    db=db,
                    to_email=email,
                    customer_name=pool.supplier_pool_name or pool.supplier_pool_code,
                    pool_alerts=[pool_alert],
                    card_alerts=[]
                )
                sent_any = sent_any or sent
            except Exception as exc:
                logger.exception(
                    "供应商流量池邮件提醒失败 supplier_id=%s pool_id=%s email=%s error=%s",
                    supplier.id,
                    pool.id,
                    email,
                    exc,
                )
                errors.append(f"{email}: {exc}")

        if sent_any:
            pool.last_alert_at = beijing_now()
            pool.last_alert_usage_percent = pool.usage_percent
            pool.last_alert_threshold = alert_threshold
        return "; ".join(errors) if errors else None

    @staticmethod
    def _resolve_recipients(raw_value: Optional[str]) -> List[str]:
        if not raw_value:
            return []
        return [item.strip() for item in raw_value.replace(";", ",").split(",") if item.strip()]


supplier_traffic_pool_service = SupplierTrafficPoolService()
