"""
优博讯(upiot)物联卡平台API客户端
API文档版本: V2.47
Host: ec.upiot.net
"""
import hashlib
import json
import logging
import re
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

import httpx

from app.clients.supplier_api import SupplierAPIClient

logger = logging.getLogger(__name__)

# upiot 卡状态码 -> 系统状态映射
UPIOT_STATUS_MAP = {
    "00": "activated",      # 正使用
    "10": "testing",        # 测试期
    "11": "silent",         # 沉默期
    "02": "suspended",      # 停机
    "03": "cancelled",      # 预销号
    "04": "cancelled",      # 销号
    "12": "suspended",      # 停机保号
    "15": "stock",          # 库存期
    "99": "unknown",        # 未知
}

UPIOT_POWER_STATUS_MAP = {
    "0": "开机",
    "1": "关机",
    "2": "未知",
    "3": "未知",
}

UPIOT_WORK_STATUS_MAP = {
    "0": "在线",
    "1": "离线",
    "2": "未知",
    "3": "未知",
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
        self.last_sor_result: Optional[Dict[str, Any]] = None
        self.last_force_activate_result: Optional[Dict[str, Any]] = None

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

    async def _get_with_business_code(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        allowed_codes: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """发送允许特定业务码的GET请求"""
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
        accepted_codes = {200, *(allowed_codes or [])}
        if result.get("code") not in accepted_codes:
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

    def _map_power_status_text(self, value: Any) -> str:
        return UPIOT_POWER_STATUS_MAP.get(str(value), "未知")

    def _map_work_status_text(self, value: Any) -> str:
        return UPIOT_WORK_STATUS_MAP.get(str(value), "未知")

    def _parse_supplier_error(self, error: Exception) -> Dict[str, Optional[str]]:
        message = str(error)
        match = re.search(r"code=([^,]+), msg=(.+)$", message)
        if not match:
            return {"code": None, "msg": message}
        return {
            "code": match.group(1).strip(),
            "msg": match.group(2).strip(),
        }

    def _resolve_usage_payload(self, card: Dict[str, Any]) -> Dict[str, Any]:
        monthly_used = self._parse_float(card.get("data_usage"))
        cycle_used = self._parse_float(card.get("cycle_data_usage"))
        is_accumulated = card.get("accumulated") is True and card.get("cycle_data_usage") not in (None, "")
        if is_accumulated:
            return {
                "data_used": cycle_used,
                "data_used_month": monthly_used,
                "data_used_scope": "cycle",
            }
        return {
            "data_used": monthly_used,
            "data_used_month": monthly_used,
            "data_used_scope": "month",
        }

    def _looks_like_yearly_usage_row(self, row: Dict[str, Any]) -> bool:
        product_code = str(row.get("bg_code") or row.get("code") or "").upper()
        if product_code.endswith("Y") or "Y" in product_code:
            return True
        expiry_date = row.get("expiry_date")
        valid_date = row.get("valid_date") or row.get("active_date")
        if not expiry_date or not valid_date:
            return False
        try:
            expiry = datetime.strptime(str(expiry_date), "%Y-%m-%d").date()
            valid = datetime.strptime(str(valid_date), "%Y-%m-%d").date()
        except ValueError:
            return False
        return (expiry - valid).days >= 300

    # ========== 核心接口实现 ==========

    async def get_card_usage(self, iccid: str) -> Dict[str, Any]:
        """
        单卡流量查询
        upiot接口: GET /card/{iccid}/
        """
        data = await self._get(f"card/{iccid}")
        card = data.get("data", {})
        usage_payload = self._resolve_usage_payload(card)
        return {
            "iccid": card.get("iccid", iccid),
            **usage_payload,
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
                iccid = row.get("iccid", "")
                if iccid and self._looks_like_yearly_usage_row(row):
                    try:
                        results.append(await self.get_card_usage(iccid))
                        continue
                    except Exception as exc:
                        logger.warning("年包周期累计用量补查失败: iccid=%s, error=%s", iccid, exc)
                usage_payload = self._resolve_usage_payload(row)
                results.append({
                    "iccid": iccid,
                    **usage_payload,
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

    async def suspend_card(self, iccid: str, reason: Optional[str] = None, callback_no: Optional[str] = None) -> bool:
        """
        停卡
        upiot接口: POST /sor/  type=01
        """
        self.last_sor_result = None
        try:
            payload = {"number": iccid, "type": "01"}
            if callback_no:
                payload["callback_no"] = callback_no
            await self._post("sor", payload)
            self.last_sor_result = {"submitted": True}
            return True
        except Exception as e:
            error_meta = self._parse_supplier_error(e)
            supplier_msg = error_meta.get("msg") or ""
            if error_meta.get("code") == "535" and "停机" in supplier_msg and "正使用" not in supplier_msg:
                self.last_sor_result = {
                    "submitted": True,
                    "idempotent": True,
                    "supplier_code": error_meta.get("code"),
                    "supplier_msg": supplier_msg,
                    "reconciled_status": "suspended",
                }
                logger.warning(
                    "upiot suspend_card already suspended, reconcile locally: iccid=%s, msg=%s",
                    iccid,
                    supplier_msg,
                )
                return True
            self.last_sor_result = {
                "submitted": False,
                "supplier_code": error_meta.get("code"),
                "supplier_msg": supplier_msg,
                "error": str(e),
            }
            logger.error(f"upiot suspend_card failed: iccid={iccid}, error={e}")
            return False

    async def resume_card(self, iccid: str, callback_no: Optional[str] = None) -> bool:
        """
        复机
        upiot接口: POST /sor/  type=00
        """
        self.last_sor_result = None
        try:
            payload = {"number": iccid, "type": "00"}
            if callback_no:
                payload["callback_no"] = callback_no
            await self._post("sor", payload)
            self.last_sor_result = {"submitted": True}
            return True
        except Exception as e:
            error_meta = self._parse_supplier_error(e)
            supplier_msg = error_meta.get("msg") or ""
            if error_meta.get("code") == "535" and "正使用" in supplier_msg:
                self.last_sor_result = {
                    "submitted": True,
                    "idempotent": True,
                    "supplier_code": error_meta.get("code"),
                    "supplier_msg": supplier_msg,
                    "reconciled_status": "activated",
                }
                logger.warning(
                    "upiot resume_card already active, reconcile locally: iccid=%s, msg=%s",
                    iccid,
                    supplier_msg,
                )
                return True
            self.last_sor_result = {
                "submitted": False,
                "supplier_code": error_meta.get("code"),
                "supplier_msg": supplier_msg,
                "error": str(e),
            }
            logger.error(f"upiot resume_card failed: iccid={iccid}, error={e}")
            return False

    async def force_activate_card(self, iccid: str, card_no: Optional[str] = None) -> bool:
        """
        强制激活

        upiot接口:
        - POST /card_status_change/ oper_type=1|2
        - GET /card_status_change_result/?task_id=xxx

        口径:
        - 测试期 -> 正使用: oper_type=2
        - 沉默期/库存期 -> 正使用: oper_type=1
        """
        self.last_force_activate_result = None
        try:
            lifecycle = await self.get_card_lifecycle(iccid)
            current_status = str(lifecycle.get("status") or "").strip()
            if current_status == "activated":
                self.last_force_activate_result = {
                    "submitted": True,
                    "idempotent": True,
                    "current_status": current_status,
                    "reconciled_status": "activated",
                    "supplier_msg": "供应商侧已是正使用状态，已按激活纠正本地状态",
                }
                return True
            oper_type = 2 if current_status == "testing" else 1
            request_card_no = (card_no or iccid or "").strip()

            payload = {"cards_no": [request_card_no], "oper_type": oper_type}
            response = await self._post("card_status_change", payload)
            task_id = response.get("data")
            self.last_force_activate_result = {
                "submitted": True,
                "task_id": task_id,
                "oper_type": oper_type,
                "current_status": current_status,
                "request_card_no": request_card_no,
            }

            if task_id:
                for _ in range(3):
                    await asyncio.sleep(2)
                    result = await self._get("card_status_change_result", {"task_id": task_id})
                    rows = result.get("data") or []
                    row = next(
                        (
                            item for item in rows
                            if str(item.get("iccid") or "") == iccid
                            or str(item.get("msisdn") or "") == iccid
                            or str(item.get("imsi") or "") == iccid
                        ),
                        None
                    )
                    if not row:
                        continue
                    result_text = str(row.get("result") or "")
                    self.last_force_activate_result["result"] = result_text
                    if "成功" in result_text:
                        return True
                    if "失败" in result_text:
                        self.last_force_activate_result.update({
                            "submitted": False,
                            "error": result_text,
                        })
                        return False

            return True
        except Exception as e:
            error_meta = self._parse_supplier_error(e)
            supplier_msg = error_meta.get("msg") or ""
            if "正使用" in supplier_msg or "已使用" in supplier_msg:
                self.last_force_activate_result = {
                    "submitted": True,
                    "idempotent": True,
                    "supplier_code": error_meta.get("code"),
                    "supplier_msg": supplier_msg,
                    "reconciled_status": "activated",
                }
                logger.warning(
                    "upiot force_activate already active, reconcile locally: iccid=%s, msg=%s",
                    iccid,
                    supplier_msg,
                )
                return True
            self.last_force_activate_result = {
                "submitted": False,
                "supplier_code": error_meta.get("code"),
                "supplier_msg": supplier_msg,
                "error": str(e),
            }
            logger.error("upiot force_activate failed: iccid=%s, error=%s", iccid, e)
            return False

    async def get_card_diagnostics(self, iccid: str) -> Dict[str, Any]:
        """
        单卡诊断查询
        upiot接口: GET /card/{iccid}/status/

        说明:
        - power_status: 设备开机状态，0=开机 1=关机
        - gprs_status: 设备工作状态，0=在线 1=离线
        """
        data = await self._get(f"card/{iccid}/status")
        card = data.get("data", {})
        power_status = card.get("power_status")
        work_status = card.get("gprs_status")
        power_status_msg = card.get("power_status_msg") or self._map_power_status_text(power_status)
        work_status_msg = card.get("gprs_status_msg") or self._map_work_status_text(work_status)

        return {
            "iccid": iccid,
            "power_status": str(power_status) if power_status is not None else None,
            "power_status_msg": power_status_msg,
            "work_status": str(work_status) if work_status is not None else None,
            "work_status_msg": work_status_msg,
        }

    async def get_card_imei_info(self, iccid: str) -> Dict[str, Any]:
        """
        获取单卡实时IMEI及绑定状态

        upiot接口:
        - GET /card/{iccid}/imei/device/
        - GET /card/{iccid}/imei/lock/status/
        - GET /card/{iccid}/stop_reason/
        """
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
            device_data = await self._get(f"card/{iccid}/imei/device")
            imei_payload = device_data.get("data", {}) or {}
            result["imei"] = (imei_payload.get("imei") or "").strip() or None
            result["device_name"] = (imei_payload.get("device") or "").strip() or None
        except Exception as exc:
            error_info = self._parse_supplier_error(exc)
            error_msg = (error_info.get("msg") or "").strip()
            if error_msg:
                result["detection_message"] = error_msg
                if "暂不支持" in error_msg or "未开放" in error_msg or "未开通" in error_msg:
                    result["detection_status"] = "unsupported"
            logger.warning("upiot get_card_imei_info device fallback: iccid=%s error=%s", iccid, exc)

        try:
            lock_data = await self._get(f"card/{iccid}/imei/lock/status")
            lock_payload = lock_data.get("data", {}) or {}
            triggered = lock_payload.get("triggered")
            result["bind_status"] = lock_payload.get("status")
            result["lock_triggered"] = triggered in {True, "true", "True", 1, "1", "是"}
        except Exception as exc:
            logger.warning("upiot get_card_imei_info lock status fallback: iccid=%s error=%s", iccid, exc)

        try:
            stop_reason = await self._get_with_business_code(
                f"card/{iccid}/stop_reason",
                allowed_codes=[300]
            )
            result["separation_stop_msg"] = stop_reason.get("msg")
            result["separation_stop_code"] = stop_reason.get("code")
            stop_msg = (stop_reason.get("msg") or "").strip()
            if stop_msg == "是":
                result["detection_status"] = "detected"
                result["detection_message"] = "机卡分离停机"
            elif stop_msg == "否":
                result["detection_status"] = "clear"
                result["detection_message"] = "未机卡分离"
            elif stop_msg:
                result["detection_status"] = "pending"
                result["detection_message"] = stop_msg
        except Exception as exc:
            error_info = self._parse_supplier_error(exc)
            error_msg = (error_info.get("msg") or "").strip()
            if error_msg and result["detection_status"] == "unknown":
                result["detection_message"] = error_msg
                if "暂不支持" in error_msg or "未开放" in error_msg or "未开通" in error_msg:
                    result["detection_status"] = "unsupported"
            logger.warning("upiot get_card_imei_info stop_reason fallback: iccid=%s error=%s", iccid, exc)

        return result
