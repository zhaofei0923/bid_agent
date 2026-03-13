"""Application configuration via Pydantic Settings.

All environment variables are loaded from .env file or system environment.
"""

import json
from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    API_V1_PREFIX: str = "/v1"
    CORS_ORIGINS: str = "http://localhost:3000"
    APP_NAME: str = "BidAgent V2"
    APP_VERSION: str = "2.0.0"
    FRONTEND_URL: str = "https://bid.easudata.com"

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/bid_agent"
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # ── Redis ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ──────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24h
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── LLM ──────────────────────────────────────────────────────
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com"
    LLM_MODEL: str = "deepseek-chat"
    LLM_REASONING_MODEL: str = "deepseek-reasoner"
    LLM_MAX_RETRIES: int = 1
    LLM_TIMEOUT: int = 180

    # ── Embedding ────────────────────────────────────────────────
    EMBEDDING_PROVIDER: str = "hunyuan"  # hunyuan | zhipu
    EMBEDDING_DIMENSION: int = 1024
    EMBEDDING_FALLBACK_ENABLED: bool = True
    HUNYUAN_SECRET_ID: str = ""
    HUNYUAN_SECRET_KEY: str = ""
    ZHIPU_API_KEY: str = ""

    # Primary embedding endpoint (腾讯混元)
    EMBEDDING_API_URL: str = "https://api.hunyuan.cloud.tencent.com/v1/embeddings"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = "hunyuan-embedding"

    # Fallback embedding endpoint (智谱)
    EMBEDDING_FALLBACK_URL: str = "https://open.bigmodel.cn/api/paas/v4/embeddings"
    EMBEDDING_FALLBACK_KEY: str = ""
    EMBEDDING_FALLBACK_MODEL: str = "embedding-3"

    # ── Tencent Cloud OCR (扫描件 PDF 识别) ────────────────────
    TENCENT_OCR_ENABLED: bool = False  # 开关: True 时启用扫描件 OCR
    TENCENT_OCR_SECRET_ID: str = ""  # 可复用 HUNYUAN_SECRET_ID
    TENCENT_OCR_SECRET_KEY: str = ""  # 可复用 HUNYUAN_SECRET_KEY
    TENCENT_OCR_REGION: str = "ap-guangzhou"

    # ── Celery ───────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_URL: str = "redis://localhost:6379/2"

    # ── Fetcher ───────────────────────────────────────────────────
    FETCHER_REQUEST_DELAY: float = 2.0
    # Proxy for fetchers (optional, format: http://host:port)
    FETCHER_PROXY: str = ""

    # ── Upload ───────────────────────────────────────────────────
    UPLOAD_DIR: str = "data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # ── Email (腾讯云 SES SMTP) ─────────────────────────────────
    SMTP_HOST: str = "smtp.qcloudmail.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""  # 腾讯云 SES 发件人邮箱
    SMTP_PASSWORD: str = ""  # 腾讯云 SES SMTP 密钥
    EMAIL_FROM_NAME: str = "BidAgent"
    EMAIL_ENABLED: bool = False  # 开关: False 时只打印验证码到日志

    # ── Redis Key Namespace (防止多项目共用 Redis 时 key 冲突) ───
    REDIS_KEY_PREFIX: str = "bidagent"

    # ── Verification Code ───────────────────────────────────────
    VERIFY_CODE_TTL: int = 600  # 验证码有效期 (秒)
    VERIFY_CODE_RATE_LIMIT: int = 60  # 重发冷却时间 (秒)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> str:
        """Accept any format and normalize to comma-separated string."""
        if isinstance(v, list):
            return ",".join(v)
        if isinstance(v, str):
            v = v.strip()
            # Handle JSON array format: '["url1","url2"]'
            if v.startswith("["):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return ",".join(str(i) for i in parsed)
                except (json.JSONDecodeError, ValueError):
                    pass
            return v
        return str(v)

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton."""
    return settings
