"""
配置管理
"""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field


class Settings(BaseSettings):
    """应用配置类"""
    app_name: str = "IoT Card Platform"
    app_env: str = "development"
    debug: bool = True
    port: int = 8000

    # 数据库配置 - 支持单独字段或完整URL
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "iot_card_platform"
    
    # JWT 配置
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 7
    super_login_expire_minutes: int = 60  # 超级登录有效期

    # Redis 配置
    redis_url: str = "redis://localhost:6379/0"

    # CORS 配置
    allow_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # 批量操作限制
    max_batch_operation_size: int = 10000
    max_export_size: int = 10000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # 忽略额外的环境变量
    )
    
    @property
    def db_url(self) -> str:
        """构建 MySQL 数据库连接 URL"""
        return f"mysql+aiomysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"


settings = Settings()

# 安全检查：生产环境必须配置SECRET_KEY
if settings.app_env == "production" and not settings.secret_key:
    raise ValueError("生产环境必须设置 SECRET_KEY 环境变量")
