"""
全局常量
"""
import re
from typing import Any

# ICCID格式验证（19-20位字母或数字）
ICCID_PATTERN = re.compile(r'^[A-Za-z0-9]{19,20}$')

def validate_iccid(iccid: str) -> bool:
    """验证ICCID格式"""
    return bool(ICCID_PATTERN.match(iccid))

# 密码复杂度验证（8-20位，包含大小写字母和数字）
PASSWORD_PATTERN = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,20}$')

def validate_password(password: str) -> bool:
    """验证密码强度"""
    return bool(PASSWORD_PATTERN.match(password))

def sanitize_text(text: str) -> str:
    """清理文本，防止XSS"""
    import html
    if not text:
        return ""
    return html.escape(text.strip())

# 账户名格式验证（4-20位字母数字下划线）
ACCOUNT_PATTERN = re.compile(r'^[a-zA-Z0-9_]{4,20}$')

def validate_account(account: str) -> bool:
    """验证账户名格式"""
    return bool(ACCOUNT_PATTERN.match(account))

# 手机号格式验证
PHONE_PATTERN = re.compile(r'^1[3-9]\d{9}$')

def validate_phone(phone: str) -> bool:
    """验证手机号格式"""
    return bool(PHONE_PATTERN.match(phone)) if phone else True

# 邮箱格式验证
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    return bool(EMAIL_PATTERN.match(email)) if email else True

def encrypt_secret(text: str) -> str:
    """加密敏感信息"""
    from cryptography.fernet import Fernet
    import os
    key = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    f = Fernet(key.encode())
    return f.encrypt(text.encode()).decode()

def decrypt_secret(encrypted: str) -> str:
    """解密敏感信息"""
    from cryptography.fernet import Fernet
    import os
    key = os.getenv("ENCRYPTION_KEY", "")
    if not key:
        return encrypted
    f = Fernet(key.encode())
    return f.decrypt(encrypted.encode()).decode()

# 简单缓存
_cache: dict[str, Any] = {}
_cache_expire: dict[str, float] = {}

def cache_result(ttl_seconds: int = 300):
    """缓存装饰器（5分钟默认）"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            from datetime import datetime
            cache_key = f"{func.__name__}:{str(args[1:] if args else '')}:{str(kwargs)}"
            now = datetime.now().timestamp()
            if cache_key in _cache and now < _cache_expire.get(cache_key, 0):
                return _cache[cache_key]
            result = await func(*args, **kwargs)
            _cache[cache_key] = result
            _cache_expire[cache_key] = now + ttl_seconds
            return result
        return wrapper
    return decorator

# 状态码
SUCCESS_CODE = 200
ERROR_CODE = 400
NOT_FOUND_CODE = 404
UNAUTHORIZED_CODE = 401
FORBIDDEN_CODE = 403
SERVER_ERROR_CODE = 500

# 分页
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# 用户角色
USER_ROLE_ADMIN = "admin"
USER_ROLE_OPERATOR = "operator"
USER_ROLE_USER = "user"

# 卡片状态中文映射
CARD_STATUS_MAP = {
    "inactive": "未激活",
    "active": "已激活",
    "suspended": "已停机",
    "deactivated": "已销户",
    "testing": "测试期"
}

# 运营商中文映射
CARRIER_MAP = {
    "china_mobile": "中国移动",
    "china_unicom": "中国联通",
    "china_telecom": "中国电信"
}
