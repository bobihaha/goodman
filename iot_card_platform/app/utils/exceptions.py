"""
自定义异常 + 全局异常处理器
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from app.utils.logger import logger


class BusinessException(Exception):
    def __init__(self, code: int = 400, msg: str = "业务处理失败"):
        self.code = code
        self.msg = msg
        super().__init__(self.msg)


class UserNotFoundException(BusinessException):
    def __init__(self):
        super().__init__(code=404, msg="用户不存在")


class UserDisabledException(BusinessException):
    def __init__(self):
        super().__init__(code=403, msg="用户已被禁用")


class PasswordErrorException(BusinessException):
    def __init__(self):
        super().__init__(code=400, msg="账号或密码错误")


class AuthException(BusinessException):
    def __init__(self):
        super().__init__(code=401, msg="身份认证失败，请重新登录")


class PermissionDeniedException(BusinessException):
    def __init__(self):
        super().__init__(code=403, msg="权限不足")


async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=200,
        content={"code": exc.code, "msg": exc.msg, "data": None}
    )


async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"全局异常 - 路径：{request.url.path} - 异常：{str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=200,
        content={"code": 500, "msg": "服务器内部错误", "data": None}
    )
