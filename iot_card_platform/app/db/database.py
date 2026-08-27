"""
数据库连接配置
"""
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.utils.exceptions import BusinessException

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.db_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except BusinessException:
            await session.rollback()
            raise
        except Exception as e:
            logger.exception("Database transaction failed: %s", e)
            await session.rollback()
            raise
