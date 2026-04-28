#!/usr/bin/env python3
"""
按供应商生命周期纠正本地卡片到期日。

默认只修复“供应商到期日晚于本地到期日”的安全场景。
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按供应商生命周期纠正本地卡片到期日")
    parser.add_argument("--iccid", action="append", dest="iccids", required=True, help="待修复 ICCID，可重复传入")
    parser.add_argument("--operator-id", type=int, default=1, help="写入操作日志时使用的操作者 ID，默认 1")
    parser.add_argument("--dry-run", action="store_true", help="只输出将要修复的内容，不落库")
    return parser.parse_args()


def load_runtime_dependencies():
    from sqlalchemy import select
    from app.clients.supplier_api import get_supplier_client
    from app.crud.system_crud import SysOperationLogCRUD
    from app.crud.supplier_crud import supplier_crud
    from app.db.database import AsyncSessionLocal, engine
    from app.db.models.iot_card import CardStatus, IotCardModel

    return {
        "select": select,
        "get_supplier_client": get_supplier_client,
        "SysOperationLogCRUD": SysOperationLogCRUD,
        "supplier_crud": supplier_crud,
        "AsyncSessionLocal": AsyncSessionLocal,
        "engine": engine,
        "CardStatus": CardStatus,
        "IotCardModel": IotCardModel,
    }


async def reconcile_card(db, card: IotCardModel, operator_id: int, dry_run: bool) -> tuple[str, str]:
    runtime = load_runtime_dependencies()
    supplier_crud = runtime["supplier_crud"]
    get_supplier_client = runtime["get_supplier_client"]
    CardStatus = runtime["CardStatus"]
    SysOperationLogCRUD = runtime["SysOperationLogCRUD"]

    supplier = await supplier_crud.get_by_id(db, card.supplier_id) if card.supplier_id else None
    if not supplier:
        return "skip", f"{card.iccid}: 缺少供应商配置"

    client = get_supplier_client(
        supplier_id=card.supplier_id,
        api_url=supplier.api_url or "",
        api_key=supplier.api_key or "",
        api_secret=supplier.api_secret or "",
    )
    lifecycle = await client.get_card_lifecycle(card.iccid)
    supplier_expired_at = lifecycle.get("expired_at")
    if not supplier_expired_at:
        return "skip", f"{card.iccid}: 供应商未返回 expired_at"

    supplier_expiry = datetime.strptime(supplier_expired_at, "%Y-%m-%d").date()
    local_expiry = card.expired_at
    if local_expiry and supplier_expiry <= local_expiry:
        return "skip", f"{card.iccid}: 本地 {local_expiry} 不短于供应商 {supplier_expiry}"

    activated_at = lifecycle.get("activated_at")
    test_expire_date = lifecycle.get("test_expire_date")
    silent_expire_date = lifecycle.get("silent_expire_date")
    status = lifecycle.get("status")

    if dry_run:
        return "fix", f"{card.iccid}: 本地 {local_expiry or '-'} -> 供应商 {supplier_expiry}"

    if activated_at:
        card.activated_at = datetime.strptime(activated_at, "%Y-%m-%d").date()
    if test_expire_date:
        card.test_expire_date = datetime.strptime(test_expire_date, "%Y-%m-%d").date()
    if silent_expire_date:
        card.silent_expire_date = datetime.strptime(silent_expire_date, "%Y-%m-%d").date()
    if status:
        card.status = CardStatus(status)
    card.expired_at = supplier_expiry
    await db.commit()

    await SysOperationLogCRUD.create(
        db=db,
        module="cards",
        action="reconcile_expiry",
        user_id=operator_id,
        target_type="card",
        target_id=card.id,
        target_name=card.iccid,
        detail=f"按供应商生命周期纠正到期日，本地 {local_expiry or '-'}，供应商 {supplier_expiry}"
    )
    return "fix", f"{card.iccid}: 本地 {local_expiry or '-'} -> 供应商 {supplier_expiry}"


async def async_main(args: argparse.Namespace) -> int:
    runtime = load_runtime_dependencies()
    AsyncSessionLocal = runtime["AsyncSessionLocal"]
    engine = runtime["engine"]
    select = runtime["select"]
    IotCardModel = runtime["IotCardModel"]
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(IotCardModel).where(
                    IotCardModel.iccid.in_(args.iccids),
                    IotCardModel.is_deleted == 0,
                )
            )
            cards = list(result.scalars().all())
            card_map = {card.iccid: card for card in cards}

            missing = [iccid for iccid in args.iccids if iccid not in card_map]
            for iccid in missing:
                print(f"skip {iccid}: 本地卡表不存在")

            fixed = 0
            skipped = len(missing)
            for iccid in args.iccids:
                card = card_map.get(iccid)
                if not card:
                    continue
                outcome, detail = await reconcile_card(db, card, args.operator_id, args.dry_run)
                print(f"{outcome} {detail}")
                if outcome == "fix":
                    fixed += 1
                else:
                    skipped += 1

            print(f"summary fixed={fixed} skipped={skipped} dry_run={args.dry_run}")
            return 0
    finally:
        await engine.dispose()


def main() -> int:
    args = parse_args()
    return asyncio.run(async_main(args))


if __name__ == "__main__":
    raise SystemExit(main())
