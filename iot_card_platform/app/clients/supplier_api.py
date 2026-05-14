"""
供应商API客户端基类
用于对接不同供应商的API
"""
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import httpx
from datetime import datetime
from app.config import settings


class SupplierAPIClient(ABC):
    """供应商API客户端抽象基类"""

    def __init__(self, api_url: str, api_key: str, api_secret: str, timeout: float = 30.0):
        self.api_url = api_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout

    @abstractmethod
    async def get_card_usage(self, iccid: str) -> Dict[str, Any]:
        """
        获取单卡流量使用情况
        
        返回格式:
        {
            "iccid": "89860123456789012345",
            "data_used": 1024,  # 已用流量(MB)
            "data_total": 5120,  # 总流量(MB)
            "sync_time": "2026-02-09 12:00:00"
        }
        """
        pass

    @abstractmethod
    async def get_batch_usage(self, iccid_list: List[str]) -> List[Dict[str, Any]]:
        """
        批量获取卡片流量使用情况
        
        返回格式:
        [
            {
                "iccid": "89860123456789012345",
                "data_used": 1024,
                "data_total": 5120,
                "sync_time": "2026-02-09 12:00:00"
            },
            ...
        ]
        """
        pass

    @abstractmethod
    async def get_card_lifecycle(self, iccid: str) -> Dict[str, Any]:
        """
        获取单卡生命周期信息
        
        返回格式:
        {
            "iccid": "89860123456789012345",
            "test_expire_date": "2026-01-31",  # 测试期到期日
            "silent_expire_date": "2026-04-30",  # 沉默期到期日
            "activated_at": "2026-02-01",  # 激活日期
            "expired_at": "2027-02-01",  # 过期日期
            "status": "activated"  # 状态
        }
        """
        pass

    @abstractmethod
    async def get_batch_lifecycle(self, iccid_list: List[str]) -> List[Dict[str, Any]]:
        """
        批量获取卡片生命周期信息
        """
        pass

    @abstractmethod
    async def suspend_card(self, iccid: str, reason: Optional[str] = None, callback_no: Optional[str] = None) -> bool:
        """
        停卡
        """
        pass

    @abstractmethod
    async def resume_card(self, iccid: str, callback_no: Optional[str] = None) -> bool:
        """
        复机
        """
        pass

    @abstractmethod
    async def force_activate_card(self, iccid: str, card_no: Optional[str] = None) -> bool:
        """
        强制激活
        """
        pass

    @abstractmethod
    async def get_card_diagnostics(self, iccid: str) -> Dict[str, Any]:
        """
        获取单卡诊断状态

        返回格式:
        {
            "iccid": "89860123456789012345",
            "power_status": "0",
            "power_status_msg": "开机",
            "work_status": "1",
            "work_status_msg": "离线"
        }
        """
        pass

    @abstractmethod
    async def get_card_imei_info(self, iccid: str) -> Dict[str, Any]:
        """
        获取单卡IMEI信息
        """
        pass

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        发送HTTP请求
        """
        url = f"{self.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # 添加认证头
        if headers is None:
            headers = {}
        headers.update(self._get_auth_headers())

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    @abstractmethod
    def _get_auth_headers(self) -> Dict[str, str]:
        """
        获取认证头
        子类需要实现具体的认证方式
        """
        pass


class MockSupplierAPIClient(SupplierAPIClient):
    """
    模拟供应商API客户端 (用于测试)
    """

    def _get_auth_headers(self) -> Dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "X-API-Secret": self.api_secret
        }

    async def get_card_usage(self, iccid: str) -> Dict[str, Any]:
        """模拟获取单卡流量"""
        import random
        return {
            "iccid": iccid,
            "data_used": random.randint(100, 4000),
            "data_total": 5120,
            "sync_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    async def get_batch_usage(self, iccid_list: List[str]) -> List[Dict[str, Any]]:
        """模拟批量获取流量"""
        import random
        return [
            {
                "iccid": iccid,
                "data_used": random.randint(100, 4000),
                "data_total": 5120,
                "sync_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            for iccid in iccid_list
        ]

    async def get_card_lifecycle(self, iccid: str) -> Dict[str, Any]:
        """模拟获取单卡生命周期"""
        from datetime import date, timedelta
        today = date.today()
        return {
            "iccid": iccid,
            "test_expire_date": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
            "silent_expire_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "activated_at": today.strftime("%Y-%m-%d"),
            "expired_at": (today + timedelta(days=365)).strftime("%Y-%m-%d"),
            "status": "activated"
        }

    async def get_batch_lifecycle(self, iccid_list: List[str]) -> List[Dict[str, Any]]:
        """模拟批量获取生命周期"""
        from datetime import date, timedelta
        today = date.today()
        return [
            {
                "iccid": iccid,
                "test_expire_date": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
                "silent_expire_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
                "activated_at": today.strftime("%Y-%m-%d"),
                "expired_at": (today + timedelta(days=365)).strftime("%Y-%m-%d"),
                "status": "activated"
            }
            for iccid in iccid_list
        ]

    async def suspend_card(self, iccid: str, reason: Optional[str] = None, callback_no: Optional[str] = None) -> bool:
        """模拟停卡"""
        return True

    async def resume_card(self, iccid: str, callback_no: Optional[str] = None) -> bool:
        """模拟复机"""
        return True

    async def force_activate_card(self, iccid: str, card_no: Optional[str] = None) -> bool:
        """模拟强制激活"""
        return True

    async def get_card_diagnostics(self, iccid: str) -> Dict[str, Any]:
        """模拟诊断状态"""
        return {
            "iccid": iccid,
            "power_status": "0",
            "power_status_msg": "开机",
            "work_status": "0",
            "work_status_msg": "在线"
        }

    async def get_card_imei_info(self, iccid: str) -> Dict[str, Any]:
        """模拟IMEI查询"""
        return {
            "iccid": iccid,
            "imei": "868327073452754",
            "device_name": "Mock Device",
            "bind_status": "bind_support",
            "lock_triggered": False,
        }


def get_supplier_client(
    supplier_id: int,
    api_url: str,
    api_key: str,
    api_secret: str,
    supplier_code: Optional[str] = None,
    api_config: Optional[Dict[str, Any]] = None,
) -> SupplierAPIClient:
    """
    根据供应商信息获取对应的API客户端。

    supplier_id 对应 suppliers 表的 id；supplier_code 对应业务供应商编码。
    优先按明确供应商编码分发，避免新供应商影响已上线供应商。
    """
    from app.clients.upiot_client import UpiotSupplierClient
    from app.clients.simboss_client import SimbossSupplierClient
    from app.utils.const import decrypt_secret

    normalized_url = (api_url or "").strip()
    normalized_key = decrypt_secret((api_key or "").strip())
    normalized_secret = decrypt_secret((api_secret or "").strip())
    normalized_code = str(supplier_code or "").strip()
    config = api_config or {}

    def normalize_simboss_url(url: str) -> str:
        if not url:
            return settings.simboss_api_url
        lowered = url.lower()
        if "simboss.com/www" in lowered or "simboss.com/2.0" in lowered:
            return settings.simboss_api_url
        return url

    if normalized_code == "002" or str(config.get("platform") or "").lower() == "simboss":
        return SimbossSupplierClient(
            normalize_simboss_url(normalized_url),
            normalized_key or settings.simboss_appid,
            normalized_secret or settings.simboss_app_secret,
        )

    # 根据 api_url 判断供应商平台类型
    if normalized_url and "upiot" in normalized_url.lower():
        return UpiotSupplierClient(normalized_url, normalized_key, normalized_secret)

    if normalized_url and "simboss" in normalized_url.lower():
        return SimbossSupplierClient(
            normalize_simboss_url(normalized_url),
            normalized_key or settings.simboss_appid,
            normalized_secret or settings.simboss_app_secret,
        )

    # 仅开发环境允许兜底 mock，避免生产环境生成随机脏数据
    if settings.app_env != "production":
        return MockSupplierAPIClient(normalized_url, normalized_key, normalized_secret)

    raise ValueError(
        f"供应商 {supplier_id} API 未配置完整，生产环境禁止使用 Mock 客户端 "
        f"(api_url={'yes' if normalized_url else 'no'}, "
        f"api_key={'yes' if normalized_key else 'no'}, "
        f"api_secret={'yes' if normalized_secret else 'no'})"
    )
