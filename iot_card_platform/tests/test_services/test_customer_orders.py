from datetime import date
from types import SimpleNamespace

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.api.v1.customer_orders import orders, cards, numbers, update_remark, OrderRemarkUpdate
from app.crud.stock_crud import insert_out_record
from app.utils.exceptions import BusinessException


@pytest.mark.asyncio
async def test_order_snapshot_and_customer_scope():
    engine = create_async_engine("sqlite+aiosqlite://")
    customer = SimpleNamespace(id=10, user_level=3)
    async with AsyncSession(engine) as db:
        for ddl in (
            "CREATE TABLE stock_out_records (id INTEGER PRIMARY KEY, user_id, to_user_id, record_no, "
            "sale_package_id, stock_out_date DATE, card_count, success_count, failed_count, "
            "unit_price, total_amount, remark, customer_remark, operator_id, created_at, updated_at, is_deleted DEFAULT 0)",
            "CREATE TABLE stock_out_record_cards (id INTEGER PRIMARY KEY, record_id, card_id, "
            "iccid TEXT, sale_package_name, is_deleted DEFAULT 0)",
            "CREATE TABLE iot_cards (id INTEGER PRIMARY KEY, user_id, is_deleted DEFAULT 0)",
        ):
            await db.execute(text(ddl))
        day = date(2026, 1, 8)
        for number, uid, count in [('OUT1', 10, 2), ('OUT2', 10, 1), ('OUT3', 20, 1), ('OUT4', 10, 0)]:
            await insert_out_record(db, number, uid, 1, day, 3, count, 100, None, 1)
        await db.execute(text("INSERT INTO iot_cards (id,user_id) VALUES (1,10),(2,20)"))
        await db.execute(text("INSERT INTO stock_out_record_cards (record_id,card_id,iccid) "
                              "VALUES (1,1,'0001234567890123456789'),(1,2,'0002')"))
        result = await orders(day, day, '', 1, customer, db)
        assert result.data['total'] == 2
        assert [r['record_no'] for r in result.data['items']] == ['OUT2', 'OUT1']
        assert (await orders(date(2026, 1, 9), None, '', 1, customer, db)).data['total'] == 0
        rows = (await cards(1, '', 1, customer, db)).data['items']
        assert [r['card_id'] for r in rows] == [1, None]
        assert (await numbers(1, customer, db)).data == ['0001234567890123456789', '0002']
        with pytest.raises(BusinessException):
            await numbers(3, customer, db)
        await db.execute(text("UPDATE stock_out_records SET stock_out_date=NULL, "
                              "created_at='2026-01-09 23:59:59', remark='内部备注' WHERE id=1"))
        historical = await orders(date(2026, 1, 9), date(2026, 1, 9), '', 1, customer, db)
        assert historical.data['total'] == 1
        assert str(historical.data['items'][0]['stock_out_date']) == '2026-01-09'
        assert (await orders(day, day, '', 1, customer, db)).data['total'] == 1
        await update_remark(1, OrderRemarkUpdate(remark='  客户采购批次  '), customer, db)
        assert await db.scalar(text("SELECT customer_remark FROM stock_out_records WHERE id=1")) == '客户采购批次'
        assert await db.scalar(text("SELECT remark FROM stock_out_records WHERE id=1")) == '内部备注'
        with pytest.raises(BusinessException):
            await update_remark(3, OrderRemarkUpdate(remark='越权'), customer, db)
        await update_remark(1, OrderRemarkUpdate(remark=''), customer, db)
        assert await db.scalar(text("SELECT customer_remark FROM stock_out_records WHERE id=1")) is None
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            OrderRemarkUpdate(remark='字' * 501)

    await engine.dispose()


@pytest.mark.asyncio
async def test_excel_import_orders_only_successful_rows_and_survives_retry():
    from sqlalchemy.schema import CreateTable
    from sqlalchemy.dialects import sqlite
    from app.db.models.iot_card import IotCardModel
    from app.db.models.package import SalePackageModel
    from app.db.models.stock import StockOutRecordCardModel
    from app.schemas.stock import ExcelStockOutItem
    from app.services.stock_service import stock_service

    engine = create_async_engine("sqlite+aiosqlite://")
    async with AsyncSession(engine, autoflush=False, expire_on_commit=False) as db:
        for model in (IotCardModel, SalePackageModel, StockOutRecordCardModel):
            ddl = str(CreateTable(model.__table__).compile(dialect=sqlite.dialect()))
            await db.execute(text(ddl.replace('BIGINT', 'INTEGER')))
        await db.execute(text("CREATE TABLE stock_out_records (id INTEGER PRIMARY KEY, user_id, "
                              "to_user_id, record_no, sale_package_id, stock_out_date, card_count, "
                              "success_count, failed_count, unit_price, total_amount, remark, "
                              "operator_id, created_at, updated_at)"))
        spec = dict(carrier='cmcc', period_type='monthly', flow_size=100)
        db.add(SalePackageModel(id=5, name='月包', code='M', price_cost=1, price_sale=2, **spec))
        rows = []
        for i, uid in enumerate([10, 10, 20], start=1):
            db.add(IotCardModel(id=i, iccid=str(i), data_total=100, **spec))
            rows.append(ExcelStockOutItem(iccid=str(i), user_id=uid, sale_package_id=5,
                                          period_count=1, stock_out_date=date(2026, 2, 1),
                                          silent_expire_date=date(2026, 3, 1)))
        await db.commit()
        result = await stock_service.batch_stock_out_import(db, [*rows, rows[0]], 1)
        assert (result['success'], result['failed']) == (3, 1)
        assert (await stock_service.batch_stock_out_import(db, rows, 1))['success'] == 0
        saved = await db.execute(text("SELECT to_user_id, stock_out_date, success_count "
                                      "FROM stock_out_records ORDER BY id"))
        assert saved.all() == [(10, '2026-02-01', 2), (20, '2026-02-01', 1)]
        assert await db.scalar(text("SELECT COUNT(*) FROM stock_out_record_cards")) == 3
    await engine.dispose()
