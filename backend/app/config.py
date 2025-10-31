from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    ALPHA_VANTAGE_KEY: str = ""
    FINNHUB_KEY: str = ""
    RAPIDAPI_KEY: Optional[str] = None
    FRED_API_KEY: Optional[str] = None

    # Cache settings (seconds)
    CACHE_TTL_QUOTES: int = 90
    CACHE_TTL_MOVERS: int = 30
    CACHE_TTL_BREADTH: int = 60
    CACHE_TTL_SECTORS: int = 90
    CACHE_TTL_MACRO: int = 300

    # Server
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 5173

    # HTTP settings
    HTTP_TIMEOUT: int = 3
    HTTP_RETRIES: int = 2

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
