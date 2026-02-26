"""
SupplierService 单元测试
覆盖: test_api_connection (含 TODO stub 行为验证)、create/get/delete 异常路径
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.supplier_service import SupplierService
from app.utils.exceptions import BusinessException


@pytest.fixture
def service():
    return SupplierService()


@pytest.fixture
def mock_db():
    return AsyncMock()


# ========== test_api_connection ==========

class TestApiConnection:
    @pytest.mark.asyncio
    async def test_supplier_not_found_raises(self, service, mock_db):
        with patch("app.services.supplier_service.supplier_crud") as mock_crud:
            mock_crud.get_by_id = AsyncMock(return_value=None)
            with pytest.raises(BusinessException) as exc:
                await service.test_api_connection(mock_db, 999)
            assert exc.value.code == 404

    @pytest.mark.asyncio
    async def test_no_api_url_raises(self, service, mock_db):
        supplier = MagicMock()
        supplier.api_url = None
        with patch("app.services.supplier_service.supplier_crud") as mock_crud:
            mock_crud.get_by_id = AsyncMock(return_value=supplier)
            with pytest.raises(BusinessException) as exc:
                await service.test_api_connection(mock_db, 1)
            assert exc.value.code == 400

    @pytest.mark.asyncio
    async def test_no_api_key_raises(self, service, mock_db):
        supplier = MagicMock()
        supplier.api_url = "http://ec.upiot.net"
        supplier.api_key = None
        supplier.api_secret = "secret"
        with patch("app.services.supplier_service.supplier_crud") as mock_crud:
            mock_crud.get_by_id = AsyncMock(return_value=supplier)
            with pytest.raises(BusinessException) as exc:
                await service.test_api_connection(mock_db, 1)
            assert exc.value.code == 400

    @pytest.mark.asyncio
    async def test_no_api_secret_raises(self, service, mock_db):
        supplier = MagicMock()
        supplier.api_url = "http://ec.upiot.net"
        supplier.api_key = "key"
        supplier.api_secret = None
        with patch("app.services.supplier_service.supplier_crud") as mock_crud:
            mock_crud.get_by_id = AsyncMock(return_value=supplier)
            with pytest.raises(BusinessException) as exc:
                await service.test_api_connection(mock_db, 1)
            assert exc.value.code == 400

    @pytest.mark.asyncio
    async def test_connection_success_no_exception(self, service, mock_db):
        """客户端调用成功（无异常）-> success=True"""
        supplier = MagicMock()
        supplier.api_url = "http://ec.upiot.net"
        supplier.api_key = "KEY"
        supplier.api_secret = "SECRET"
        mock_client = AsyncMock()
        mock_client.get_card_usage = AsyncMock(return_value={"iccid": "000000000000000"})
        with patch("app.services.supplier_service.supplier_crud") as mock_crud, \
             patch("app.services.supplier_service.get_supplier_client", return_value=mock_client):
            mock_crud.get_by_id = AsyncMock(return_value=supplier)
            result = await service.test_api_connection(mock_db, 1)
        assert result["success"] is True
        assert result["supplier_id"] == 1

    @pytest.mark.asyncio
    async def test_connection_success_on_upiot_business_error(self, service, mock_db):
        """upiot 返回业务错误（卡不存在）也视为连通成功"""
        supplier = MagicMock()
        supplier.api_url = "http://ec.upiot.net"
        supplier.api_key = "KEY"
        supplier.api_secret = "SECRET"
        mock_client = AsyncMock()
        mock_client.get_card_usage = AsyncMock(
            side_effect=Exception("upiot GET error: code=404, msg=card not found")
        )
        with patch("app.services.supplier_service.supplier_crud") as mock_crud, \
             patch("app.services.supplier_service.get_supplier_client", return_value=mock_client):
            mock_crud.get_by_id = AsyncMock(return_value=supplier)
            result = await service.test_api_connection(mock_db, 1)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_connection_failure_on_network_error(self, service, mock_db):
        """网络不通 -> success=False，message 包含错误信息"""
        supplier = MagicMock()
        supplier.api_url = "http://ec.upiot.net"
        supplier.api_key = "KEY"
        supplier.api_secret = "SECRET"
        mock_client = AsyncMock()
        mock_client.get_card_usage = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        with patch("app.services.supplier_service.supplier_crud") as mock_crud, \
             patch("app.services.supplier_service.get_supplier_client", return_value=mock_client):
            mock_crud.get_by_id = AsyncMock(return_value=supplier)
            result = await service.test_api_connection(mock_db, 1)
        assert result["success"] is False
        assert "Connection refused" in result["message"]


# ========== create_supplier ==========

class TestCreateSupplier:
    @pytest.mark.asyncio
    async def test_duplicate_code_raises(self, service, mock_db):
        data = MagicMock()
        data.code = "UPIOT_001"
        with patch("app.services.supplier_service.supplier_crud") as mock_crud:
            mock_crud.get_by_code = AsyncMock(return_value=MagicMock())
            with pytest.raises(BusinessException) as exc:
                await service.create_supplier(mock_db, data, created_by=1)
            assert exc.value.code == 400
            assert "UPIOT_001" in exc.value.msg

    @pytest.mark.asyncio
    async def test_create_success(self, service, mock_db):
        data = MagicMock()
        data.code = "NEW_001"
        supplier = MagicMock()
        supplier.to_dict.return_value = {"id": 1, "code": "NEW_001"}
        with patch("app.services.supplier_service.supplier_crud") as mock_crud:
            mock_crud.get_by_code = AsyncMock(return_value=None)
            mock_crud.create = AsyncMock(return_value=supplier)
            result = await service.create_supplier(mock_db, data, created_by=1)
        assert result["code"] == "NEW_001"


# ========== get_supplier ==========

class TestGetSupplier:
    @pytest.mark.asyncio
    async def test_not_found_raises(self, service, mock_db):
        with patch("app.services.supplier_service.supplier_crud") as mock_crud:
            mock_crud.get_by_id = AsyncMock(return_value=None)
            with pytest.raises(BusinessException) as exc:
                await service.get_supplier(mock_db, 999)
            assert exc.value.code == 404

    @pytest.mark.asyncio
    async def test_found_returns_dict(self, service, mock_db):
        supplier = MagicMock()
        supplier.to_dict.return_value = {"id": 5, "name": "优博讯"}
        with patch("app.services.supplier_service.supplier_crud") as mock_crud:
            mock_crud.get_by_id = AsyncMock(return_value=supplier)
            result = await service.get_supplier(mock_db, 5)
        assert result["id"] == 5


# ========== delete_supplier ==========

class TestDeleteSupplier:
    @pytest.mark.asyncio
    async def test_not_found_raises(self, service, mock_db):
        with patch("app.services.supplier_service.supplier_crud") as mock_crud:
            mock_crud.get_by_id = AsyncMock(return_value=None)
            with pytest.raises(BusinessException) as exc:
                await service.delete_supplier(mock_db, 999)
            assert exc.value.code == 404

    @pytest.mark.asyncio
    async def test_delete_blocked_by_packages(self, service, mock_db):
        supplier = MagicMock()
        with patch("app.services.supplier_service.supplier_crud") as mock_crud:
            mock_crud.get_by_id = AsyncMock(return_value=supplier)
            mock_crud.count_packages = AsyncMock(return_value=3)
            mock_crud.count_cards = AsyncMock(return_value=0)
            with pytest.raises(BusinessException) as exc:
                await service.delete_supplier(mock_db, 1)
            assert exc.value.code == 400
            assert "3" in exc.value.msg
            assert "套餐" in exc.value.msg

    @pytest.mark.asyncio
    async def test_delete_blocked_by_cards(self, service, mock_db):
        supplier = MagicMock()
        with patch("app.services.supplier_service.supplier_crud") as mock_crud:
            mock_crud.get_by_id = AsyncMock(return_value=supplier)
            mock_crud.count_packages = AsyncMock(return_value=0)
            mock_crud.count_cards = AsyncMock(return_value=100)
            with pytest.raises(BusinessException) as exc:
                await service.delete_supplier(mock_db, 1)
            assert exc.value.code == 400
            assert "100" in exc.value.msg
            assert "卡片" in exc.value.msg

    @pytest.mark.asyncio
    async def test_delete_success(self, service, mock_db):
        supplier = MagicMock()
        with patch("app.services.supplier_service.supplier_crud") as mock_crud:
            mock_crud.get_by_id = AsyncMock(return_value=supplier)
            mock_crud.count_packages = AsyncMock(return_value=0)
            mock_crud.count_cards = AsyncMock(return_value=0)
            mock_crud.delete = AsyncMock(return_value=True)
            result = await service.delete_supplier(mock_db, 1)
        assert result is True
