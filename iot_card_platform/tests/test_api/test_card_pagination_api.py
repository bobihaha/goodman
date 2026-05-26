from unittest.mock import AsyncMock, patch

import pytest

from app.main import app
from app.schemas.auth import CurrentUser
from app.utils.auth import get_current_user


async def override_user():
    return CurrentUser(
        id=2,
        parent_id=None,
        user_level=2,
        name="一级用户",
        account="agent",
        status="enable",
    )


class TestCardPaginationApi:
    @pytest.mark.asyncio
    async def test_card_list_accepts_200_items_per_page(self, async_client):
        app.dependency_overrides[get_current_user] = override_user

        with patch(
            "app.api.v1.iot_card.iot_card_service.get_cards",
            AsyncMock(return_value=([], 0)),
        ) as mock_service:
            response = await async_client.get("/api/v1/cards?page=1&page_size=200")

        assert response.status_code == 200
        assert response.json()["data"]["page_size"] == 200
        _, kwargs = mock_service.await_args
        assert kwargs["page_size"] == 200

    @pytest.mark.asyncio
    async def test_card_list_rejects_more_than_200_items_per_page(self, async_client):
        app.dependency_overrides[get_current_user] = override_user

        with patch(
            "app.api.v1.iot_card.iot_card_service.get_cards",
            AsyncMock(return_value=([], 0)),
        ) as mock_service:
            response = await async_client.get("/api/v1/cards?page=1&page_size=201")

        assert response.status_code == 422
        mock_service.assert_not_awaited()
