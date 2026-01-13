"""
物联网卡管理平台 - 应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, sys_user, sys_menu
from app.config import settings
from app.utils.logger import logger
from app.utils.exceptions import BusinessException, business_exception_handler, global_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"✅ 物联网卡管理平台启动 - 环境：{settings.app_env} - 端口：{settings.port}")
    yield
    logger.info("✅ 物联网卡管理平台关闭")


app = FastAPI(
    title="物联网卡管理平台",
    description="IoT SIM Card Management Platform API - 三级多租户架构",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证管理"])
app.include_router(sys_user.router, prefix="/api/v1/users", tags=["用户管理"])
app.include_router(sys_menu.router, prefix="/api/v1/menus", tags=["菜单管理"])

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 异常处理
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)


@app.get("/health", tags=["健康检查"])
async def health_check():
    return {"status": "ok", "service": settings.app_name}


@app.get("/", tags=["首页"])
async def root():
    return {"message": "Welcome to IoT Card Management Platform API", "docs": "/docs", "redoc": "/redoc"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", reload=settings.debug, host="0.0.0.0", port=settings.port)
