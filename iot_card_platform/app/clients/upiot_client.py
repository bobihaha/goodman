"""
优博讯(upiot)物联卡平台API客户端
API文档版本: V2.47
Host: ec.upiot.net
"""
import hashlib
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

import httpx

from app.clients.supplier_api import SupplierAPIClient

logger = logging.getLogger(__name__)

# upiot 卡状态码 -> 系统状态映射
UPIOT_STATUS_MAP = {
    "00": "activated",      # 正使用
    "10": "test",           # 测试期
    "11": "silent",         # 沉默期
    "02": "suspended",      # 停机
    "03": "pre_cancelled",  # 预销号
    "04": "cancelled",      # 销号
    "12": "suspended",      # 停机保号
    "15": "inventory",      # 库存期
    "99": "unknown",        # 未知
}

# 批量接口单次最大卡数
BATCH_MAX_SIZE = 50


class UpiotSupplierClient(SupplierAPIClient):
    """
    优博讯(upiot)物联卡平台API客户端

    认证方式: URL路径中携带API_KEY + _sign参数(MD5签名)
    API地址格式: {host}/api/v2/{API_KEY}/{endpoint}/?_sign={SIGN}
    """

    def __init__(self, api_url: str, api_key: str, api_secret: str):
        super().__init__(api_url, api_key, api_secret)
        if not self.api_url:
            self.api_url = "http://ec.upiot.net"

    # ========== 签名计算 ==========

    def _md5(self, text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def _calc_get_sign(self, params: Optional[Dict] = None) -> str:
        """GET请求签名: 参数按k=v拼接排序 + API_SECRET -> MD5"""
        if not params:
            return self._md5(self.api_secret)
        sorted_parts = sorted([f"{k}={v}" for k, v in params.items()])
        return self._md5("".join(sorted_parts) + self.api_secret)

    def _calc_post_sign(self, body_str: str) -> str:
        """POST(JSON)签名: 请求体字符串 + API_SECRET -> MD5"""
        return self._md5(body_str + self.api_secret)

    def _get_auth_headers(self) -> Dict[str, str]:
        """upiot不使用Header认证，签名放在URL参数中"""
        return {}

    # ========== 请求封装 ==========

    def _build_url(self, endpoint: str) -> str:
        host = self.api_url.rstrip("/")
        return f"{host}/api/v2/{self.api_key}/{endpoint.strip('/')}/"

    async def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """发送GET请求"""
        url = self._build_url(endpoint)
        sign = self._calc_get_sign(params)
        query = {**(params or {}), "_sign": sign}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params=query)
            resp.raise_for_status()
            try:
                result = resp.json()
            except Exception:
                raise Exception(
                    f"upiot GET error: 响应非JSON (HTTP {resp.status_code}), url={url}, body={resp.text[:200]}"
                )
        if result.get("code") != 200:
            raise Exception(
                f"upiot GET error: code={result.get('code')}, msg={result.get('msg', '')}"
            )
        return result

    async def _post(self, endpoint: str, body: Dict) -> Dict[str, Any]:
        """发送POST(JSON)请求"""
        url = self._build_url(endpoint)
        body_str = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        sign = self._calc_post_sign(body_str)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{url}?_sign={sign}",
                content=body_str.encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            try:
                result = resp.json()
            except Exception:
                raise Exception(
                    f"upiot POST error: 响应非JSON (HTTP {resp.status_code}), url={url}, body={resp.text[:200]}"
                )
        if result.get("code") != 200:
            raise Exception(
                f"upiot POST error: code={result.get('code')}, msg={result.get('msg', '')}"
            )
        return result

    # ========== 辅助方法 ==========

    def _parse_float(self, value) -> float:
        """安全解析流量值(upiot返回字符串如'30.000')"""
        try:
            return float(value) if value else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _map_status(self, account_status: str) -> str:
        """将upiot卡状态码映射为系统状态"""
        return UPIOT_STATUS_MAP.get(str(account_status), "unknown")

    # ========== 核心接口实现 ==========

    async def get_card_usage(self, iccid: str) -> Dict[str, Any]:
        """
        单卡流量查询
        upiot接口: GET /card/{iccid}/
        """
        data = await self._get(f"card/{iccid}")
        card = data.get("data", {})
        return {
            "iccid": card.get("iccid", iccid),
            "data_used": self._parse_float(card.get("data_usage")),
            "data_total": self._parse_float(card.get("data_traffic_amount")),
            "sync_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    async def get_batch_usage(self, iccid_list: List[str]) -> List[Dict[str, Any]]:
        """
        批量流量查询
        upiot接口: POST /card_usage_info/  (每次最多50卡)
        """
        results = []
        for i in range(0, len(iccid_list), BATCH_MAX_SIZE):
            batch = iccid_list[i : i + BATCH_MAX_SIZE]
            data = await self._post("card_usage_info", {"msisdns": batch})
            for row in data.get("data", {}).get("rows", []):
                results.append({
                    "iccid": row.get("iccid", ""),
                    "data_used": self._parse_float(row.get("data_usage")),
                    "data_total": self._parse_float(row.get("data_plan")),
                    "sync_time": row.get("updated_time")
                        or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
        return results

    async def get_card_lifecycle(self, iccid: str) -> Dict[str, Any]:
        """
        单卡生命周期查询
        upiot接口: GET /card/{iccid}/
        """
        data = await self._get(f"card/{iccid}")
        card = data.get("data", {})
        return {
            "iccid": card.get("iccid", iccid),
            "test_expire_date": card.get("test_valid_date", ""),
            "silent_expire_date": card.get("silent_valid_date", ""),
            "activated_at": card.get("active_date", ""),
            "expired_at": card.get("expiry_date", ""),
            "status": self._map_status(card.get("account_status", "99")),
        }

    async def get_batch_lifecycle(self, iccid_list: List[str]) -> List[Dict[str, Any]]:
        """
        批量生命周期查询
        upiot接口: POST /batch/card/info/  (每次最多50卡)
        """
        results = []
        for i in range(0, len(iccid_list), BATCH_MAX_SIZE):
            batch = iccid_list[i : i + BATCH_MAX_SIZE]
            data = await self._post("batch/card/info", {"iccids": batch})
            for row in data.get("data", []):
                results.append({
                    "iccid": row.get("iccid", ""),
                    "test_expire_date": row.get("test_valid_date", ""),
                    "silent_expire_date": row.get("silent_valid_date", ""),
                    "activated_at": row.get("active_date", ""),
                    "expired_at": row.get("expiry_date", ""),
                    "status": self._map_status(row.get("account_status", "99")),
                })
        return results

    async def suspend_card(self, iccid: str, reason: Optional[str] = None) -> bool:
        """
        停卡
        upiot接口: POST /sor/  type=01
        """
        try:
            await self._post("sor", {"number": iccid, "type": "01"})
            return True
        except Exception as e:
            logger.error(f"upiot suspend_card failed: iccid={iccid}, error={e}")
            return False

    async def resume_card(self, iccid: str) -> bool:
        """
        复机
        upiot接口: POST /sor/  type=00
        """
        try:
            await self._post("sor", {"number": iccid, "type": "00"})
            return True
        except Exception as e:
            logger.error(f"upiot resume_card failed: iccid={iccid}, error={e}")
            return False
