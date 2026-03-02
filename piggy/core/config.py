"""
Configuration module.
"""

from typing import List

from fastapi_mail import ConnectionConfig
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """
    Configuration settings for the Piggy API application.
    """

    POSTGRES_USER: str = "piggy"
    POSTGRES_PASSWORD: str = "LOCAL_PW"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "piggy_db"

    @property
    def DATABASE_URL(  # pylint: disable=invalid-name, missing-function-docstring
        self,
    ) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            + f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 28

    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    FINTS_PRODUCT_ID: str = "6151256F3D4F9975B877BD4A2"

    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@piggy.example"
    MAIL_PORT: int = 1025
    MAIL_SERVER: str = "localhost"
    MAIL_FROM_NAME: str = "Piggy"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = False
    VALIDATE_CERTS: bool = False

    @property
    def MAIL_CONFIG(  # pylint: disable=invalid-name, missing-function-docstring
        self,
    ) -> ConnectionConfig:
        return ConnectionConfig(
            MAIL_USERNAME=self.MAIL_USERNAME,
            MAIL_PASSWORD=self.MAIL_PASSWORD,
            MAIL_FROM=self.MAIL_FROM,
            MAIL_PORT=self.MAIL_PORT,
            MAIL_SERVER=self.MAIL_SERVER,
            MAIL_FROM_NAME=self.MAIL_FROM_NAME,
            MAIL_STARTTLS=self.MAIL_STARTTLS,
            MAIL_SSL_TLS=self.MAIL_SSL_TLS,
            USE_CREDENTIALS=self.USE_CREDENTIALS,
            VALIDATE_CERTS=self.VALIDATE_CERTS,
        )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


config = Config()
