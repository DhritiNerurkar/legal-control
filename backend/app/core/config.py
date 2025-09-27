from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Legal Entity Due Diligence System"
    VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str = "sqlite:///./legal_capacity.db"

    # AI Configuration
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

    # ChromaDB Configuration
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "legal_documents"

    # Document Processing
    DOCUMENTS_PATH: str = "./data/documents"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # External APIs
    LEI_API_BASE_URL: str = "https://api.gleif.org/api/v1"
    SEC_EDGAR_BASE_URL: str = "https://data.sec.gov"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Development/Testing Configuration
    DEVELOPMENT_MODE: bool = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
    ENABLED_STEPS: str = os.getenv("ENABLED_STEPS", "1,2,3,4,5,6,7")  # Comma-separated step numbers

    # CORS
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()