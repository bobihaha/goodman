"""
一期补量与复机接口回归测试
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.main import app
from app.schemas.auth import CurrentUser
from app.utils.auth import get_current_user


async def override_admin_user():
    return CurrentUser(
        id=1,
        parent_id=None,
        user_level=1,
        name="超管",
        account="admin",
        phone=None,
        email=None,
        avatar=None,
        status="enable",
        permissions=[],
        is_super_login=False,
        original_user_id=None
    )


async def override_agent_user():
    return CurrentUser(
        id=2,
        parent_id=None,
        user_level=2,
        name="一级用户",
        account="agent",
        phone=None,
        email=None,
        avatar=None,
        status="enable",
        permissions=[],
        is_super_login=False,
        original_user_id=None
    )


class TestFlowAdjustmentApi:
    @pytest.mark.asyncio
    async def test_batch_add_flow_by_iccids_route(self, async_client):
        app.dependency_overrides[get_current_user] = override_agent_user

        mock_result = {
            "success": 1,
            "failed": 0,
            "success_list": [{"iccid": "8986000000000000101"}],
            "failed_list": [],
            "auto_resumed": 1
        }

        with patch("app.api.v1.iot_card.iot_card_service.batch_add_flow_by_iccids", AsyncMock(return_value=mock_result)) as mock_service:
            response = await async_client.post(
                "/api/v1/cards/batch/add-flow-by-iccids",
                json={
                    "iccids": ["8986000000000000101"],
                    "added_flow_mb": 512,
                    "remark": "后台补量"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "自动复机1张" in data["msg"]
        assert data["data"]["auto_resumed"] == 1
        mock_service.assert_awaited_once()
        _, kwargs = mock_service.await_args
        assert kwargs["iccids"] == ["8986000000000000101"]
        assert kwargs["added_flow_mb"] == 512
        assert kwargs["current_user_id"] == 2
        assert kwargs["user_level"] == 2

    @pytest.mark.asyncio
    async def test_recharge_pool_route(self, async_client):
        app.dependency_overrides[get_current_user] = override_agent_user

        mock_result = {
            "id": 88,
            "name": "测试池",
            "auto_resumed": 2
        }

        with patch("app.api.v1.pool.pool_service.recharge_pool", AsyncMock(return_value=mock_result)) as mock_service:
            response = await async_client.post(
                "/api/v1/pools/88/recharge",
                json={
                    "added_flow_mb": 1024,
                    "remark": "池补量"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "自动复机 2 张卡片" in data["msg"]
        assert data["data"]["id"] == 88
        mock_service.assert_awaited_once()
        _, kwargs = mock_service.await_args
        assert kwargs["pool_id"] == 88
        assert kwargs["added_flow_mb"] == 1024
        assert kwargs["current_user_id"] == 2
        assert kwargs["user_level"] == 2

    @pytest.mark.asyncio
    async def test_force_resume_requires_super_admin(self, async_client):
        app.dependency_overrides[get_current_user] = override_agent_user

        response = await async_client.post(
            "/api/v1/cards/batch/force-resume-by-iccids",
            json=["8986000000000000101"]
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 403
        assert data["msg"] == "仅超级管理员可强制复机"

    @pytest.mark.asyncio
    async def test_force_resume_route_for_super_admin(self, async_client):
        app.dependency_overrides[get_current_user] = override_admin_user

        mock_result = {
            "success": 1,
            "failed": 0,
            "success_list": [{"iccid": "8986000000000000102"}],
            "failed_list": []
        }

        with patch("app.api.v1.iot_card.iot_card_service.batch_force_resume_by_iccids", AsyncMock(return_value=mock_result)) as mock_service:
            response = await async_client.post(
                "/api/v1/cards/batch/force-resume-by-iccids",
                json=["8986000000000000102"]
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "成功1张" in data["msg"]
        mock_service.assert_awaited_once()
        _, kwargs = mock_service.await_args
        assert kwargs["iccids"] == ["8986000000000000102"]
        assert kwargs["current_user_id"] == 1
