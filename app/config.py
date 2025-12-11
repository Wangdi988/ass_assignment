import os
from typing import List, Optional, Union, ClassVar
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    # APP SETTINGS
    ENVIRONMENT: str = "development"
    APP_NAME: str = "FastAPI Template"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api"
    SECRET_KEY: str
    AUTH_USERS: str = ""

    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    def get_auth_users(self) -> dict:
        """Parse AUTH_USERS string into a dictionary of username:password pairs."""
        if not self.AUTH_USERS:
            return {}

        users = {}
        for user_entry in self.AUTH_USERS.split(','):
            if ':' in user_entry:
                username, password = user_entry.split(':', 1)
                users[username.strip()] = password.strip()

        return users
    
    # REDIS
    REDIS_URL: str
    REDIS_TIMEOUT: int = 60

    # LOGGING
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"

    # SECURITY
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    FILE_PATH: str = ""

    APP_DIR: ClassVar[Path] = Path(__file__).resolve().parent
    REPO_ROOT: ClassVar[Path] = APP_DIR.parent
    SECRETS_DIR: ClassVar[Path] = REPO_ROOT / "app" / "core"  / "secrets"


settings = Settings()