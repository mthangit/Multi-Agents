from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database settings
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Jaeger settings
    JAEGER_HOST: str
    JAEGER_PORT: int
    JAEGER_ENABLED: bool

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings() 