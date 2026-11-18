"""客户账号按手填出库日期查询本人的交付清单。"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.auth import CurrentUser
from app.schemas.common import ResponseModel
from app.services.iot_card_service import iot_card_service
from app.utils.auth import get_current_user
from app.utils.exceptions import BusinessException

router = APIRouter(prefix="/orders")
ORDER_DATE = "COALESCE(o.stock_out_date, DATE(o.created_at))"
ORDER_SCOPE = "o.to_user_id = :uid AND o.is_deleted = 0 AND o.success_count > 0"


@router.get("")
async def orders(start: Optional[date] = None, end: Optional[date] = None,
                 number: str = "", page: int = Query(1, ge=1),
                 user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    where = ORDER_SCOPE
    params = {"uid": user.id, "offset": (page - 1) * 20}
    for value, clause, key in [(start, f"{ORDER_DATE} >= :start", "start"),
                               (end, f"{ORDER_DATE} <= :end", "end"),
                               (number.strip(), "o.record_no = :number", "number")]:
        if value:
            where += f" AND {clause}"
            params[key] = value
    total = await db.scalar(text(f"SELECT COUNT(*) FROM stock_out_records o WHERE {where}"), params)
    rows = await db.execute(text(f"""
        SELECT o.id, o.record_no, {ORDER_DATE} AS stock_out_date, o.success_count, o.customer_remark,
               (SELECT rc.sale_package_name FROM stock_out_record_cards rc
                WHERE rc.record_id=o.id AND rc.is_deleted=0 ORDER BY rc.id LIMIT 1) AS package_name
        FROM stock_out_records o WHERE {where}
        ORDER BY {ORDER_DATE} DESC, o.id DESC LIMIT 20 OFFSET :offset
    """), params)
    return ResponseModel(data={"total": total, "items": [dict(row) for row in rows.mappings()]})


async def require_order(db, order_id, uid):
    exists = await db.scalar(text(f"SELECT o.id FROM stock_out_records o WHERE o.id=:id AND {ORDER_SCOPE}"),
                             {"id": order_id, "uid": uid})
    if not exists:
        raise BusinessException(code=404, msg="订单不存在")


@router.get("/{order_id}/cards")
async def cards(order_id: int, keyword: str = "", page: int = Query(1, ge=1),
                user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_order(db, order_id, user.id)
    where = "rc.record_id=:id AND rc.is_deleted=0"
    params = {"id": order_id, "offset": (page - 1) * 20}
    if keyword.strip():
        where += " AND rc.iccid LIKE :keyword"
        params["keyword"] = "%" + keyword.strip() + "%"
    total = await db.scalar(text(f"SELECT COUNT(*) FROM stock_out_record_cards rc WHERE {where}"), params)
    rows = await db.execute(text(f"""
        SELECT rc.iccid, c.id, c.user_id FROM stock_out_record_cards rc
        LEFT JOIN iot_cards c ON c.id=rc.card_id AND c.is_deleted=0
        WHERE {where} ORDER BY rc.id LIMIT 20 OFFSET :offset
    """), params)
    scope = await iot_card_service._get_accessible_user_ids(db, user.id, user.user_level)
    items = [{"iccid": r.iccid, "card_id": r.id if scope is None or r.user_id in scope else None} for r in rows]
    return ResponseModel(data={"total": total, "items": items})


@router.get("/{order_id}/numbers")
async def numbers(order_id: int, user: CurrentUser = Depends(get_current_user),
                  db: AsyncSession = Depends(get_db)):
    await require_order(db, order_id, user.id)
    result = await db.scalars(text("""
        SELECT iccid FROM stock_out_record_cards
        WHERE record_id=:id AND is_deleted=0 ORDER BY id
    """), {"id": order_id})
    return ResponseModel(data=result.all())


class OrderRemarkUpdate(BaseModel):
    remark: str = Field(max_length=500)


@router.put("/{order_id}/remark")
async def update_remark(order_id: int, payload: OrderRemarkUpdate,
                        user: CurrentUser = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    await require_order(db, order_id, user.id)
    remark = payload.remark.strip()
    await db.execute(text("""
        UPDATE stock_out_records SET customer_remark=:remark
        WHERE id=:id AND to_user_id=:uid AND is_deleted=0 AND success_count>0
    """), {"remark": remark or None, "id": order_id, "uid": user.id})
    await db.commit()
    return ResponseModel(data={"customer_remark": remark or None}, msg="备注已保存")
