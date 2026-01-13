"""
全局常量
"""

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
