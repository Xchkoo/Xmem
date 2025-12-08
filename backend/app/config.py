from pydantic_settings import BaseSettings  # pyright: ignore[reportMissingImports]
from pydantic import Field  # pyright: ignore[reportMissingImports]


class Settings(BaseSettings):
    database_url: str = Field(env="DATABASE_URL")
    jwt_secret: str = Field(env="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    class Config:
        env_file = ".env"


settings = Settings()

