from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.auth import UserLevel
from app.services.system_service import LoginLogService


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
