"""
北京时间工具。

数据库 DATETIME 字段按北京时间的无时区值保存；接口返回也按北京时间格式化。
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional


CHINA_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")


def configure_process_timezone() -> None:
    """让进程内 datetime.now()/日志默认使用 Asia/Shanghai。"""
    os.environ.setdefault("TZ", "Asia/Shanghai")
    if hasattr(time, "tzset"):
        time.tzset()


def beijing_now() -> datetime:
    """返回适合写入数据库 DATETIME 的北京时间无时区值。"""
    return datetime.now(CHINA_TZ).replace(tzinfo=None)


def normalize_china_datetime(value: Optional[datetime]) -> Optional[datetime]:
    """将查询入参归一为北京时间无时区值。"""
    if not value:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(CHINA_TZ).replace(tzinfo=None)


def format_china_datetime(value: Optional[datetime]) -> Optional[str]:
    """格式化为北京时间字符串。"""
    value = normalize_china_datetime(value)
    if not value:
        return None
    return value.strftime("%Y-%m-%d %H:%M:%S")
