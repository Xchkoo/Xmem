from pydantic_settings import BaseSettings  # pyright: ignore[reportMissingImports]
from pydantic import Field  # pyright: ignore[reportMissingImports]


class Settings(BaseSettings):
    database_url: str = Field(env="DATABASE_URL")
    jwt_secret: str = Field(env="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # OCR 配置
    ocr_provider: str = Field(default="local", env="OCR_PROVIDER")  # "local" 或 "remote"
    # 本地 OCR 配置（使用 pytesseract）
    tesseract_cmd: str = Field(default="", env="TESSERACT_CMD")  # Tesseract 可执行文件路径，空则使用系统默认
    # 远程 OCR API 配置（预留）
    ocr_api_url: str = Field(default="", env="OCR_API_URL")  # 远程 OCR API 地址
    ocr_api_key: str = Field(default="", env="OCR_API_KEY")  # 远程 OCR API 密钥

    class Config:
        env_file = ".env"


settings = Settings()

