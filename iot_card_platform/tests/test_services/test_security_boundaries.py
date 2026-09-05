from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock, patch

import pytest
from starlette.requests import Request

from app.api.v1.callback import upiot_sor_callback
from app.crud.sys_user_crud import sys_user_crud
from app.db.models.sys_user import UserLevel, UserStatus
from app.schemas.auth import CurrentUser
from app.schemas.sys_user import UserPasswordReset, UserUpdate
from app.services.auth_service import AuthService
from app.services.h5_service import H5Service
from app.services.permission_service import permission_service
from app.services.sys_user_service import SysUserService
from app.utils.exceptions import AuthException, BusinessException, PermissionDeniedException


def _operator(user_id: int, level: int, parent_id=None) -> CurrentUser:
    return CurrentUser(
        id=user_id,
        parent_id=parent_id,
        user_level=level,
        name=f"user-{user_id}",
        account=f"account-{user_id}",
        status="enable",
    )


@pytest.mark.asyncio
async def test_user_cannot_change_own_balance_through_generic_update():
    target = SimpleNamespace(id=2, quota={"account_balance": 100}, user_level=2, parent_id=1)
    with patch.object(
        sys_user_crud,
        "get_by_id",
        AsyncMock(return_value=target),
    ), patch.object(sys_user_crud, "update", AsyncMock()) as update:
        with pytest.raises(PermissionDeniedException):
            await SysUserService.update_user(
                AsyncMock(),
                _operator(2, UserLevel.USER.value),
                2,
                UserUpdate(quota={"account_balance": 999999}),
            )

    update.assert_not_awaited()


@pytest.mark.asyncio
async def test_admin_partial_quota_update_preserves_financial_and_unsent_fields():
    target = SimpleNamespace(
        id=2,
        quota={"account_balance": 100, "max_cards": 10, "max_sub_users": 3},
        user_level=2,
        parent_id=1,
    )
    update = AsyncMock(return_value=target)
    with patch.object(sys_user_crud, "get_by_id", AsyncMock(return_value=target)), patch.object(
        sys_user_crud,
        "update",
        update,
    ), patch.object(SysUserService, "_build_user_info", return_value={}):
        await SysUserService.update_user(
            AsyncMock(),
            _operator(1, UserLevel.SUPER_ADMIN.value),
            2,
            UserUpdate(quota={"account_balance": 999, "max_cards": 20}),
        )

    quota = update.await_args.kwargs["obj_in"]["quota"]
    assert quota == {"account_balance": 100, "max_cards": 20, "max_sub_users": 3}


@pytest.mark.asyncio
async def test_status_change_invalidates_existing_sessions():
    target = SimpleNamespace(id=2, quota={}, user_level=2, parent_id=1, token_version=7)
    update = AsyncMock(return_value=target)
    with patch.object(sys_user_crud, "get_by_id", AsyncMock(return_value=target)), patch.object(
        sys_user_crud,
        "update",
        update,
    ), patch.object(SysUserService, "_build_user_info", return_value={}):
        await SysUserService.change_status(
            AsyncMock(),
            _operator(1, UserLevel.SUPER_ADMIN.value),
            2,
            UserStatus.disable,
        )

    assert update.await_args.kwargs["obj_in"]["token_version"] == 8


@pytest.mark.asyncio
async def test_self_password_reset_requires_old_password_flow():
    target = SimpleNamespace(id=2, user_level=2, parent_id=1)
    with patch.object(sys_user_crud, "get_by_id", AsyncMock(return_value=target)):
        with pytest.raises(BusinessException, match="验证旧密码"):
            await SysUserService.reset_password(
                AsyncMock(),
                _operator(2, UserLevel.USER.value),
                2,
                UserPasswordReset(new_password="StrongPass123"),
            )


@pytest.mark.asyncio
async def test_subuser_cannot_clear_parent_permissions():
    target = SimpleNamespace(id=2, user_level=UserLevel.USER.value, parent_id=1)
    with patch(
        "app.services.permission_service.sys_user_crud.get_by_id",
        AsyncMock(return_value=target),
    ):
        with pytest.raises(PermissionDeniedException):
            await permission_service.ensure_user_access(
                AsyncMock(),
                _operator(3, UserLevel.SUB_USER.value, parent_id=2),
                2,
                for_write=True,
            )


def test_token_version_mismatch_invalidates_old_session():
    with pytest.raises(AuthException):
        AuthService._verify_token_version(
            {"tv": 1},
            SimpleNamespace(token_version=2),
        )


def test_h5_verify_configuration_fails_closed():
    with pytest.raises(BusinessException, match="验证码服务尚未配置"):
        H5Service._enforce_verification(SimpleNamespace(h5_require_verify=1), "123456")


def _request(token: str = "") -> Request:
    headers = []
    if token:
        headers.append((b"x-upiot-callback-token", token.encode()))
    return Request({
        "type": "http",
        "method": "POST",
        "path": "/api/v1/callback/upiot/sor",
        "headers": headers,
        "query_string": b"",
    })


@pytest.mark.asyncio
async def test_callback_rejects_invalid_shared_token():
    with patch("app.api.v1.callback.settings.upiot_callback_token", "expected"):
        response = await upiot_sor_callback(_request("wrong"), AsyncMock())

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_callback_accepts_valid_shared_token_without_logging_secret():
    payload = {"callback_no": "cb-1", "code": "200", "account_status": "02"}
    with patch(
        "app.api.v1.callback.settings.upiot_callback_token",
        "expected",
    ), patch(
        "app.api.v1.callback._parse_callback_payload",
        AsyncMock(return_value=payload),
    ), patch(
        "app.api.v1.callback.SupplierCallbackService.handle_upiot_sor_callback",
        AsyncMock(),
    ) as handle:
        response = await upiot_sor_callback(_request("expected"), AsyncMock())

    assert response.status_code == 200
    handle.assert_awaited_once_with(ANY, payload)
