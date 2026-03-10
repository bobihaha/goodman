"""
供应商API客户端基类
用于对接不同供应商的API
"""
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import httpx
from datetime import datetime


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
    async def suspend_card(self, iccid: str, reason: Optional[str] = None) -> bool:
        """
        停卡
        """
        pass

    @abstractmethod
    async def resume_card(self, iccid: str) -> bool:
        """
        复机
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

    async def suspend_card(self, iccid: str, reason: Optional[str] = None) -> bool:
        """模拟停卡"""
        return True

    async def resume_card(self, iccid: str) -> bool:
        """模拟复机"""
        return True


def get_supplier_client(supplier_id: int, api_url: str, api_key: str, api_secret: str) -> SupplierAPIClient:
    """
    根据供应商ID获取对应的API客户端

    supplier_id 对应 suppliers 表的 id
    通过 api_url 判断供应商类型:
      - 包含 upiot.net 或 api_config 中标记为 upiot -> UpiotSupplierClient
      - 其他 -> MockSupplierAPIClient (后续可扩展)
    """
    from app.clients.upiot_client import UpiotSupplierClient

    # 根据 api_url 判断供应商平台类型
    if api_url and "upiot" in api_url.lower():
        return UpiotSupplierClient(api_url, api_key, api_secret)

    # 默认返回模拟客户端
    return MockSupplierAPIClient(api_url, api_key, api_secret)







