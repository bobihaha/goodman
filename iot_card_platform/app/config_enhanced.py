"""
增强的配置管理
"""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets


class Settings(BaseSettings):
    """应用配置类"""
    app_name: str = "IoT Card Platform"
    app_env: str = "development"
    debug: bool = True
    port: int = 8000

    # MySQL 8.4.7 数据库配置
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "iot_card_platform"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    
    @property
    def db_url(self) -> str:
        """构建异步MySQL连接URL"""
        return f"mysql+aiomysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"

    # JWT 配置
    secret_key: str = ""
    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # Redis 配置
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None
    redis_db: int = 0

    # CORS 配置
    allow_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers: List[str] = [
        "Accept", "Accept-Language", "Content-Language", 
        "Content-Type", "Authorization", "X-Requested-With"
    ]

    # 超级登录 Token 有效期 (分钟)
    super_login_expire_minutes: int = 60

    # 安全配置
    password_min_length: int = 8
    max_login_attempts: int = 5
    login_lockout_minutes: int = 15
    rate_limit_per_minute: int = 60

    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    log_max_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    def __post_init__(self):
        """配置后验证"""
        if not self.secret_key:
            if self.app_env == "production":
                raise ValueError("生产环境必须设置JWT secret_key")
            else:
                # 开发环境生成随机密钥
                self.secret_key = secrets.token_urlsafe(32)
        
        # 验证密码长度
        if self.password_min_length < 6:
            raise ValueError("密码最小长度不能少于6位")
        
        # 验证数据库配置
        if not all([self.db_host, self.db_user, self.db_name]):
            raise ValueError("数据库配置不完整")


settings = Settings()