"""
增强的数据库连接配置
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import logging

from app.config_enhanced import settings

logger = logging.getLogger(__name__)

# 创建异步引擎
engine = create_async_engine(
    settings.db_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    poolclass=NullPool if settings.app_env == "testing" else None,
    connect_args={
        "charset": "utf8mb4",
        "use_unicode": True,
    }
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    增强版本：更好的异常处理和连接管理
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"数据库事务回滚: {str(e)}")
        raise e
    finally:
        await session.close()


async def get_db_no_commit() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（不自动提交）
    用于需要手动控制事务的场景
    """
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()


async def check_db_connection() -> bool:
    """检查数据库连接"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"数据库连接检查失败: {str(e)}")
        return False


async def close_db_connections():
    """关闭所有数据库连接"""
    await engine.dispose()