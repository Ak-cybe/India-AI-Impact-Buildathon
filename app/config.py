"""Application configuration management"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    api_key: str = "default-api-key-change-this"
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    
    # LLM API Keys
    google_api_key: str
    openai_api_key: Optional[str] = None
    safe_browsing_api_key: Optional[str] = None
    
    # Evaluation Callback
    callback_endpoint: str = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Application Settings
    environment: str = "development"
    log_level: str = "INFO"
    max_conversation_turns: int = 20
    confidence_threshold: float = 0.75
    
    # Response Latency
    min_response_delay: int = 10
    max_response_delay: int = 90
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
