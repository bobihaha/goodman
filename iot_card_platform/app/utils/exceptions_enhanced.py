"""
增强的自定义异常 + 全局异常处理器
"""
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from datetime import datetime

from app.utils.logger import logger

# 异常代码常量
class ErrorCodes:
    """错误代码常量"""
    SUCCESS = 0
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    RATE_LIMIT = 429
    INTERNAL_ERROR = 500


class BusinessException(Exception):
    """业务异常基类"""
    def __init__(
        self, 
        code: int = ErrorCodes.BAD_REQUEST, 
        msg: str = "业务处理失败",
        data: Optional[Dict[str, Any]] = None,
        details: Optional[str] = None
    ):
        self.code = code
        self.msg = msg
        self.data = data
        self.details = details
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.msg)


class ValidationException(BusinessException):
    """参数验证异常"""
    def __init__(self, msg: str = "参数验证失败", field: Optional[str] = None):
        super().__init__(code=ErrorCodes.BAD_REQUEST, msg=msg)
        self.field = field


class UserNotFoundException(BusinessException):
    """用户不存在"""
    def __init__(self, msg: str = "用户不存在", user_id: Optional[int] = None):
        super().__init__(code=ErrorCodes.NOT_FOUND, msg=msg)
        self.user_id = user_id


class UserDisabledException(BusinessException):
    """用户已禁用"""
    def __init__(self, msg: str = "用户已被禁用", user_id: Optional[int] = None):
        super().__init__(code=ErrorCodes.FORBIDDEN, msg=msg)
        self.user_id = user_id


class PasswordErrorException(BusinessException):
    """密码错误"""
    def __init__(self, msg: str = "账号或密码错误"):
        super().__init__(code=ErrorCodes.BAD_REQUEST, msg=msg)


class AuthException(BusinessException):
    """认证失败"""
    def __init__(self, msg: str = "身份认证失败，请重新登录"):
        super().__init__(code=ErrorCodes.UNAUTHORIZED, msg=msg)


class PermissionDeniedException(BusinessException):
    """权限不足"""
    def __init__(self, msg: str = "权限不足", permission: Optional[str] = None):
        super().__init__(code=ErrorCodes.FORBIDDEN, msg=msg)
        self.permission = permission


class DataNotFoundException(BusinessException):
    """数据不存在"""
    def __init__(self, msg: str = "数据不存在", resource: Optional[str] = None):
        super().__init__(code=ErrorCodes.NOT_FOUND, msg=msg)
        self.resource = resource


class DuplicateDataException(BusinessException):
    """数据重复"""
    def __init__(self, msg: str = "数据已存在", field: Optional[str] = None):
        super().__init__(code=ErrorCodes.CONFLICT, msg=msg)
        self.field = field


class QuotaExceededException(BusinessException):
    """配额超限"""
    def __init__(self, msg: str = "配额已用完", quota_type: Optional[str] = None):
        super().__init__(code=ErrorCodes.BAD_REQUEST, msg=msg)
        self.quota_type = quota_type


class RateLimitException(BusinessException):
    """请求频率限制"""
    def __init__(self, msg: str = "请求过于频繁，请稍后再试"):
        super().__init__(code=ErrorCodes.RATE_LIMIT, msg=msg)


class DatabaseException(BusinessException):
    """数据库异常"""
    def __init__(self, msg: str = "数据库操作失败", operation: Optional[str] = None):
        super().__init__(code=ErrorCodes.INTERNAL_ERROR, msg=msg)
        self.operation = operation


class ExternalServiceException(BusinessException):
    """外部服务异常"""
    def __init__(self, msg: str = "外部服务调用失败", service: Optional[str] = None):
        super().__init__(code=ErrorCodes.INTERNAL_ERROR, msg=msg)
        self.service = service


def create_error_response(
    code: int, 
    msg: str, 
    data: Any = None,
    details: Optional[str] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """创建标准错误响应"""
    response = {
        "code": code,
        "msg": msg,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    if details:
        response["details"] = details
    
    if request_id:
        response["request_id"] = request_id
    
    return response


async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    """业务异常处理器"""
    # 记录业务异常
    logger.warning(
        f"业务异常 - 路径：{request.url.path} - 异常：{exc.msg} - 代码：{exc.code}",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "code": exc.code,
            "message": exc.msg,
            "details": exc.details,
            "data": exc.data
        }
    )
    
    # 获取请求ID（如果有）
    request_id = getattr(request.state, 'request_id', None)
    
    return JSONResponse(
        status_code=200,  # 业务异常统一返回200
        content=create_error_response(
            code=exc.code,
            msg=exc.msg,
            data=exc.data,
            details=exc.details,
            request_id=request_id
        )
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """参数验证异常处理器"""
    # 格式化验证错误
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"参数验证异常 - 路径：{request.url.path} - 错误：{errors}",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "errors": errors
        }
    )
    
    request_id = getattr(request.state, 'request_id', None)
    
    return JSONResponse(
        status_code=200,
        content=create_error_response(
            code=ErrorCodes.BAD_REQUEST,
            msg="参数验证失败",
            data={"errors": errors},
            request_id=request_id
        )
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    logger.warning(
        f"HTTP异常 - 路径：{request.url.path} - 状态码：{exc.status_code} - 详情：{exc.detail}",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "status_code": exc.status_code,
            "detail": exc.detail
        }
    )
    
    request_id = getattr(request.state, 'request_id', None)
    
    return JSONResponse(
        status_code=200,
        content=create_error_response(
            code=exc.status_code,
            msg=str(exc.detail),
            request_id=request_id
        )
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局异常处理器"""
    # 记录详细错误信息
    error_details = {
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        "traceback": traceback.format_exc()
    }
    
    logger.error(
        f"全局异常 - 路径：{request.url.path} - 异常：{str(exc)}",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc()
        },
        exc_info=True
    )
    
    request_id = getattr(request.state, 'request_id', None)
    
    # 生产环境隐藏详细错误信息
    from app.config_enhanced import settings
    if settings.app_env == "production":
        error_msg = "服务器内部错误"
        details = None
    else:
        error_msg = f"服务器内部错误: {str(exc)}"
        details = error_details["exception_message"]
    
    return JSONResponse(
        status_code=200,
        content=create_error_response(
            code=ErrorCodes.INTERNAL_ERROR,
            msg=error_msg,
            details=details,
            request_id=request_id
        )
    )


class ExceptionHandlerMiddleware:
    """异常处理中间件"""
    
    @staticmethod
    def setup_exception_handlers(app):
        """设置异常处理器"""
        app.add_exception_handler(BusinessException, business_exception_handler)
        app.add_exception_handler(RequestValidationError, validation_exception_handler)
        app.add_exception_handler(StarletteHTTPException, http_exception_handler)
        app.add_exception_handler(Exception, global_exception_handler)