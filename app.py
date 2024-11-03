# app.py
import streamlit as st
import asyncio
import os
from datetime import datetime
import logging
from typing import Optional, Dict, Any
from config import settings
from database.mongo_manager import get_db_session
from auth.authenticator import AsyncAuthenticator
from security.rate_limiter import RateLimiter
from security.audit_log import AuditLogger
from security.encryption import EncryptionHandler
from utils.data_handlers import AsyncBlogContentHandler, AsyncAnalyticsHandler
from utils.session_manager import AsyncSessionManager

# Import applications
from apps.blog_generator import BlogGeneratorApp
from apps.social_media_scheduler import SocialMediaSchedulerApp
from apps.reddit_monitoring import RedditMonitoringApp
from apps.user_management import UserManagementApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FairnessFactor:
    """Main application class for Fairness Factor Internal Tools"""
    
    def __init__(self):
        self.initialize_state()
        self.setup_config()
        self.load_apps()

    def initialize_state(self):
        """Initialize session state variables"""
        state_vars = {
            'authenticated': False,
            'user': None,
            'current_app': None,
            'db_session': None,
            'handlers': {},
            'encryption': None
        }
        
        for var, value in state_vars.items():
            if var not in st.session_state:
                st.session_state[var] = value

    def setup_config(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title="Fairness Factor Internal Tools",
            page_icon="⚖️",
            layout="wide",
            initial_sidebar_state="expanded"
        )

    def load_apps(self):
        """Initialize available applications"""
        self.apps = {
            'Blog Generator': BlogGeneratorApp(),
            'Social Media Scheduler': SocialMediaSchedulerApp(),
            'Reddit Monitoring': RedditMonitoringApp(),
            'User Management': UserManagementApp()
        }

    async def initialize_handlers(self):
        """Initialize database and security handlers"""
        try:
            # Get database session
            db_session = get_db_session()
            client, db = await db_session.__aenter__()
            
            # Initialize handlers
            st.session_state.handlers = {
                'auth': AsyncAuthenticator(db),
                'blog': AsyncBlogContentHandler(db),
                'analytics': AsyncAnalyticsHandler(db),
                'rate_limiter': RateLimiter(db),
                'audit': AuditLogger(db),
                'session': AsyncSessionManager(db)
            }
            
            # Initialize encryption
            st.session_state.encryption = EncryptionHandler()
            
            st.session_state.db_session = db_session
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize handlers: {str(e)}")
            return False

    def render_login(self):
        """Render login page"""
        st.title("Fairness Factor Internal Tools")
        
        if os.path.exists('static/logo.png'):
            st.image('static/logo.png', width=200)
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="example@fairnessfactor.com")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Sign In"):
                self.handle_login(email, password)

    async def handle_login(self, email: str, password: str):
        """Process login attempt"""
        try:
            # Check rate limiting
            if await st.session_state.handlers['rate_limiter'].is_rate_limited(email):
                st.error("Too many login attempts. Please try again later.")
                return
            
            # Authenticate user
            auth_result = await st.session_state.handlers['auth'].authenticate_user(email, password)
            
            if not auth_result:
                st.error("Invalid credentials")
                await st.session_state.handlers['audit'].log_event(
                    email,
                    'login_failed',
                    {'reason': 'invalid_credentials'}
                )
                return
            
            if auth_result.get('requires_2fa'):
                st.session_state['pending_2fa'] = True
                st.session_state['temp_user_id'] = auth_result['user_id']
                st.rerun()
                return
            
            # Set session state
            st.session_state.authenticated = True
            st.session_state.user = auth_result['user']
            
            # Create session
            session_id = await st.session_state.handlers['session'].create_session(
                email,
                {'login_time': datetime.utcnow().isoformat()}
            )
            
            # Log successful login
            await st.session_state.handlers['audit'].log_event(
                email,
                'login_successful',
                {'session_id': session_id}
            )
            
            st.success("Login successful!")
            st.rerun()
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            st.error("An error occurred during login")

    def render_sidebar(self):
        """Render application sidebar"""
        with st.sidebar:
            st.write(f"Welcome, {st.session_state.user['name']}")
            st.write(f"Role: {st.session_state.user['role'].capitalize()}")
            
            # Get available apps based on user role
            available_apps = self.get_available_apps(st.session_state.user['role'])
            
            # App selection
            selected_app = st.selectbox(
                "Select Application",
                options=available_apps
            )
            
            if selected_app != st.session_state.current_app:
                st.session_state.current_app = selected_app
                st.rerun()
            
            if st.button("Sign Out"):
                self.handle_logout()

    def get_available_apps(self, role: str) -> list:
        """Get list of available apps based on user role"""
        role_apps = {
            'admin': [
                'Blog Generator',
                'Social Media Scheduler',
                'Reddit Monitoring',
                'User Management'
            ],
            'content_writer': [
                'Blog Generator',
                'Social Media Scheduler',
                'Reddit Monitoring'
            ],
            'viewer': [
                'Blog Generator'
            ]
        }
        return role_apps.get(role, ['Blog Generator'])

    async def handle_logout(self):
        """Process user logout"""
        try:
            if st.session_state.user:
                # End session
                await st.session_state.handlers['session'].end_session(
                    st.session_state.user['email']
                )
                
                # Log logout
                await st.session_state.handlers['audit'].log_event(
                    st.session_state.user['email'],
                    'logout',
                    {'timestamp': datetime.utcnow().isoformat()}
                )
            
            # Clear session state
            for key in list(st.session_state.keys()):
                if key not in ['db_session', 'handlers', 'encryption']:
                    del st.session_state[key]
            
            st.rerun()
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            st.error("An error occurred during logout")

    def render_app(self):
        """Render selected application"""
        try:
            if st.session_state.current_app:
                app = self.apps[st.session_state.current_app]
                app.render(st.session_state.handlers)
            else:
                st.write("Please select an application from the sidebar.")
                
        except Exception as e:
            logger.error(f"Error rendering app: {str(e)}")
            st.error("An error occurred while loading the application")

    def main(self):
        """Main application entry point"""
        try:
            # Initialize handlers if needed
            if not st.session_state.handlers:
                asyncio.run(self.initialize_handlers())
            
            # Load CSS
            with open('static/styles.css') as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
            
            # Check authentication
            if not st.session_state.authenticated:
                self.render_login()
                return
            
            # Render sidebar and main content
            self.render_sidebar()
            self.render_app()
            
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            st.error("An unexpected error occurred")
            
        finally:
            # Cleanup if needed
            if st.session_state.get('db_session'):
                asyncio.run(st.session_state.db_session.__aexit__(None, None, None))

if __name__ == "__main__":
    app = FairnessFactor()
    app.main()