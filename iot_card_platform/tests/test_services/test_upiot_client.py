"""
UpiotSupplierClient 单元测试
覆盖: 签名计算、URL构建、GET/POST请求、各业务接口、停复机
"""
import hashlib
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.clients.upiot_client import UpiotSupplierClient, UPIOT_STATUS_MAP


# ========== Fixtures ==========

@pytest.fixture
def client():
    return UpiotSupplierClient(
        api_url="http://ec.upiot.net",
        api_key="TEST_API_KEY",
        api_secret="TEST_API_SECRET",
    )


def md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


# ========== 签名计算 ==========

class TestSignature:
    def test_md5(self, client):
        assert client._md5("hello") == hashlib.md5(b"hello").hexdigest()

    def test_get_sign_no_params(self, client):
        expected = md5("TEST_API_SECRET")
        assert client._calc_get_sign(None) == expected

    def test_get_sign_with_params(self, client):
        params = {"b": "2", "a": "1"}
        # 排序后: a=1, b=2 -> "a=1b=2TEST_API_SECRET"
        expected = md5("a=1b=2TEST_API_SECRET")
        assert client._calc_get_sign(params) == expected

    def test_post_sign(self, client):
        body_str = '{"iccids":["8986"]}'
        expected = md5(body_str + "TEST_API_SECRET")
        assert client._calc_post_sign(body_str) == expected

    def test_get_auth_headers_empty(self, client):
        assert client._get_auth_headers() == {}


# ========== URL 构建 ==========

class TestBuildUrl:
    def test_basic(self, client):
        url = client._build_url("card/8986")
        assert url == "http://ec.upiot.net/api/v2/TEST_API_KEY/card/8986/"

    def test_trailing_slash_stripped(self, client):
        c = UpiotSupplierClient("http://ec.upiot.net/", "KEY", "SECRET")
        url = c._build_url("/card/8986/")
        assert url == "http://ec.upiot.net/api/v2/KEY/card/8986/"

    def test_default_url_when_empty(self):
        c = UpiotSupplierClient("", "KEY", "SECRET")
        assert c.api_url == "http://ec.upiot.net"


# ========== 辅助方法 ==========

class TestHelpers:
    def test_parse_float_normal(self, client):
        assert client._parse_float("30.000") == 30.0

    def test_parse_float_none(self, client):
        assert client._parse_float(None) == 0.0

    def test_parse_float_invalid(self, client):
        assert client._parse_float("abc") == 0.0

    def test_map_status_known(self, client):
        assert client._map_status("00") == "activated"
        assert client._map_status("02") == "suspended"
        assert client._map_status("04") == "cancelled"

    def test_map_status_unknown(self, client):
        assert client._map_status("99") == "unknown"
        assert client._map_status("XX") == "unknown"


# ========== GET 请求 ==========

class TestGetRequest:
    @pytest.mark.asyncio
    async def test_get_success(self, client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"code": 200, "data": {"iccid": "8986"}}
        mock_resp.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.get = AsyncMock(return_value=mock_resp)

        with patch("app.clients.upiot_client.httpx.AsyncClient", return_value=mock_http):
            result = await client._get("card/8986")

        assert result["code"] == 200
        assert result["data"]["iccid"] == "8986"

    @pytest.mark.asyncio
    async def test_get_api_error(self, client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"code": 401, "msg": "签名错误"}
        mock_resp.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.get = AsyncMock(return_value=mock_resp)

        with patch("app.clients.upiot_client.httpx.AsyncClient", return_value=mock_http):
            with pytest.raises(Exception, match="upiot GET error"):
                await client._get("card/8986")

    @pytest.mark.asyncio
    async def test_get_non_json_response(self, client):
        """响应体非JSON时抛出含响应内容的错误"""
        mock_resp = MagicMock()
        mock_resp.json.side_effect = ValueError("No JSON")
        mock_resp.status_code = 200
        mock_resp.text = "<html>Error Page</html>"
        mock_resp.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.get = AsyncMock(return_value=mock_resp)

        with patch("app.clients.upiot_client.httpx.AsyncClient", return_value=mock_http):
            with pytest.raises(Exception, match="响应非JSON"):
                await client._get("card/8986")

    @pytest.mark.asyncio
    async def test_get_sign_appended_to_params(self, client):
        """验证 _sign 参数被正确附加到请求"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"code": 200, "data": {}}
        mock_resp.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.get = AsyncMock(return_value=mock_resp)

        with patch("app.clients.upiot_client.httpx.AsyncClient", return_value=mock_http):
            await client._get("card/8986", params={"page": 1})

        call_kwargs = mock_http.get.call_args
        sent_params = call_kwargs[1]["params"]
        assert "_sign" in sent_params
        assert sent_params["page"] == 1


# ========== POST 请求 ==========

class TestPostRequest:
    @pytest.mark.asyncio
    async def test_post_success(self, client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"code": 200, "data": []}
        mock_resp.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.post = AsyncMock(return_value=mock_resp)

        with patch("app.clients.upiot_client.httpx.AsyncClient", return_value=mock_http):
            result = await client._post("batch/card/info", {"iccids": ["8986"]})

        assert result["code"] == 200

    @pytest.mark.asyncio
    async def test_post_sign_in_url(self, client):
        """验证签名附加在 URL query string 中"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"code": 200, "data": []}
        mock_resp.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.post = AsyncMock(return_value=mock_resp)

        with patch("app.clients.upiot_client.httpx.AsyncClient", return_value=mock_http):
            await client._post("sor", {"number": "8986", "type": "01"})

        call_args = mock_http.post.call_args
        url_called = call_args[0][0]
        assert "_sign=" in url_called

    @pytest.mark.asyncio
    async def test_post_api_error(self, client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"code": 500, "msg": "服务器错误"}
        mock_resp.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.post = AsyncMock(return_value=mock_resp)

        with patch("app.clients.upiot_client.httpx.AsyncClient", return_value=mock_http):
            with pytest.raises(Exception, match="upiot POST error"):
                await client._post("sor", {"number": "8986", "type": "01"})


# ========== 业务接口 ==========

class TestGetCardUsage:
    @pytest.mark.asyncio
    async def test_returns_normalized_fields(self, client):
        api_data = {
            "code": 200,
            "data": {
                "iccid": "898600000000001",
                "data_usage": "512.000",
                "data_traffic_amount": "1024.000",
            }
        }
        with patch.object(client, "_get", AsyncMock(return_value=api_data)):
            result = await client.get_card_usage("898600000000001")

        assert result["iccid"] == "898600000000001"
        assert result["data_used"] == 512.0
        assert result["data_total"] == 1024.0
        assert "sync_time" in result

    @pytest.mark.asyncio
    async def test_fallback_iccid_from_param(self, client):
        api_data = {"code": 200, "data": {}}
        with patch.object(client, "_get", AsyncMock(return_value=api_data)):
            result = await client.get_card_usage("898600000000001")
        assert result["iccid"] == "898600000000001"


class TestGetBatchUsage:
    @pytest.mark.asyncio
    async def test_single_batch(self, client):
        api_data = {
            "code": 200,
            "data": {
                "rows": [
                    {"iccid": "A", "data_usage": "100", "data_plan": "1024", "updated_time": "2026-01-01 00:00:00"},
                    {"iccid": "B", "data_usage": "200", "data_plan": "1024", "updated_time": ""},
                ]
            }
        }
        with patch.object(client, "_post", AsyncMock(return_value=api_data)):
            results = await client.get_batch_usage(["A", "B"])

        assert len(results) == 2
        assert results[0]["iccid"] == "A"
        assert results[0]["data_used"] == 100.0
        assert results[1]["sync_time"] != ""  # fallback to now

    @pytest.mark.asyncio
    async def test_splits_into_batches_of_50(self, client):
        iccids = [str(i) for i in range(110)]
        api_data = {"code": 200, "data": {"rows": []}}
        mock_post = AsyncMock(return_value=api_data)

        with patch.object(client, "_post", mock_post):
            await client.get_batch_usage(iccids)

        # 110 cards -> 3 batches: 50, 50, 10
        assert mock_post.call_count == 3


class TestGetCardLifecycle:
    @pytest.mark.asyncio
    async def test_returns_normalized_fields(self, client):
        api_data = {
            "code": 200,
            "data": {
                "iccid": "898600000000001",
                "test_valid_date": "2026-01-31",
                "silent_valid_date": "2026-04-30",
                "active_date": "2026-02-01",
                "expiry_date": "2027-02-01",
                "account_status": "00",
            }
        }
        with patch.object(client, "_get", AsyncMock(return_value=api_data)):
            result = await client.get_card_lifecycle("898600000000001")

        assert result["status"] == "activated"
        assert result["test_expire_date"] == "2026-01-31"
        assert result["expired_at"] == "2027-02-01"

    @pytest.mark.asyncio
    async def test_unknown_status(self, client):
        api_data = {"code": 200, "data": {"account_status": "99"}}
        with patch.object(client, "_get", AsyncMock(return_value=api_data)):
            result = await client.get_card_lifecycle("X")
        assert result["status"] == "unknown"


class TestGetBatchLifecycle:
    @pytest.mark.asyncio
    async def test_returns_list(self, client):
        api_data = {
            "code": 200,
            "data": [
                {"iccid": "A", "account_status": "00", "test_valid_date": "", "silent_valid_date": "", "active_date": "", "expiry_date": ""},
                {"iccid": "B", "account_status": "02", "test_valid_date": "", "silent_valid_date": "", "active_date": "", "expiry_date": ""},
            ]
        }
        with patch.object(client, "_post", AsyncMock(return_value=api_data)):
            results = await client.get_batch_lifecycle(["A", "B"])

        assert len(results) == 2
        assert results[0]["status"] == "activated"
        assert results[1]["status"] == "suspended"

    @pytest.mark.asyncio
    async def test_splits_into_batches_of_50(self, client):
        iccids = [str(i) for i in range(60)]
        api_data = {"code": 200, "data": []}
        mock_post = AsyncMock(return_value=api_data)

        with patch.object(client, "_post", mock_post):
            await client.get_batch_lifecycle(iccids)

        assert mock_post.call_count == 2


# ========== 停复机 ==========

class TestSuspendResumeCard:
    @pytest.mark.asyncio
    async def test_suspend_success(self, client):
        with patch.object(client, "_post", AsyncMock(return_value={"code": 200})):
            result = await client.suspend_card("898600000000001")
        assert result is True

    @pytest.mark.asyncio
    async def test_suspend_failure_returns_false(self, client):
        with patch.object(client, "_post", AsyncMock(side_effect=Exception("网络错误"))):
            result = await client.suspend_card("898600000000001")
        assert result is False

    @pytest.mark.asyncio
    async def test_resume_success(self, client):
        with patch.object(client, "_post", AsyncMock(return_value={"code": 200})):
            result = await client.resume_card("898600000000001")
        assert result is True

    @pytest.mark.asyncio
    async def test_resume_failure_returns_false(self, client):
        with patch.object(client, "_post", AsyncMock(side_effect=Exception("超时"))):
            result = await client.resume_card("898600000000001")
        assert result is False

    @pytest.mark.asyncio
    async def test_suspend_sends_type_01(self, client):
        mock_post = AsyncMock(return_value={"code": 200})
        with patch.object(client, "_post", mock_post):
            await client.suspend_card("8986", reason="欠费")
        mock_post.assert_called_once_with("sor", {"number": "8986", "type": "01"})

    @pytest.mark.asyncio
    async def test_resume_sends_type_00(self, client):
        mock_post = AsyncMock(return_value={"code": 200})
        with patch.object(client, "_post", mock_post):
            await client.resume_card("8986")
        mock_post.assert_called_once_with("sor", {"number": "8986", "type": "00"})


# ========== 工厂函数 ==========

class TestGetSupplierClient:
    def test_upiot_url_returns_upiot_client(self):
        from app.clients.supplier_api import get_supplier_client
        c = get_supplier_client(1, "http://ec.upiot.net", "K", "S")
        assert isinstance(c, UpiotSupplierClient)

    def test_unknown_url_returns_mock_client(self):
        from app.clients.supplier_api import get_supplier_client, MockSupplierAPIClient
        c = get_supplier_client(1, "http://other-supplier.com", "K", "S")
        assert isinstance(c, MockSupplierAPIClient)

    def test_upiot_case_insensitive(self):
        from app.clients.supplier_api import get_supplier_client
        c = get_supplier_client(1, "http://EC.UPIOT.NET", "K", "S")
        assert isinstance(c, UpiotSupplierClient)
