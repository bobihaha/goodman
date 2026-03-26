"""
物联网卡管理平台 - 应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from app.api.v1 import auth, sys_user, sys_menu, supplier, package, iot_card, stock, pool, suspend, dashboard, system, sync, permission, project, debug, h5
from app.config import settings
from app.utils.logger import logger
from app.utils.exceptions import BusinessException, business_exception_handler, global_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"✅ 物联网卡管理平台启动 - 环境：{settings.app_env} - 端口：{settings.port}")

    # 启动定时任务调度器
    from app.scheduler import start_scheduler, load_sync_tasks, shutdown_scheduler
    start_scheduler()
    await load_sync_tasks()

    yield

    # 关闭定时任务调度器
    shutdown_scheduler()
    logger.info("✅ 物联网卡管理平台关闭")


app = FastAPI(
    title="物联网卡管理平台",
    description="IoT SIM Card Management Platform API - 三级多租户架构",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
    docs_url=None,  # 禁用默认的 docs
    redoc_url="/redoc"
)

# 自定义 Swagger UI，使用国内 CDN
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - API文档",
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css",
    )

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证管理"])
app.include_router(sys_user.router, prefix="/api/v1/users", tags=["用户管理"])
app.include_router(sys_menu.router, prefix="/api/v1/menus", tags=["菜单管理"])
app.include_router(permission.router, prefix="/api/v1/permissions", tags=["权限管理"])
app.include_router(supplier.router, prefix="/api/v1/suppliers", tags=["供应商管理"])
app.include_router(package.router, prefix="/api/v1/packages", tags=["套餐管理"])
app.include_router(iot_card.router, prefix="/api/v1", tags=["卡片管理"])
app.include_router(stock.router, prefix="/api/v1/stock", tags=["出入库管理"])
app.include_router(pool.router, prefix="/api/v1/pools", tags=["流量池管理"])
app.include_router(suspend.router, prefix="/api/v1/suspend", tags=["停卡策略"])
app.include_router(sync.router, prefix="/api/v1/sync", tags=["数据同步"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["仪表盘"])
app.include_router(system.router, prefix="/api/v1/system", tags=["系统设置"])
app.include_router(project.router, prefix="/api/v1/projects", tags=["项目管理"])
app.include_router(debug.router, prefix="/api/v1", tags=["调试接口"])
app.include_router(h5.router, prefix="/api/v1", tags=["H5自助服务"])

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
