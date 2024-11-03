from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Required settings with defaults for development
    MONGODB_URI: str = "mongodb://localhost:27017"
    JWT_SECRET_KEY: str = "development_secret_key"
    ANTHROPIC_API_KEY: str = "default_key"
    
    # Optional settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Cache and return settings instance"""
    return Settings()

# Create settings instance
settings = get_settings()
