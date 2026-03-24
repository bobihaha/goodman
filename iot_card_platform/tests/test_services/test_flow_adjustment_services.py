"""
一期补量与复机规则单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.db.models.iot_card import CardStatus, SuspendType
from app.db.models.sys_user import UserLevel
from app.schemas.suspend import ManualResume
from app.services.iot_card_service import IotCardService
from app.services.pool_service import PoolService
from app.services.suspend_service import SuspendActionService


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    return db


class TestSuspendActionService:
    @pytest.mark.asyncio
    async def test_manual_resume_rejects_manual_suspend_without_force(self, mock_db):
        card = MagicMock()
        card.id = 1
        card.iccid = "8986000000000000001"
        card.status = CardStatus.suspended
        card.suspend_type = SuspendType.manual
        card.supplier_id = 10

        supplier_result = MagicMock()
        supplier_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=supplier_result)

        with patch("app.services.suspend_service.CardSuspendCRUD.get_cards_by_ids", AsyncMock(return_value=[card])), \
             patch("app.services.suspend_service.get_supplier_client") as mock_client_factory:
            result = await SuspendActionService.manual_resume(
                db=mock_db,
                data=ManualResume(card_ids=[1]),
                operator_id=100,
                user_id=100
            )

        assert result.success_count == 0
        assert result.fail_count == 1
        assert result.fail_cards[0]["reason"] == "人工停卡需管理员强制复机"
        mock_client_factory.assert_not_called()

    @pytest.mark.asyncio
    async def test_manual_resume_allows_card_exceed_after_topup(self, mock_db):
        card = MagicMock()
        card.id = 2
        card.iccid = "8986000000000000002"
        card.status = CardStatus.suspended
        card.suspend_type = SuspendType.card_exceed
        card.supplier_id = 20
        card.data_used = 900
        card.data_total = 1200

        supplier = MagicMock()
        supplier.id = 20
        supplier.api_url = "https://example.com"
        supplier.api_key = "key"
        supplier.api_secret = "secret"

        supplier_result = MagicMock()
        supplier_result.scalars.return_value.all.return_value = [supplier]
        mock_db.execute = AsyncMock(return_value=supplier_result)

        mock_client = AsyncMock()
        mock_client.resume_card = AsyncMock(return_value=True)

        with patch("app.services.suspend_service.CardSuspendCRUD.get_cards_by_ids", AsyncMock(return_value=[card])), \
             patch("app.services.suspend_service.CardSuspendCRUD.resume_card", AsyncMock()) as mock_resume_card, \
             patch("app.services.suspend_service.SuspendLogCRUD.create", AsyncMock()) as mock_log_create, \
             patch("app.services.suspend_service.get_supplier_client", return_value=mock_client):
            result = await SuspendActionService.manual_resume(
                db=mock_db,
                data=ManualResume(card_ids=[2]),
                operator_id=100,
                user_id=100
            )

        assert result.success_count == 1
        assert result.fail_count == 0
        assert result.success_cards == ["8986000000000000002"]
        mock_client.resume_card.assert_awaited_once_with("8986000000000000002")
        mock_resume_card.assert_awaited_once()
        mock_log_create.assert_awaited()


class TestIotCardService:
    @pytest.mark.asyncio
    async def test_batch_add_flow_by_iccids_adjusts_single_cards_and_skips_pool_cards(self, mock_db):
        service = IotCardService()

        single_card = MagicMock()
        single_card.id = 11
        single_card.iccid = "8986000000000000011"
        single_card.msisdn = "13800000001"
        single_card.user_id = 2001
        single_card.is_pool_member = 0
        single_card.data_total = 1024

        pool_card = MagicMock()
        pool_card.id = 12
        pool_card.iccid = "8986000000000000012"
        pool_card.msisdn = "13800000002"
        pool_card.user_id = 2001
        pool_card.is_pool_member = 1
        pool_card.data_total = 2048

        with patch.object(service, "_get_cards_by_iccids_in_scope", AsyncMock(return_value=[single_card, pool_card])), \
             patch.object(service, "_get_direct_child_user_ids", AsyncMock(return_value=[2001])), \
             patch("app.services.iot_card_service.SuspendActionService.auto_resume_cards_after_flow_adjustment", AsyncMock(return_value={"resumed_count": 1})) as mock_auto_resume, \
             patch("app.services.iot_card_service.SysOperationLogCRUD.create", AsyncMock()) as mock_log_create:
            result = await service.batch_add_flow_by_iccids(
                db=mock_db,
                iccids=[single_card.iccid, pool_card.iccid],
                added_flow_mb=512,
                current_user_id=1001,
                user_level=UserLevel.AGENT.value,
                remark="后台补量"
            )

        assert single_card.data_total == 1536
        assert pool_card.data_total == 2048
        assert result["success"] == 1
        assert result["failed"] == 1
        assert result["auto_resumed"] == 1
        assert result["failed_list"][0]["error"] == "流量池卡请在流量池维度补量"
        mock_db.commit.assert_awaited_once()
        mock_auto_resume.assert_awaited_once()
        mock_log_create.assert_awaited_once()
        _, log_kwargs = mock_log_create.await_args
        assert log_kwargs["target_id"] == 11
        assert log_kwargs["target_name"] == "8986000000000000011"


class TestPoolService:
    @pytest.mark.asyncio
    async def test_recharge_pool_updates_addon_flow_and_triggers_auto_resume(self, mock_db):
        service = PoolService()

        pool = MagicMock()
        pool.id = 88
        pool.user_id = 3001
        pool.name = "测试流量池"
        pool.addon_flow = 1024
        pool.to_dict.return_value = {"id": 88, "name": "测试流量池", "addon_flow": 1536}

        suspended_card_1 = MagicMock()
        suspended_card_2 = MagicMock()

        suspended_cards_result = MagicMock()
        suspended_cards_result.scalars.return_value.all.return_value = [suspended_card_1, suspended_card_2]
        mock_db.execute = AsyncMock(return_value=suspended_cards_result)

        with patch.object(service, "_get_pool_in_scope", AsyncMock(return_value=pool)), \
             patch.object(service, "_get_direct_child_user_ids", AsyncMock(return_value=[3001])), \
             patch.object(service, "_enrich_pool_dict", AsyncMock()) as mock_enrich, \
             patch("app.services.pool_service.pool_crud.update_stats", AsyncMock(return_value=pool)) as mock_update_stats, \
             patch("app.services.pool_service.SuspendActionService.auto_resume_cards_after_flow_adjustment", AsyncMock(return_value={"resumed_count": 2})) as mock_auto_resume, \
             patch("app.services.pool_service.SysOperationLogCRUD.create", AsyncMock()) as mock_log_create:
            result = await service.recharge_pool(
                db=mock_db,
                pool_id=88,
                added_flow_mb=512,
                current_user_id=1001,
                user_level=UserLevel.AGENT.value,
                remark="池补量"
            )

        assert pool.addon_flow == 1536
        assert result["auto_resumed"] == 2
        mock_db.commit.assert_awaited_once()
        mock_update_stats.assert_awaited_once_with(mock_db, 88)
        mock_auto_resume.assert_awaited_once()
        mock_log_create.assert_awaited_once()
        mock_enrich.assert_awaited_once()
