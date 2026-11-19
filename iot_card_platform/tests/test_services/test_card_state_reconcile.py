from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy import select, BigInteger
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services import card_state_reconcile_service as svc
from app.db.models.base import Base
from app.db.models.iot_card import IotCardModel, CardStatus, SuspendType
from app.db.models.supplier import SupplierModel
from app.db.models.suspend import AlertLogModel, SuspendLogModel, SupplierSuspendOperationModel

@compiles(BigInteger, 'sqlite')
def bigint(element, compiler, **kw):
    return 'INTEGER'

def card(kind=SuspendType.none):
    return SimpleNamespace(status=CardStatus.suspended, is_deleted=0, suspend_type=kind, expired_at=date.today()+timedelta(days=30))

@pytest.mark.parametrize('kind,upstream,code,expected', [
    (SuspendType.none, {'status':'activated'}, '001','repair'),
    (SuspendType.manual, {'status':'activated'}, '001','alert'),
    (SuspendType.expired, {'status':'activated'}, '001','skip'),
    (SuspendType.pool_exceed, {'status':'activated'}, '001','skip'),
    (SuspendType.card_exceed, {'status':'activated'}, '001','skip'),
    (SuspendType.none, {'status':'suspended'}, '001','skip'),
    (SuspendType.none, {'status':'unknown'}, '001','skip'),
    (SuspendType.none, {'status':'activated'}, '002','skip'),
    (SuspendType.none, {'status':'activated','network_status':'activated'}, '002','repair'),
])
def test_policy(kind, upstream, code, expected):
    assert svc.decision(card(kind),upstream,code,None)==expected

@pytest.mark.parametrize('pending,recent,submitted,expected', [
    ('pending',False,True,'skip'), ('pending',False,False,'repair'),
    ('success',True,True,'skip'), ('failed',False,True,'repair'),
])
def test_operation_guard(pending,recent,submitted,expected):
    import json
    op=SimpleNamespace(created_at=datetime.now()-timedelta(minutes=1 if recent else 60),callback_status=pending,request_result=json.dumps({'submitted':submitted}))
    assert svc.decision(card(),{'status':'activated'},'001',op)==expected

def test_expired_and_authorization():
    c=card(SuspendType.manual)
    assert svc.decision(c,{'status':'activated'},'001',None,True)=='repair'
    c.expired_at=date.today()-timedelta(days=1)
    assert svc.decision(c,{'status':'activated'},'001',None,True)=='skip'

@pytest.mark.asyncio
async def test_database_repair_alert_dedup_authorization_and_failure():
    engine=create_async_engine('sqlite+aiosqlite:///:memory:')
    factory=sessionmaker(engine,class_=AsyncSession,expire_on_commit=False)
    tables=[m.__table__ for m in [SupplierModel,IotCardModel,AlertLogModel,SuspendLogModel,SupplierSuspendOperationModel]]
    async with engine.begin() as conn:
        await conn.run_sync(lambda c:Base.metadata.create_all(c,tables=tables))
    async with factory() as db:
        db.add(SupplierModel(id=1,name='test',code='001'))
        for i,kind in [(1,SuspendType.none),(2,SuspendType.manual)]:
            db.add(IotCardModel(id=i,iccid=str(i),supplier_id=1,user_id=10,carrier='cucc',flow_size=100,data_total=100,period_type='monthly',status=CardStatus.suspended,suspend_type=kind,expired_at=date.today()+timedelta(days=30)))
        await db.commit()
    client=SimpleNamespace(get_card_lifecycle=AsyncMock(return_value={'status':'activated'}))
    with patch.object(svc,'AsyncSessionLocal',factory), patch.object(svc,'get_supplier_client',return_value=client):
        a=await svc.reconcile_supplier(1)
        assert a['repair']==1 and a['alert']==1
        await svc.reconcile_supplier(1)
        async with factory() as db:
            assert len((await db.execute(select(AlertLogModel))).scalars().all())==1
            assert len((await db.execute(select(SuspendLogModel))).scalars().all())==1
            assert (await db.get(IotCardModel,2)).status==CardStatus.suspended
        client.get_card_lifecycle.side_effect=RuntimeError('offline')
        assert (await svc.reconcile_supplier(1))['failed']==1
        client.get_card_lifecycle.side_effect=None
        assert (await svc.reconcile_supplier(1,['2']))['repair']==1
        async with factory() as db:
            assert (await db.get(IotCardModel,2)).suspend_type==SuspendType.none
            assert (await db.execute(select(AlertLogModel))).scalar_one().handled==1
        assert (await svc.reconcile_supplier(1,['2']))['repair']==0
    await engine.dispose()

@pytest.mark.asyncio
async def test_superseded_stop_does_not_override_new_resume():
    from unittest.mock import MagicMock
    from app.services import suspend_service as mod
    op=SimpleNamespace(id=1,card_id=1,supplier_id=1,action=svc.SuspendActionType.suspend,callback_status='pending',request_result='{}')
    target=SimpleNamespace(id=1,iccid='one',supplier_id=1,status=CardStatus.activated)
    supplier=SimpleNamespace(code='001',api_url='',api_key='',api_secret='',api_config=None)
    def result(value):
        r=MagicMock();r.scalar_one_or_none.return_value=value;return r
    db=MagicMock(get=AsyncMock(return_value=target),execute=AsyncMock(side_effect=[result(supplier),result(2)]),refresh=AsyncMock(),rollback=AsyncMock())
    context=MagicMock();context.__aenter__=AsyncMock(return_value=db);context.__aexit__=AsyncMock()
    with patch.object(mod,'AsyncSessionLocal',return_value=context), patch.object(mod,'get_supplier_client',return_value=SimpleNamespace(get_card_lifecycle=AsyncMock(return_value={'status':'suspended'}))), patch.object(mod.SupplierSuspendOperationCRUD,'get_by_callback_no',AsyncMock(return_value=op)), patch.object(mod.SupplierSuspendOperationCRUD,'update_request_result',AsyncMock()), patch.object(mod.SupplierSuspendOperationCRUD,'update_callback_result',AsyncMock()) as update, patch.object(mod.SuspendActionService,'_safe_update_supplier_action_audit',AsyncMock()), patch.object(mod.SuspendActionService,'normalize_card_suspend_state') as normalize:
        await mod.SuspendActionService._run_pending_operation_reconcile('old',0)
    normalize.assert_not_called()
    assert update.await_args.args[3]=='SUPERSEDED'
    assert target.status==CardStatus.activated


@pytest.mark.parametrize("minutes_after_stop, expected", [(1, "repair"), (-1, "alert")])
def test_failed_resume_after_manual_stop(minutes_after_stop, expected):
    target = card(SuspendType.manual)
    target.supplier_id = 1
    target.suspend_at = datetime.now() - timedelta(hours=1)
    operation = SimpleNamespace(
        action=svc.SuspendActionType.resume, callback_status="failed", supplier_id=1,
        created_at=target.suspend_at + timedelta(minutes=minutes_after_stop), request_result=None,
    )
    assert svc.decision(target, {"status": "activated"}, "001", operation) == expected

@pytest.mark.asyncio
async def test_manual_refresh_reconciles_recent_failed_resume():
    from app.services.sync_service import sync_service
    from app.db.models.suspend import SuspendActionType

    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    tables = [m.__table__ for m in (IotCardModel, SupplierSuspendOperationModel, SuspendLogModel)]
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=tables))
    async with AsyncSession(engine, expire_on_commit=False) as db:
        stopped = datetime.now() - timedelta(minutes=3)
        target = IotCardModel(id=1, iccid='test', supplier_id=1, user_id=10, carrier='cucc',
                              flow_size=100, data_total=100, period_type='monthly', status=CardStatus.suspended,
                              suspend_type=SuspendType.manual, suspend_at=stopped)
        op = SupplierSuspendOperationModel(card_id=1, supplier_id=1, iccid='test', action=SuspendActionType.resume,
                                          callback_no='resume', callback_status='pending',
                                          created_at=stopped + timedelta(minutes=1))
        db.add_all([target, op])
        await db.commit()
        client = SimpleNamespace(get_card_lifecycle=AsyncMock(return_value={'status': 'activated'}))
        supplier = SimpleNamespace(code='001')
        await sync_service.refresh_card_lifecycle(db, target, supplier, client)
        assert target.status == CardStatus.suspended
        op.callback_status = 'failed'
        await db.commit()
        await sync_service.refresh_card_lifecycle(db, target, supplier, client)
        await db.commit()
        assert target.status == CardStatus.activated and target.suspend_type == SuspendType.none
        assert (await db.execute(select(SuspendLogModel))).scalar_one().api_called == 0
    await engine.dispose()

@pytest.mark.asyncio
async def test_admin_stop_blocks_customers_reapplies_and_requires_matching_unlock():
    from app.services.suspend_service import SuspendActionService as actions

    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    tables = [m.__table__ for m in (SupplierModel, IotCardModel, SupplierSuspendOperationModel, SuspendLogModel)]
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=tables))
    async with AsyncSession(engine, expire_on_commit=False) as db:
        supplier = SupplierModel(id=1, code="001", name="test")
        target = IotCardModel(id=1, iccid='locked', supplier_id=1, user_id=10, carrier='cucc',
                              flow_size=100, data_total=100, period_type='monthly', status=CardStatus.activated)
        db.add_all([target, supplier])
        await db.commit()
        with patch.object(actions, '_call_supplier_suspend', AsyncMock(return_value=(True, 'stop', 'suspended'))) as stop:
            await actions.set_admin_stop(db, target.iccid, 1)
            token = target.admin_stop_token
            assert token and target.status == CardStatus.suspended
            assert await actions._call_supplier_resume(db, target, supplier, 12) == (False, None, None)
            assert svc.decision(target, {"status": "activated"}, "001", None, True) == "skip"
            await actions.enforce_admin_stop(db, target, supplier, {"status": "activated"}, None)
            assert stop.await_count == 2
            pending = SimpleNamespace(action=svc.SuspendActionType.suspend, created_at=datetime.now(),
                                      callback_status='pending')
            await actions.enforce_admin_stop(db, target, supplier, {"status": "activated"}, pending)
            assert stop.await_count == 2
            await actions.confirm_admin_resume(db, target, "previous-lock", "activated")
            assert target.admin_stop_token == token
            rejected = SupplierSuspendOperationModel(
                card_id=target.id, supplier_id=1, iccid=target.iccid, action=svc.SuspendActionType.resume,
                callback_no='rejected', callback_status='pending', request_result='{"submitted": false}',
                request_payload='{"admin_unlock_token": "%s"}' % token, created_at=datetime.now(),
            )
            db.add(rejected)
            await db.commit()
            with patch.object(actions, '_call_supplier_resume', AsyncMock(return_value=(True, 'resume', 'activated'))) as resume:
                await actions.set_admin_stop(db, target.iccid, 1, release=True)
                assert resume.await_args.kwargs['unlock_token'] == token
            assert target.admin_stop_token is None and target.status == CardStatus.activated
            target.admin_stop_token = 'second-lock'
            target.status = CardStatus.suspended
            accepted = SupplierSuspendOperationModel(
                card_id=target.id, supplier_id=1, iccid=target.iccid, action=svc.SuspendActionType.resume,
                callback_no='accepted', callback_status='pending', request_result='{"submitted": true}',
                request_payload='{"admin_unlock_token": "second-lock"}',
                created_at=datetime.now() - timedelta(minutes=12),
            )
            db.add(accepted)
            await db.commit()
            await actions.enforce_admin_stop(db, target, supplier, {"status": "activated"}, accepted)
            assert target.admin_stop_token is None and accepted.callback_status == "success"
            assert stop.await_count == 2
    await engine.dispose()
