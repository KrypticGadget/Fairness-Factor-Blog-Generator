import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel
import streamlit as st

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    MONGODB_URI: str
    JWT_SECRET_KEY: str
    ANTHROPIC_API_KEY: str
    APP_NAME: str = "Fairness Factor Blog Generator"
    APP_DOMAIN: str = "fairnessfactor.com"
    ADMIN_EMAIL: str = "admin@fairnessfactor.com"

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables"""
        env_vars = {}
        for field in cls.model_fields.keys():
            # Try Streamlit secrets first
            try:
                value = st.secrets[field]
            except:
                # Fall back to environment variables
                value = os.getenv(field)
            
            if value is not None:
                env_vars[field] = value

        return cls(**env_vars)

    def validate(self):
        """Validate all required configuration is present"""
        missing = []
        for field in ["MONGODB_URI", "JWT_SECRET_KEY", "ANTHROPIC_API_KEY"]:
            if not getattr(self, field):
                missing.append(field)
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

# Create settings instance
settings = Settings.from_env()
