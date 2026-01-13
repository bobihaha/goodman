"""
增强的物联网卡管理平台 - 应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import uuid
import logging

from app.api.v1 import auth, sys_user, sys_menu
from app.config_enhanced import settings
from app.utils.logger import logger
from app.utils.exceptions_enhanced import ExceptionHandlerMiddleware
from app.db.database_enhanced import check_db_connection, close_db_connections

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 - 增强版本"""
    # 启动时执行
    logger.info(f"🚀 物联网卡管理平台启动中...")
    logger.info(f"📍 环境：{settings.app_env}")
    logger.info(f"🌐 端口：{settings.port}")
    logger.info(f"🔧 调试模式：{settings.debug}")
    
    # 检查数据库连接
    if await check_db_connection():
        logger.info("✅ 数据库连接正常")
    else:
        logger.error("❌ 数据库连接失败")
        raise Exception("数据库连接失败")
    
    logger.info("✅ 物联网卡管理平台启动完成")
    
    yield
    
    # 关闭时执行
    logger.info("🔄 物联网卡管理平台关闭中...")
    await close_db_connections()
    logger.info("✅ 物联网卡管理平台已关闭")


app = FastAPI(
    title="物联网卡管理平台",
    description="""
    ## IoT SIM Card Management Platform API
    
    ### 用户层级架构
    - **Level 1: 超级管理员** - 管理所有用户和系统配置
    - **Level 2: 用户** - 管理子用户和卡片业务
    - **Level 3: 子用户** - 使用卡片功能，受限操作
    
    ### 认证方式
    - **Bearer Token (JWT)** - 标准认证方式
    - **超级登录** - 管理员可以切换到下级用户身份
    
    ### 安全特性
    - JWT令牌认证
    - 登录频率限制
    - 权限分级控制
    - 操作日志记录
    - CORS跨域保护
    """,
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None
)


# ================== 中间件配置 ==================

# 请求ID和日志中间件
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """请求日志中间件"""
    # 生成请求ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # 记录请求开始时间
    start_time = time.time()
    
    # 记录请求信息
    logger.info(
        f"📥 请求开始 - ID: {request_id} - {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": str(request.url.path),
            "query_params": str(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent")
        }
    )
    
    try:
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录响应信息
        logger.info(
            f"📤 请求完成 - ID: {request_id} - 状态码: {response.status_code} - 耗时: {process_time:.3f}s",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": process_time
            }
        )
        
        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time, 3))
        
        return response
        
    except Exception as e:
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录错误信息
        logger.error(
            f"❌ 请求异常 - ID: {request_id} - 错误: {str(e)} - 耗时: {process_time:.3f}s",
            extra={
                "request_id": request_id,
                "error": str(e),
                "process_time": process_time
            },
            exc_info=True
        )
        
        # 重新抛出异常，让全局异常处理器处理
        raise


# 安全头部中间件
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """安全头部中间件"""
    response = await call_next(request)
    
    # 添加安全头部
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    if settings.app_env == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


# 信任主机中间件（生产环境）
if settings.app_env == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # 在生产环境中应该配置具体的主机名
    )


# CORS 跨域配置 - 增强版本
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=settings.allow_methods,
    allow_headers=settings.allow_headers,
    expose_headers=["X-Request-ID", "X-Process-Time"]
)


# ================== 异常处理配置 ==================
ExceptionHandlerMiddleware.setup_exception_handlers(app)


# ================== 注册路由 ==================
# 认证模块
app.include_router(
    auth.router, 
    prefix="/api/v1/auth", 
    tags=["认证管理"],
    responses={404: {"description": "Not found"}}
)

# 用户管理
app.include_router(
    sys_user.router, 
    prefix="/api/v1/users", 
    tags=["用户管理"],
    responses={404: {"description": "Not found"}}
)

# 菜单管理
app.include_router(
    sys_menu.router, 
    prefix="/api/v1/menus", 
    tags=["菜单管理"],
    responses={404: {"description": "Not found"}}
)


# ================== 健康检查 ==================
@app.get("/health", tags=["健康检查"], summary="健康检查")
async def health_check():
    """健康检查接口"""
    db_status = await check_db_connection()
    
    return {
        "status": "ok" if db_status else "error",
        "service": settings.app_name,
        "version": "1.0.0",
        "environment": settings.app_env,
        "database": "connected" if db_status else "disconnected",
        "timestamp": time.time()
    }


@app.get("/", tags=["首页"], summary="API首页")
async def root():
    """API 首页"""
    return {
        "message": "Welcome to IoT Card Management Platform API",
        "version": "1.0.0",
        "environment": settings.app_env,
        "docs": "/docs" if settings.debug else "Documentation not available in production",
        "health": "/health"
    }


# ================== 开发工具 ==================
if settings.debug:
    @app.get("/debug/config", tags=["开发工具"], summary="查看配置信息")
    async def debug_config():
        """查看当前配置（仅开发环境）"""
        return {
            "app_name": settings.app_name,
            "app_env": settings.app_env,
            "debug": settings.debug,
            "port": settings.port,
            "db_host": settings.db_host,
            "db_port": settings.db_port,
            "db_name": settings.db_name,
            "cors_origins": settings.allow_origins,
            "token_expire_minutes": settings.access_token_expire_minutes,
            "password_min_length": settings.password_min_length,
            "max_login_attempts": settings.max_login_attempts
        }


if __name__ == "__main__":
    import uvicorn
    
    # 启动配置
    uvicorn_config = {
        "app": "app.main_enhanced:app",
        "reload": settings.debug,
        "host": "0.0.0.0",
        "port": settings.port,
        "log_level": settings.log_level.lower(),
        "access_log": True
    }
    
    # 生产环境额外配置
    if settings.app_env == "production":
        uvicorn_config.update({
            "workers": 4,
            "limit_concurrency": 1000,
            "limit_max_requests": 1000,
            "timeout_keep_alive": 5
        })
    
    uvicorn.run(**uvicorn_config)