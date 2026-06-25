import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict  # pyright: ignore[reportMissingImports]
from pydantic import Field  # pyright: ignore[reportMissingImports]


def resolve_env_file() -> str | None:
    """解析应加载的 .env 文件（支持 ENV_FILE 显式覆盖）。

    约定：
    - 本地开发默认使用 backend/.env.dev（如果存在）；
    - 生产与 CI 建议通过环境变量/Secrets 注入，不依赖仓库内 env 文件。
    """
    explicit = os.getenv("ENV_FILE")
    if explicit:
        return explicit

    for name in (".env.dev", ".env"):
        if Path(name).exists():
            return name

    return None


class Settings(BaseSettings):
    database_url: str = Field(env="DATABASE_URL")
    jwt_secret: str = Field(env="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    app_env: str = Field(default="local", env="APP_ENV")
    allow_insecure_http: bool = Field(default=True, env="ALLOW_INSECURE_HTTP")
    csrf_trusted_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,https://localhost:5173,https://127.0.0.1:5173,https://localhost",
        env="CSRF_TRUSTED_ORIGINS",
    )
    cors_origins: str = Field(
        default="https://localhost",
        env="CORS_ORIGINS",
    )

    password_min_length: int = Field(default=8, env="PASSWORD_MIN_LENGTH")
    password_max_length: int = Field(default=128, env="PASSWORD_MAX_LENGTH")
    password_require_upper: bool = Field(default=True, env="PASSWORD_REQUIRE_UPPER")
    password_require_lower: bool = Field(default=True, env="PASSWORD_REQUIRE_LOWER")
    password_require_digit: bool = Field(default=True, env="PASSWORD_REQUIRE_DIGIT")
    password_require_symbol: bool = Field(default=True, env="PASSWORD_REQUIRE_SYMBOL")
    password_disallow_whitespace: bool = Field(default=True, env="PASSWORD_DISALLOW_WHITESPACE")
    
    # OCR 配置
    ocr_provider: str = Field(default="local", env="OCR_PROVIDER")  # "local" 或 "remote"
    # 本地 OCR 配置（使用 pytesseract）
    tesseract_cmd: str = Field(default="", env="TESSERACT_CMD")  # Tesseract 可执行文件路径，空则使用系统默认
    # 远程 OCR API 配置（预留）
    ocr_api_url: str = Field(default="http://example.invalid", env="OCR_API_URL")  # 远程 OCR API 地址
    ocr_api_key: str = Field(default="", env="OCR_API_KEY")  # 远程 OCR API 密钥

    # LLM 配置
    llm_provider: str = Field(default="", env="LLM_PROVIDER")  # "local" 或 "remote"

    # 远程 LLM API 配置
    llm_api_url: str = Field(default="", env="LLM_API_URL")  # 远程 LLM API 地址
    llm_api_key: str = Field(default="", env="LLM_API_KEY")  # 远程 LLM API 密钥

    model_config = SettingsConfigDict(env_file=resolve_env_file(), env_file_encoding="utf-8")


settings = Settings()
