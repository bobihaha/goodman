from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

import pytest

from app.schemas.auth import UserLevel
from app.services.system_service import OperationLogService, LoginLogService, _china_time_to_storage, _storage_time_to_china_string


class TestLoginLogService:
    @pytest.mark.asyncio
    async def test_non_super_admin_only_sees_own_logs(self):
        fake_log = SimpleNamespace(to_dict=lambda: {"id": 1, "user_id": 23})

        with patch("app.services.system_service.SysLoginLogCRUD.get_list", new=AsyncMock(return_value=([fake_log], 1))) as mock_get_list:
            logs, total = await LoginLogService.get_logs(
                db=AsyncMock(),
                current_user_id=23,
                current_user_level=UserLevel.USER.value,
                user_id=999,
                account="other-account",
                page=1,
                page_size=20
            )

        assert total == 1
        assert logs == [{"id": 1, "user_id": 23}]
        assert mock_get_list.await_args.kwargs["user_id"] == 23

    @pytest.mark.asyncio
    async def test_super_admin_can_query_specific_user(self):
        with patch("app.services.system_service.SysLoginLogCRUD.get_list", new=AsyncMock(return_value=([], 0))) as mock_get_list:
            await LoginLogService.get_logs(
                db=AsyncMock(),
                current_user_id=1,
                current_user_level=UserLevel.SUPER_ADMIN.value,
                user_id=88,
                account="target-account",
                page=1,
                page_size=20
            )

        assert mock_get_list.await_args.kwargs["user_id"] == 88
        assert mock_get_list.await_args.kwargs["account"] == "target-account"

    def test_log_time_is_returned_as_china_time(self):
        assert _storage_time_to_china_string(datetime(2026, 5, 14, 9, 30, 0)) == "2026-05-14 09:30:00"

    def test_china_query_time_is_converted_to_storage_time(self):
        assert _china_time_to_storage(datetime(2026, 5, 14, 9, 30, 0)) == datetime(2026, 5, 14, 9, 30, 0)

    def test_aware_utc_time_is_converted_to_china_time(self):
        utc_value = datetime(2026, 5, 14, 1, 30, 0, tzinfo=timezone.utc)
        assert _china_time_to_storage(utc_value) == datetime(2026, 5, 14, 9, 30, 0)


class TestOperationLogService:
    @pytest.mark.asyncio
    async def test_module_filter_matches_legacy_card_module_values(self):
        with patch("app.services.system_service.SysOperationLogCRUD.get_list", new=AsyncMock(return_value=([], 0))) as mock_get_list:
            await OperationLogService.get_logs(
                db=AsyncMock(),
                current_user_id=1,
                current_user_level=UserLevel.SUPER_ADMIN.value,
                module="card",
                page=1,
                page_size=20
            )

        assert mock_get_list.await_args.kwargs["module"] is None
        assert mock_get_list.await_args.kwargs["modules"] == ["card", "cards", "orders"]
        assert mock_get_list.await_args.kwargs["actions"] == [
            "transfer",
            "update_remark",
            "suspend",
            "resume",
            "restart",
            "renew",
            "add_flow",
            "card_renew_purchase",
            "card_topup_purchase",
        ]

    @pytest.mark.asyncio
    async def test_suspend_filter_matches_card_suspend_and_resume_logs(self):
        with patch("app.services.system_service.SysOperationLogCRUD.get_list", new=AsyncMock(return_value=([], 0))) as mock_get_list:
            await OperationLogService.get_logs(
                db=AsyncMock(),
                current_user_id=12,
                current_user_level=UserLevel.SUB_USER.value,
                module="suspend",
            )

        assert mock_get_list.await_args.kwargs["modules"] == ["suspend", "card"]
        assert mock_get_list.await_args.kwargs["actions"] == ["suspend", "resume", "restart"]
        assert mock_get_list.await_args.kwargs["user_ids"] == [12]

    @pytest.mark.asyncio
    async def test_parent_user_sees_own_and_child_operation_logs(self):
        with patch(
            "app.services.system_service.SysUserCRUDEnhanced.get_children_ids",
            new=AsyncMock(return_value=[13, 14]),
        ), patch(
            "app.services.system_service.SysOperationLogCRUD.get_list",
            new=AsyncMock(return_value=([], 0)),
        ) as mock_get_list:
            await OperationLogService.get_logs(
                db=AsyncMock(),
                current_user_id=12,
                current_user_level=UserLevel.USER.value,
                module="card",
            )

        assert mock_get_list.await_args.kwargs["user_ids"] == [12, 13, 14]
