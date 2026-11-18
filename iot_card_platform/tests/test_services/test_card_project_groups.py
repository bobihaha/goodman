"""项目分组的真实 SQL 回归；仅使用内存 SQLite，不访问业务数据库。"""
import json
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.crud.iot_card_crud import iot_card_crud
from app.crud.project_crud import project_crud
from app.db.models.iot_card import IotCardModel
from app.db.models.project import ProjectModel
from app.db.models.sys_log import SysOperationLogModel
from app.schemas.project import ProjectMoveRequest, ProjectCreate
from app.services.iot_card_service import IotCardService
from app.services.project_service import project_service
from app.utils.exceptions import BusinessException


def iccid(index):
    return f'8986000000000000{index:04d}'


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        for model in [ProjectModel, IotCardModel, SysOperationLogModel]:
            await conn.run_sync(model.__table__.create)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        session.add_all([
            ProjectModel(id=1, name='项目 A', user_id=10),
            ProjectModel(id=2, name='项目 B', user_id=10),
            ProjectModel(id=3, name='其他账号项目', user_id=20),
        ])
        for index, owner, project in [(1,10,None),(2,10,1),(3,10,2),(4,20,None),(5,20,3),(6,10,1)]:
            session.add(IotCardModel(id=index, iccid=iccid(index), user_id=owner,
                                    project_id=project, carrier='cmcc', flow_size=1024,
                                    period_type='monthly', data_total=1024, status='activated',
                                    is_deleted=1 if index == 6 else 0))
        await session.commit()
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_move_partial_success_deduplicates_and_audits(db):
    result = await project_service.move_cards(db, 10, ProjectMoveRequest(
        iccids=[iccid(1), iccid(1), iccid(2), iccid(4), iccid(6), 'bad'], project_id=1,
    ), original_user_id=99)
    assert (result['success_count'], result['skipped_count'], result['failed_count'], result['duplicate_count']) == (1,1,3,1)
    assert (await db.get(IotCardModel, 1)).project_id == 1
    assert (await db.get(IotCardModel, 4)).project_id is None
    logs = (await db.execute(select(SysOperationLogModel))).scalars().all()
    assert len(logs) == 1
    assert logs[0].original_user_id == 99
    assert json.loads(logs[0].detail) == {'old_project_id': None, 'new_project_id': 1}
    retry = await project_service.move_cards(db, 10, ProjectMoveRequest(iccids=[iccid(1)], project_id=1))
    assert retry['skipped_count'] == 1


@pytest.mark.asyncio
async def test_cross_project_move_remove_and_source_guard(db):
    moved = await project_service.move_cards(db, 10, ProjectMoveRequest(
        iccids=[iccid(2)], project_id=2, source_project_id=1,
    ))
    assert moved['success_count'] == 1
    stale = await project_service.move_cards(db, 10, ProjectMoveRequest(
        iccids=[iccid(2), iccid(3)], project_id=None, source_project_id=1,
    ))
    assert stale['failed_count'] == 2
    removed = await project_service.move_cards(db, 10, ProjectMoveRequest(
        iccids=[iccid(2)], project_id=None, source_project_id=2,
    ))
    assert removed['success_count'] == 1
    assert (await db.get(IotCardModel, 2)).project_id is None
    already_grouped = await project_service.move_cards(db, 10, ProjectMoveRequest(
        iccids=[iccid(3)], project_id=1, source_ungrouped=True,
    ))
    assert already_grouped['failed_count'] == 1


@pytest.mark.asyncio
async def test_foreign_or_deleted_project_cannot_be_target(db):
    for project_id in [3, 404]:
        with pytest.raises(BusinessException):
            await project_service.move_cards(db, 10, ProjectMoveRequest(iccids=[iccid(1)], project_id=project_id))
    await project_service.delete(db, 10, 1)
    assert (await db.get(IotCardModel, 2)).project_id is None
    with pytest.raises(BusinessException):
        await project_service.move_cards(db, 10, ProjectMoveRequest(iccids=[iccid(1)], project_id=1))


@pytest.mark.asyncio
async def test_reorder_persists_and_rejects_foreign_duplicate_or_stale_set(db):
    await project_service.reorder(db, 10, [2,1])
    assert [p.id for p in await project_crud.get_all_by_user(db, 10)] == [2,1]
    for ids in [[1,3], [1,1], [1]]:
        with pytest.raises(BusinessException):
            await project_service.reorder(db, 10, ids)
    assert [p.id for p in await project_crud.get_all_by_user(db, 10)] == [2,1]


@pytest.mark.asyncio
@pytest.mark.parametrize('scope,expected', [({},[1,2,3,4,5]), ({'project_id':1},[2]), ({'ungrouped':True},[1])])
async def test_list_stats_batch_and_exports_share_scope(db, monkeypatch, scope, expected):
    service = IotCardService()
    service._hydrate_card_dicts = AsyncMock()  # 本测试仅验证范围，不涉及供应商和账户展示。
    rows, total = await service.get_cards(db, current_user_id=10, user_level=1, **scope)
    assert sorted(row['id'] for row in rows) == expected
    assert total == len(expected)
    stats = await service.get_stats(db, current_user_id=10, user_level=1, **scope)
    assert stats['total'] == len(expected)
    batch = await service.batch_query_cards(db, [iccid(i) for i in range(1,7)], 10, 1, **scope)
    assert sorted(row['id'] for row in batch['found']) == expected
    for ids in [None, list(range(1,7))]:
        export = await service.export_cards(db, 10, 1, card_ids=ids, **scope)
        assert sorted(row['ICCID'] for row in export) == [iccid(i) for i in expected]
        monkeypatch.setattr('app.crud.iot_card_crud.card_usage_history_crud.get_cards_monthly_history', AsyncMock(return_value=[]))
        history = await service.export_cards_with_history(db, 10, 1, card_ids=ids, start_date='2026-10-01', end_date='2026-10-30', **scope)
        assert sorted(row['ICCID'] for row in history) == [iccid(i) for i in expected]


@pytest.mark.asyncio
async def test_project_filter_never_bypasses_owner_or_customer_filter(db):
    service = IotCardService()
    service._hydrate_card_dicts = AsyncMock()
    service._get_customer_filter_user_ids = AsyncMock(return_value=[20])
    rows, total = await service.get_cards(db, 10, 1, project_id=1, customer_id=20)
    assert rows == [] and total == 0
    for kwargs in [{'project_id':3}, {'project_id':1,'ungrouped':True}]:
        with pytest.raises(BusinessException):
            await service.get_cards(db, 10, 1, **kwargs)


@pytest.mark.asyncio
async def test_commit_failure_rolls_back_move_and_audit(db, monkeypatch):
    monkeypatch.setattr(db, 'commit', AsyncMock(side_effect=RuntimeError('写入失败')))
    with pytest.raises(RuntimeError):
        await project_service.move_cards(db, 10, ProjectMoveRequest(iccids=[iccid(1)], project_id=1))
    await db.rollback()
    assert (await db.get(IotCardModel, 1)).project_id is None
    assert (await db.execute(select(SysOperationLogModel))).scalars().all() == []


def test_project_name_cannot_be_blank():
    with pytest.raises(ValueError):
        ProjectCreate(name='  ')
    assert ProjectCreate(name='  项目 A  ').name == '项目 A'


@pytest.mark.asyncio
async def test_ownership_change_clears_project_even_with_stale_loaded_card(db):
    # 模拟划拨先读取卡片，随后另一请求移入项目，再提交持卡人变更。
    card = await db.get(IotCardModel, 1)
    assert card.project_id is None
    async with AsyncSession(db.bind, expire_on_commit=False) as other:
        await project_service.move_cards(other, 10, ProjectMoveRequest(iccids=[iccid(1)], project_id=1))
    card.user_id = 20
    await db.commit()
    await db.refresh(card)
    assert card.user_id == 20 and card.project_id is None
    card = await db.get(IotCardModel, 2)
    card.remark = '普通更新应保留分组'
    await db.commit()
    assert card.project_id == 1
    card.user_id = None
    await db.commit()
    assert card.project_id is None


@pytest.mark.asyncio
async def test_project_api_contract_and_card_scope_query_params(db, monkeypatch):
    from fastapi import FastAPI
    from httpx import AsyncClient, ASGITransport
    from app.api.v1.project import router as projects_router
    from app.api.v1.iot_card import router as cards_router
    from app.db.database import get_db
    from app.schemas.auth import CurrentUser
    from app.services.iot_card_service import iot_card_service
    from app.utils.auth import get_current_user
    from app.utils.exceptions import business_exception_handler

    app = FastAPI()
    app.include_router(projects_router, prefix='/projects')
    app.include_router(cards_router)
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=10, user_level=1, name='测试', account='test', status='enable', original_user_id=99,
    )
    monkeypatch.setattr(iot_card_service, '_hydrate_card_dicts', AsyncMock())
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.put('/projects/order', json={'project_ids':[2,1]})
        assert response.json()['code'] == 200
        projects = (await client.get('/projects/all')).json()['data']
        assert [p['id'] for p in projects] == [2,1]
        assert projects[1]['card_count'] == 1
        response = await client.post('/projects/move-cards', json={'iccids':[iccid(1),iccid(4)],'project_id':1})
        assert response.json()['data']['success_count'] == 1
        assert response.json()['data']['failed_count'] == 1
        response = await client.post('/cards/batch-query?project_id=1', json=[iccid(1),iccid(3)])
        assert [c['id'] for c in response.json()['data']['found']] == [1]
        assert (await client.get('/cards/stats?project_id=1')).json()['data']['total'] == 2
        assert (await client.get('/cards?ungrouped=true')).json()['data']['total'] == 0
        assert (await client.get('/cards?project_id=3')).json()['code'] == 404
        assert (await client.post('/projects/move-cards', json={'iccids':[iccid(1)],'project_id':0})).status_code == 422


def test_batch_input_limit_and_preserves_iccid_string():
    value = '00060000000000000001'
    assert ProjectMoveRequest(iccids=[value] * 10000, project_id=None).iccids[0] == value
    with pytest.raises(ValueError):
        ProjectMoveRequest(iccids=[value] * 10001, project_id=None)
    with pytest.raises(ValueError):
        ProjectMoveRequest(iccids=[89860000000000000001], project_id=None)


@pytest.mark.asyncio
async def test_project_audit_is_visible_in_card_module_and_scoped_to_actor(db):
    from app.services.system_service import OperationLogService
    await project_service.move_cards(db, 10, ProjectMoveRequest(iccids=[iccid(1)], project_id=1))
    await project_service.move_cards(db, 20, ProjectMoveRequest(iccids=[iccid(4)], project_id=3))
    await project_service.delete(db, 10, 1)
    logs, total = await OperationLogService.get_logs(db, 10, 3, module='card')
    assert total == 4
    assert {log['action'] for log in logs} == {'move_project', 'delete_project'}
    assert all(log['user_id'] == 10 for log in logs)
