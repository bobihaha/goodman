"""补量规格常量"""

from datetime import date
from typing import Optional

FLOW_PACKAGE_SIZES_MB = (
    1024,
    2048,
    5120,
    10240,
    20480,
    51200,
    102400,
)

FLOW_PACKAGE_LABELS = {
    1024: "1GB",
    2048: "2GB",
    5120: "5GB",
    10240: "10GB",
    20480: "20GB",
    51200: "50GB",
    102400: "100GB",
}

FLOW_PACKAGE_PRICES = {
    1024: 10,
    2048: 20,
    5120: 50,
    10240: 100,
    20480: 200,
    51200: 500,
    102400: 1000,
}


def is_valid_flow_package_size(value: int) -> bool:
    """检查是否为系统支持的固定补量规格"""
    return value in FLOW_PACKAGE_SIZES_MB


def get_current_flow_cycle_month(today: Optional[date] = None) -> str:
    """获取当前补量生效月份，格式 YYYY-MM。"""
    current = today or date.today()
    return current.strftime("%Y-%m")


def is_flow_cycle_active(cycle_month: Optional[str], today: Optional[date] = None) -> bool:
    """补量仅在购买当月有效。"""
    return bool(cycle_month) and cycle_month == get_current_flow_cycle_month(today)
