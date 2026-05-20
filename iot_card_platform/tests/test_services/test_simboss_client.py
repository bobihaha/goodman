import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.clients.simboss_client import SimbossSupplierClient
from app.db.models.iot_card import CardType
from app.services.suspend_service import SuspendActionService


@pytest.fixture
def client():
    return SimbossSupplierClient(
        api_url="https://api.simboss.com",
        appid="APPID",
        app_secret="SECRET",
    )


def test_calc_sign_sorts_params(client):
    params = {
        "timestamp": "1499675521446",
        "iccid": "898606182222832823",
        "appid": "1",
    }

    result = client._calc_sign(params)

    expected = hashlib.sha256(
        "appid=1&iccid=898606182222832823&timestamp=1499675521446SECRET".encode("utf-8")
    ).hexdigest()
    assert result == expected


def test_build_url(client):
    assert client._build_url("/device/detail") == "https://api.simboss.com/2.0/device/detail"


def test_normalize_pool_usage_generates_readable_name_from_spec(client):
    payload = {
        "id": 18246,
        "poolSpecification": 51200,
        "totalVolume": 51200,
        "useVolume": 10240,
        "useRate": 0.2,
    }

    result = client._normalize_pool_usage(payload)

    assert result["supplier_pool_code"] == "18246"
    assert result["supplier_pool_name"] == "网络50GB/月"
    assert result["pool_specification"] == 51200


def test_normalize_pool_usage_prefers_supplier_name(client):
    payload = {
        "id": 46464,
        "poolName": "网络50GB/月",
        "poolSpecification": 51200,
    }

    result = client._normalize_pool_usage(payload)

    assert result["supplier_pool_name"] == "网络50GB/月"


def test_normalize_pool_usage_names_all_package_spec(client):
    payload = {
        "id": 18246,
        "poolSpecification": -1,
    }

    result = client._normalize_pool_usage(payload)

    assert result["supplier_pool_name"] == "全套餐"


@pytest.mark.asyncio
async def test_post_sends_form_payload_with_sign(client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"code": "0", "data": {"iccid": "8986"}}
    mock_resp.raise_for_status = MagicMock()

    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.post = AsyncMock(return_value=mock_resp)

    with patch("app.clients.simboss_client.time.time", return_value=1499675521.446), \
         patch("app.clients.simboss_client.httpx.AsyncClient", return_value=mock_http):
        result = await client._post("device/detail", {"iccid": "8986"})

    assert result["code"] == "0"
    sent_data = mock_http.post.call_args.kwargs["data"]
    assert sent_data["appid"] == "APPID"
    assert sent_data["timestamp"] == "1499675521446"
    assert sent_data["iccid"] == "8986"
    assert "sign" in sent_data


@pytest.mark.asyncio
async def test_post_business_error_raises(client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"code": "445", "message": "sign error", "detail": "bad sign"}
    mock_resp.raise_for_status = MagicMock()

    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.post = AsyncMock(return_value=mock_resp)

    with patch("app.clients.simboss_client.httpx.AsyncClient", return_value=mock_http):
        with pytest.raises(Exception, match="simboss POST error"):
            await client._post("device/detail", {"iccid": "8986"})


@pytest.mark.asyncio
async def test_get_card_usage_normalizes_fields(client):
    api_data = {
        "code": "0",
        "data": {
            "iccid": "89860425102490005703",
            "dataUsage": 12.5,
            "usedDataVolume": 30.2,
            "totalDataVolume": 1024,
        },
    }

    with patch.object(client, "_post", AsyncMock(return_value=api_data)):
        result = await client.get_card_usage("89860425102490005703")

    assert result["iccid"] == "89860425102490005703"
    assert result["data_used"] == 30.2
    assert result["data_used_month"] == 12.5
    assert result["data_used_scope"] == "cycle"
    assert result["data_total"] == 1024.0


@pytest.mark.asyncio
async def test_get_card_lifecycle_maps_status_and_dates(client):
    api_data = {
        "code": "0",
        "data": {
            "iccid": "89860425102490005703",
            "status": "activation",
            "testingExpireDate": "2026-05-01 00:00:00",
            "startDate": "2026-05-02 12:00:00",
            "ratePlanExpirationDate": "2027-05-31 23:59:59",
        },
    }

    with patch.object(client, "_post", AsyncMock(return_value=api_data)):
        result = await client.get_card_lifecycle("89860425102490005703")

    assert result["status"] == "activated"
    assert result["test_expire_date"] == "2026-05-01"
    assert result["activated_at"] == "2026-05-02"
    assert result["expired_at"] == "2027-05-31"


@pytest.mark.asyncio
async def test_get_card_lifecycle_prefers_deactivated_device_status(client):
    api_data = {
        "code": "0",
        "data": {
            "iccid": "89860425102490005703",
            "status": "activation",
            "deviceStatus": "DEACTIVATED_NAME",
        },
    }

    with patch.object(client, "_post", AsyncMock(return_value=api_data)):
        result = await client.get_card_lifecycle("89860425102490005703")

    assert result["status"] == "suspended"


@pytest.mark.asyncio
async def test_get_card_lifecycle_prefers_deactivation_status(client):
    api_data = {
        "code": "0",
        "data": {
            "iccid": "8986112425408902079",
            "status": "deactivation",
            "deviceStatus": "ACTIVATED_NAME",
        },
    }

    with patch.object(client, "_post", AsyncMock(return_value=api_data)):
        result = await client.get_card_lifecycle("8986112425408902079")

    assert result["status"] == "suspended"


@pytest.mark.asyncio
async def test_get_batch_usage_chunks_by_100(client):
    async def fake_post(endpoint, params):
        return {
            "code": "0",
            "data": [
                {
                    "iccid": iccid,
                    "dataUsage": 1,
                    "usedDataVolume": 2,
                    "totalDataVolume": 3,
                }
                for iccid in params["iccids"].split(",")
            ],
        }

    mock_post = AsyncMock(side_effect=fake_post)
    with patch.object(client, "_post", mock_post):
        result = await client.get_batch_usage([f"8986{i:016d}" for i in range(101)])

    assert len(result) == 101
    assert mock_post.await_count == 2


@pytest.mark.asyncio
async def test_get_traffic_pool_list_normalizes_rows(client):
    api_data = {
        "code": "0",
        "data": [
            {
                "id": 908,
                "poolSpecification": -1,
                "carrier": "cmcc",
                "totalVolume": 15.0,
                "useVolume": 3.264,
                "leftVolume": 11.736,
                "packageVolume": 0.0,
                "useRate": 0.2176,
                "totalCount": 4,
                "currentActivationCount": 2,
                "currentDeactivationCount": 1,
            }
        ],
    }

    with patch.object(client, "_post", AsyncMock(return_value=api_data)) as mock_post:
        result = await client.get_traffic_pool_list()

    mock_post.assert_awaited_once_with("card/pool/list", {})
    assert result[0]["supplier_pool_code"] == "908"
    assert result[0]["carrier"] == "cmcc"
    assert result[0]["total_flow"] == 15.0
    assert result[0]["used_flow"] == 3.264
    assert result[0]["remaining_flow"] == 11.736
    assert result[0]["usage_percent"] == 21.76
    assert result[0]["total_card_count"] == 4
    assert result[0]["active_card_count"] == 2


@pytest.mark.asyncio
async def test_suspend_and_resume_send_simboss_status(client):
    mock_post = AsyncMock(return_value={"code": "0", "data": "success"})
    mock_status_payload = AsyncMock(side_effect=[
        {"status": "deactivation", "deviceStatus": "ACTIVATED_NAME"},
        {"status": "activation", "deviceStatus": "ACTIVATED_NAME"},
    ])
    with patch.object(client, "_post", mock_post), \
         patch.object(client, "_get_status_payload", mock_status_payload):
        assert await client.suspend_card("8986") is True
        assert await client.resume_card("8986") is True

    assert mock_post.await_args_list[0].args == (
        "device/modifyDeviceStatus",
        {"iccid": "8986", "status": "DEACTIVATED_NAME"},
    )
    assert mock_post.await_args_list[1].args == (
        "device/modifyDeviceStatus",
        {"iccid": "8986", "status": "ACTIVATED_NAME"},
    )


@pytest.mark.asyncio
async def test_resume_returns_false_when_device_status_remains_deactivated(client):
    with patch.object(client, "_post", AsyncMock(return_value={"code": "0", "data": "success"})), \
         patch.object(client, "_get_status_payload", AsyncMock(return_value={
             "status": "activation",
             "deviceStatus": "DEACTIVATED_NAME",
         })):
        result = await client.resume_card("8986")

    assert result is False
    assert client.last_sor_result["submitted"] is False
    assert client.last_sor_result["observed_device_status"] == "DEACTIVATED_NAME"


@pytest.mark.asyncio
async def test_resume_returns_false_when_status_remains_deactivation(client):
    with patch.object(client, "_post", AsyncMock(return_value={"code": "0", "data": "success"})), \
         patch.object(client, "_get_status_payload", AsyncMock(return_value={
             "status": "deactivation",
             "deviceStatus": "ACTIVATED_NAME",
         })):
        result = await client.resume_card("8986")

    assert result is False
    assert client.last_sor_result["submitted"] is False
    assert client.last_sor_result["observed_status"] == "deactivation"


@pytest.mark.asyncio
async def test_get_card_imei_info_detects_split(client):
    async def fake_post(endpoint, params):
        if endpoint == "device/detail":
            return {"code": "0", "data": {"iccid": "8986", "imeiStatus": "SPLIT"}}
        return {"code": "0", "data": [{"iccid": "8986", "imei": "8667899901543856"}]}

    with patch.object(client, "_post", AsyncMock(side_effect=fake_post)):
        result = await client.get_card_imei_info("8986")

    assert result["imei"] == "8667899901543856"
    assert result["detection_status"] == "detected"
    assert result["lock_triggered"] is True


def test_simboss_network_switch_only_supports_pool_cards():
    supplier = MagicMock()
    supplier.code = "002"
    card = MagicMock()

    card.card_type = CardType.pool
    assert SuspendActionService._supplier_supports_network_switch(card, supplier) is True

    card.card_type = CardType.single
    assert SuspendActionService._supplier_supports_network_switch(card, supplier) is False


def test_non_simboss_network_switch_keeps_existing_behavior():
    supplier = MagicMock()
    supplier.code = "LX"
    card = MagicMock()
    card.card_type = CardType.single

    assert SuspendActionService._supplier_supports_network_switch(card, supplier) is True
