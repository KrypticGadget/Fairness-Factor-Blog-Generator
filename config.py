# E:\Kryptic Gadget Github Repos\Fairness-Factor-Blog-Generator\config.py
import streamlit as st
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_secret(key: str) -> Optional[str]:
    """Get secret from Streamlit secrets or environment variables"""
    try:
        # Try Streamlit secrets first
        return st.secrets[key]
    except:
        # Fall back to environment variables
        return os.getenv(key)

class Config:
    MONGODB_URI = get_secret("MONGODB_URI")
    JWT_SECRET_KEY = get_secret("JWT_SECRET_KEY")
    ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY")
    
    @classmethod
    def validate(cls):
        """Validate all required configuration is present"""
        missing = []
        for attr in ['MONGODB_URI', 'JWT_SECRET_KEY', 'ANTHROPIC_API_KEY']:
            if not getattr(cls, attr):
                missing.append(attr)
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")