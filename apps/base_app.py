# apps/base_app.py
import streamlit as st
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class BaseApp(ABC):
    """Base class for all applications"""
    
    def __init__(self):
        self.title = "Base Application"
        self.description = "Base application description"
        self.icon = "🔧"

    @abstractmethod
    async def initialize(self, handlers: Dict[str, Any]) -> bool:
        """Initialize application resources"""
        pass

    @abstractmethod
    async def render(self, handlers: Dict[str, Any]):
        """Render application interface"""
        pass

    def show_error(self, message: str):
        """Display error message"""
        st.error(f"{self.icon} {message}")

    def show_success(self, message: str):
        """Display success message"""
        st.success(f"{self.icon} {message}")

    def show_info(self, message: str):
        """Display info message"""
        st.info(f"{self.icon} {message}")

    async def check_permissions(self, handlers: Dict[str, Any], required_permission: str) -> bool:
        """Check if user has required permission"""
        try:
            user_id = st.session_state.user['_id']
            return await handlers['auth'].check_permission(user_id, required_permission)
        except Exception as e:
            logger.error(f"Permission check error: {str(e)}")
            return False