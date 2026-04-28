#!/usr/bin/env python3
"""
续费异常巡检脚本

用途:
1. 扫最近 N 天的续费日志，检查本地到期日是否短于日志里应有的新到期日
2. 检查已激活但缺少激活日的卡
3. 对最近续费卡或指定 ICCID 拉供应商生命周期，检查本地/供应商到期日不一致

退出码:
0 = 未发现异常
2 = 发现异常
1 = 脚本执行失败
"""
from __future__ import annotations

import argparse
import asyncio
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select


DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass
class Anomaly:
    category: str
    iccid: str
    detail: str


def load_runtime_dependencies():
    from app.clients.supplier_api import get_supplier_client
    from app.crud.supplier_crud import supplier_crud
    from app.db.database import AsyncSessionLocal, engine
    from app.db.models.iot_card import CardStatus, IotCardModel
    from app.db.models.sys_log import SysOperationLogModel

    return {
        "get_supplier_client": get_supplier_client,
        "supplier_crud": supplier_crud,
        "AsyncSessionLocal": AsyncSessionLocal,
        "engine": engine,
        "CardStatus": CardStatus,
        "IotCardModel": IotCardModel,
        "SysOperationLogModel": SysOperationLogModel,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="巡检续费和套餐周期异常")
    parser.add_argument("--days", type=int, default=7, help="巡检最近多少天的续费日志，默认 7")
    parser.add_argument("--limit", type=int, default=200, help="最多检查多少条续费日志，默认 200")
    parser.add_argument(
        "--iccid",
        action="append",
        dest="iccids",
        default=[],
        help="指定要重点巡检的 ICCID，可重复传入"
    )
    parser.add_argument(
        "--skip-supplier-check",
        action="store_true",
        help="跳过供应商生命周期对账"
    )
    return parser.parse_args()


def parse_detail_dates(detail: Optional[str]) -> tuple[Optional[date], Optional[date]]:
    if not detail:
        return None, None
    matches = [datetime.strptime(item, "%Y-%m-%d").date() for item in DATE_PATTERN.findall(detail)]
    if len(matches) >= 2:
        return matches[0], matches[-1]
    if len(matches) == 1:
        return None, matches[0]
    return None, None


async def load_recent_renew_logs(days: int, limit: int) -> list[SysOperationLogModel]:
    runtime = load_runtime_dependencies()
    AsyncSessionLocal = runtime["AsyncSessionLocal"]
    SysOperationLogModel = runtime["SysOperationLogModel"]
    cutoff = datetime.now() - timedelta(days=days)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(SysOperationLogModel)
            .where(
                SysOperationLogModel.module == "cards",
                SysOperationLogModel.action == "renew",
                SysOperationLogModel.is_deleted == 0,
                SysOperationLogModel.created_at >= cutoff,
            )
            .order_by(SysOperationLogModel.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


async def load_cards(iccids: list[str]) -> dict[str, IotCardModel]:
    if not iccids:
        return {}
    runtime = load_runtime_dependencies()
    AsyncSessionLocal = runtime["AsyncSessionLocal"]
    IotCardModel = runtime["IotCardModel"]
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(IotCardModel).where(
                IotCardModel.iccid.in_(iccids),
                IotCardModel.is_deleted == 0,
            )
        )
        cards = list(result.scalars().all())
        return {card.iccid: card for card in cards}


async def check_activated_missing_dates() -> list[Anomaly]:
    runtime = load_runtime_dependencies()
    AsyncSessionLocal = runtime["AsyncSessionLocal"]
    CardStatus = runtime["CardStatus"]
    IotCardModel = runtime["IotCardModel"]
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(IotCardModel).where(
                IotCardModel.status == CardStatus.activated,
                IotCardModel.activated_at.is_(None),
                IotCardModel.is_deleted == 0,
            )
        )
        cards = list(result.scalars().all())

    anomalies = []
    for card in cards:
        anomalies.append(
            Anomaly(
                category="activated_missing_date",
                iccid=card.iccid,
                detail=f"status=activated 但 activated_at 为空，当前 expired_at={card.expired_at or '-'}"
            )
        )
    return anomalies


async def check_recent_renew_log_consistency(
    renew_logs: list[SysOperationLogModel],
    extra_iccids: list[str]
) -> tuple[list[Anomaly], list[str], dict[str, tuple[date, datetime]]]:
    latest_expectation: dict[str, tuple[date, datetime]] = {}
    for log in renew_logs:
        if not log.target_name:
            continue
        _, expected_new = parse_detail_dates(log.detail)
        if not expected_new:
            continue
        current = latest_expectation.get(log.target_name)
        if current is None or expected_new > current[0]:
            latest_expectation[log.target_name] = (expected_new, log.created_at)

    iccids = sorted(set(latest_expectation.keys()) | set(extra_iccids))
    card_map = await load_cards(iccids)
    anomalies = []

    for iccid, (expected_new, created_at) in latest_expectation.items():
        card = card_map.get(iccid)
        if not card:
            anomalies.append(
                Anomaly(
                    category="renewed_card_missing_local",
                    iccid=iccid,
                    detail=f"续费日志存在，但本地卡表不存在。日志时间={created_at}"
                )
            )
            continue
        if not card.expired_at:
            anomalies.append(
                Anomaly(
                    category="renewed_card_missing_expiry",
                    iccid=iccid,
                    detail=f"续费日志期望新到期={expected_new}，但本地 expired_at 为空"
                )
            )
            continue
        if card.expired_at < expected_new:
            anomalies.append(
                Anomaly(
                    category="renewed_card_local_shorter",
                    iccid=iccid,
                    detail=(
                        f"续费日志期望新到期={expected_new}，"
                        f"当前本地 expired_at={card.expired_at}"
                    )
                )
            )

    return anomalies, iccids, latest_expectation


async def check_supplier_expiry_mismatches(
    iccids: list[str],
    latest_expectation: Optional[dict[str, tuple[date, datetime]]] = None
) -> list[Anomaly]:
    if not iccids:
        return []

    runtime = load_runtime_dependencies()
    AsyncSessionLocal = runtime["AsyncSessionLocal"]
    IotCardModel = runtime["IotCardModel"]
    supplier_crud = runtime["supplier_crud"]
    get_supplier_client = runtime["get_supplier_client"]

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(IotCardModel).where(
                IotCardModel.iccid.in_(iccids),
                IotCardModel.is_deleted == 0,
            )
        )
        cards = list(result.scalars().all())

        anomalies = []
        for card in cards:
            if not card.supplier_id:
                continue

            supplier = await supplier_crud.get_by_id(db, card.supplier_id)
            if not supplier:
                anomalies.append(
                    Anomaly(
                        category="supplier_missing",
                        iccid=card.iccid,
                        detail=f"supplier_id={card.supplier_id} 不存在"
                    )
                )
                continue

            try:
                client = get_supplier_client(
                    supplier_id=card.supplier_id,
                    api_url=supplier.api_url or "",
                    api_key=supplier.api_key or "",
                    api_secret=supplier.api_secret or "",
                )
                lifecycle = await client.get_card_lifecycle(card.iccid)
                supplier_expired_at = lifecycle.get("expired_at")
                supplier_date = (
                    datetime.strptime(supplier_expired_at, "%Y-%m-%d").date()
                    if supplier_expired_at
                    else None
                )
            except Exception as exc:
                anomalies.append(
                    Anomaly(
                        category="supplier_check_failed",
                        iccid=card.iccid,
                        detail=f"供应商生命周期查询失败: {exc}"
                    )
                )
                continue

            if not supplier_date or not card.expired_at:
                continue
            if card.expired_at < supplier_date:
                anomalies.append(
                    Anomaly(
                        category="local_shorter_than_supplier",
                        iccid=card.iccid,
                        detail=f"本地 expired_at={card.expired_at}，供应商 expired_at={supplier_date}"
                    )
                )
            elif card.expired_at > supplier_date:
                expected = latest_expectation.get(card.iccid) if latest_expectation else None
                if expected and card.expired_at >= expected[0]:
                    anomalies.append(
                        Anomaly(
                            category="pending_supplier_catchup",
                            iccid=card.iccid,
                            detail=(
                                f"本地 expired_at={card.expired_at}，供应商 expired_at={supplier_date}，"
                                f"但最近续费日志期望值={expected[0]}，暂按供应商未完全追平处理"
                            )
                        )
                    )
                    continue
                anomalies.append(
                    Anomaly(
                        category="local_longer_than_supplier",
                        iccid=card.iccid,
                        detail=f"本地 expired_at={card.expired_at}，供应商 expired_at={supplier_date}"
                    )
                )

        return anomalies


def print_report(anomalies: list[Anomaly]) -> None:
    if not anomalies:
        print("未发现续费/套餐周期异常")
        return

    grouped: dict[str, list[Anomaly]] = {}
    for item in anomalies:
        grouped.setdefault(item.category, []).append(item)

    print(f"发现异常 {len(anomalies)} 条")
    for category, items in grouped.items():
        print(f"\n[{category}] {len(items)} 条")
        for item in items:
            print(f"- {item.iccid}: {item.detail}")


async def async_main(args: argparse.Namespace) -> int:
    runtime = load_runtime_dependencies()
    try:
        renew_logs = await load_recent_renew_logs(args.days, args.limit)
        anomalies, inspected_iccids, latest_expectation = await check_recent_renew_log_consistency(renew_logs, args.iccids)
        anomalies.extend(await check_activated_missing_dates())

        supplier_scope = sorted(set(inspected_iccids) | set(args.iccids))
        if not args.skip_supplier_check:
            anomalies.extend(await check_supplier_expiry_mismatches(supplier_scope, latest_expectation))

        print_report(anomalies)
        return 2 if anomalies else 0
    finally:
        await runtime["engine"].dispose()


def main() -> int:
    args = parse_args()
    return asyncio.run(async_main(args))


if __name__ == "__main__":
    raise SystemExit(main())
