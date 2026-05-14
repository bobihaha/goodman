"""
SIMBOSS API 客户端

供应商编码: 002
API 文档: https://simboss.com/www/service/api
"""
import hashlib
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.clients.supplier_api import SupplierAPIClient

logger = logging.getLogger(__name__)

SIMBOSS_STATUS_MAP = {
    "testing": "testing",
    "inventory": "silent",
    "activation": "activated",
    "deactivation": "suspended",
    "retired": "cancelled",
}

SIMBOSS_DEVICE_STATUS_MAP = {
    "TEST_READY_NAME": "testing",
    "INVENTORY_NAME": "stock",
    "ACTIVATION_READY_NAME": "silent",
    "ACTIVATED_NAME": "activated",
    "DEACTIVATED_NAME": "suspended",
    "RETIRED_NAME": "cancelled",
    "PURGED_NAME": "cancelled",
}

SIMBOSS_BATCH_MAX_SIZE = 100


class SimbossSupplierClient(SupplierAPIClient):
    """SIMBOSS 物联网卡平台 API 客户端。"""

    def __init__(self, api_url: str, appid: str, app_secret: str):
        super().__init__(api_url or "https://api.simboss.com", appid, app_secret)
        self.last_sor_result: Optional[Dict[str, Any]] = None
        self.last_force_activate_result: Optional[Dict[str, Any]] = None

    @property
    def appid(self) -> str:
        return self.api_key

    @property
    def app_secret(self) -> str:
        return self.api_secret

    def _get_auth_headers(self) -> Dict[str, str]:
        return {}

    def _build_url(self, endpoint: str) -> str:
        host = self.api_url.rstrip("/")
        return f"{host}/2.0/{endpoint.strip('/')}"

    def _calc_sign(self, params: Dict[str, Any]) -> str:
        sign_parts = []
        for key in sorted(params):
            value = params[key]
            if value is None:
                continue
            sign_parts.append(f"{key}={value}")
        raw = "&".join(sign_parts) + self.app_secret
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def _post(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "appid": self.appid,
            "timestamp": str(int(time.time() * 1000)),
            **{key: value for key, value in params.items() if value is not None},
        }
        payload["sign"] = self._calc_sign(payload)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self._build_url(endpoint),
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8;"},
            )
            response.raise_for_status()
            try:
                result = response.json()
            except Exception as exc:
                raise Exception(
                    f"simboss POST error: 响应非JSON (HTTP {response.status_code}), "
                    f"endpoint={endpoint}, body={response.text[:200]}"
                ) from exc

        if str(result.get("code")) != "0":
            raise Exception(
                f"simboss POST error: code={result.get('code')}, "
                f"message={result.get('message', '')}, detail={result.get('detail', '')}"
            )
        return result

    def _parse_float(self, value: Any) -> float:
        try:
            return float(value) if value not in (None, "") else 0.0
        except (TypeError, ValueError):
            return 0.0

    def _parse_date(self, value: Any) -> str:
        if not value:
            return ""
        text = str(value).strip()
        if not text or text.lower() in {"false", "null", "none"}:
            return ""
        return text[:10]

    def _map_status(self, payload: Dict[str, Any]) -> str:
        device_status = str(payload.get("deviceStatus") or "").strip()
        if device_status in {"ACTIVATED_NAME", "DEACTIVATED_NAME", "RETIRED_NAME", "PURGED_NAME"}:
            return SIMBOSS_DEVICE_STATUS_MAP.get(device_status, "unknown")
        status = str(payload.get("status") or "").strip()
        if status in SIMBOSS_STATUS_MAP:
            return SIMBOSS_STATUS_MAP[status]
        return SIMBOSS_DEVICE_STATUS_MAP.get(device_status, "unknown")

    async def _get_device_status(self, iccid: str) -> str:
        result = await self._post("device/detail", {"iccid": iccid})
        payload = result.get("data") or {}
        return str(payload.get("deviceStatus") or "").strip()

    def _normalize_usage(self, payload: Dict[str, Any], iccid: str) -> Dict[str, Any]:
        month_usage = self._parse_float(payload.get("dataUsage"))
        package_usage = self._parse_float(payload.get("usedDataVolume"))
        if package_usage <= 0 and month_usage > 0:
            package_usage = month_usage
        return {
            "iccid": payload.get("iccid") or iccid,
            "data_used": package_usage,
            "data_used_month": month_usage,
            "data_used_scope": "cycle",
            "data_total": self._parse_float(payload.get("totalDataVolume")),
            "sync_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _normalize_lifecycle(self, payload: Dict[str, Any], iccid: str) -> Dict[str, Any]:
        return {
            "iccid": payload.get("iccid") or iccid,
            "test_expire_date": self._parse_date(payload.get("testingExpireDate")),
            "silent_expire_date": "",
            "activated_at": self._parse_date(payload.get("startDate")),
            "expired_at": self._parse_date(
                payload.get("ratePlanExpirationDate") or payload.get("expireDate")
            ),
            "status": self._map_status(payload),
        }

    async def get_card_usage(self, iccid: str) -> Dict[str, Any]:
        result = await self._post("device/detail", {"iccid": iccid})
        return self._normalize_usage(result.get("data") or {}, iccid)

    async def get_batch_usage(self, iccid_list: List[str]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for index in range(0, len(iccid_list), SIMBOSS_BATCH_MAX_SIZE):
            batch = iccid_list[index:index + SIMBOSS_BATCH_MAX_SIZE]
            result = await self._post("device/detail/batch", {"iccids": ",".join(batch)})
            rows = result.get("data") or []
            for row in rows:
                results.append(self._normalize_usage(row, row.get("iccid") or ""))
        return results

    async def get_card_lifecycle(self, iccid: str) -> Dict[str, Any]:
        result = await self._post("device/detail", {"iccid": iccid})
        return self._normalize_lifecycle(result.get("data") or {}, iccid)

    async def get_batch_lifecycle(self, iccid_list: List[str]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for index in range(0, len(iccid_list), SIMBOSS_BATCH_MAX_SIZE):
            batch = iccid_list[index:index + SIMBOSS_BATCH_MAX_SIZE]
            result = await self._post("device/detail/batch", {"iccids": ",".join(batch)})
            rows = result.get("data") or []
            for row in rows:
                results.append(self._normalize_lifecycle(row, row.get("iccid") or ""))
        return results

    async def suspend_card(self, iccid: str, reason: Optional[str] = None, callback_no: Optional[str] = None) -> bool:
        self.last_sor_result = None
        try:
            await self._post("device/modifyDeviceStatus", {
                "iccid": iccid,
                "status": "DEACTIVATED_NAME",
            })
            observed_status = await self._get_device_status(iccid)
            if observed_status != "DEACTIVATED_NAME":
                self.last_sor_result = {
                    "submitted": False,
                    "expected_device_status": "DEACTIVATED_NAME",
                    "observed_device_status": observed_status,
                    "supplier_msg": "SIMBOSS返回成功，但供应商侧网络状态未变为关停",
                }
                return False
            self.last_sor_result = {
                "submitted": True,
                "observed_device_status": observed_status,
                "reconciled_status": "suspended",
            }
            return True
        except Exception as exc:
            self.last_sor_result = {"submitted": False, "error": str(exc)}
            logger.error("simboss suspend_card failed: iccid=%s error=%s", iccid, exc)
            return False

    async def resume_card(self, iccid: str, callback_no: Optional[str] = None) -> bool:
        self.last_sor_result = None
        try:
            await self._post("device/modifyDeviceStatus", {
                "iccid": iccid,
                "status": "ACTIVATED_NAME",
            })
            observed_status = await self._get_device_status(iccid)
            if observed_status != "ACTIVATED_NAME":
                self.last_sor_result = {
                    "submitted": False,
                    "expected_device_status": "ACTIVATED_NAME",
                    "observed_device_status": observed_status,
                    "supplier_msg": "SIMBOSS返回成功，但供应商侧网络状态未恢复",
                }
                return False
            self.last_sor_result = {
                "submitted": True,
                "observed_device_status": observed_status,
                "reconciled_status": "activated",
            }
            return True
        except Exception as exc:
            self.last_sor_result = {"submitted": False, "error": str(exc)}
            logger.error("simboss resume_card failed: iccid=%s error=%s", iccid, exc)
            return False

    async def force_activate_card(self, iccid: str, card_no: Optional[str] = None) -> bool:
        self.last_force_activate_result = None
        try:
            await self._post("device/activate", {"iccid": card_no or iccid})
            self.last_force_activate_result = {"submitted": True}
            return True
        except Exception as exc:
            self.last_force_activate_result = {"submitted": False, "error": str(exc)}
            logger.error("simboss force_activate failed: iccid=%s error=%s", iccid, exc)
            return False

    async def get_card_diagnostics(self, iccid: str) -> Dict[str, Any]:
        result = await self._post("device/detail", {"iccid": iccid})
        payload = result.get("data") or {}
        device_status = str(payload.get("deviceStatus") or "").strip()
        mapped_status = self._map_status(payload)
        return {
            "iccid": payload.get("iccid") or iccid,
            "power_status": None,
            "power_status_msg": "未知",
            "work_status": device_status or None,
            "work_status_msg": mapped_status,
        }

    async def get_card_imei_info(self, iccid: str) -> Dict[str, Any]:
        result = {
            "iccid": iccid,
            "imei": None,
            "device_name": None,
            "bind_status": None,
            "lock_triggered": None,
            "detection_status": "unknown",
            "detection_message": "",
        }

        try:
            detail = await self._post("device/detail", {"iccid": iccid})
            detail_payload = detail.get("data") or {}
            imei_status = str(detail_payload.get("imeiStatus") or "").strip()
            result["bind_status"] = imei_status or None
            if imei_status == "SPLIT":
                result["lock_triggered"] = True
                result["detection_status"] = "detected"
                result["detection_message"] = "机卡分离"
            elif imei_status == "NORMAL":
                result["lock_triggered"] = False
                result["detection_status"] = "clear"
                result["detection_message"] = "机卡绑定正常"
            elif imei_status in {"NOT_SET", "NOT_BIND"}:
                result["detection_status"] = "unsupported" if imei_status == "NOT_SET" else "pending"
                result["detection_message"] = imei_status
        except Exception as exc:
            logger.warning("simboss get_card_imei_info detail fallback: iccid=%s error=%s", iccid, exc)

        try:
            num_result = await self._post("device/queryNum", {"iccids": iccid})
            rows = num_result.get("data") or []
            row = next((item for item in rows if str(item.get("iccid") or "") == iccid), None)
            if row:
                result["imei"] = (row.get("imei") or "").strip() or None
        except Exception as exc:
            logger.warning("simboss get_card_imei_info queryNum fallback: iccid=%s error=%s", iccid, exc)

        return result
