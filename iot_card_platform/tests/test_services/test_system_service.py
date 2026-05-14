from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from datetime import datetime

import pytest

from app.schemas.auth import UserLevel
from app.services.system_service import LoginLogService, _china_time_to_storage, _storage_time_to_china_string


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
        assert _storage_time_to_china_string(datetime(2026, 5, 14, 1, 30, 0)) == "2026-05-14 09:30:00"

    def test_china_query_time_is_converted_to_storage_time(self):
        assert _china_time_to_storage(datetime(2026, 5, 14, 9, 30, 0)) == datetime(2026, 5, 14, 1, 30, 0)
