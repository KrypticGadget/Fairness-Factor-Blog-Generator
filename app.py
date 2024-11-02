# app.py
import streamlit as st
import asyncio
import os
from datetime import datetime
import logging
from typing import Optional, Dict, Any
import base64
from config import Config
from utils.auth import AsyncAuthHandler
from utils.mongo_manager import AsyncMongoManager, get_db_session
from utils.data_handlers import (
    AsyncBlogContentHandler,
    AsyncFileHandler, 
    AsyncAnalyticsHandler
)
from utils.prompt_handler import AsyncPromptHandler
from utils.session_manager import AsyncSessionManager
from llm.llm_client import AsyncLLMClient

# Import page modules
from pages.topic_research import topic_research_page
from pages.topic_campaign import topic_campaign_page
from pages.article_draft import article_draft_page
from pages.editing_criteria import editing_criteria_page
from pages.final_article import final_article_page
from pages.image_description import image_description_page
from pages.seo_generation import seo_generation_page
from pages.user_management import user_management_page

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_session_state():
    """Initialize session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'user_token' not in st.session_state:
        st.session_state.user_token = None
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Login"
    if 'page_history' not in st.session_state:
        st.session_state.page_history = []

async def check_authentication():
    """Check if user is authenticated and verify token"""
    if not st.session_state.authenticated:
        return False
        
    if st.session_state.user_token:
        user = await st.session_state.auth_handler.verify_token(st.session_state.user_token)
        if user:
            st.session_state.user = user
            return True
            
    # Clear session state if authentication fails
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.user_token = None
    return False

def load_css():
    """Load CSS styles"""
    with open('static/styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def display_logo(context: str = 'main'):
    """Display logo with context-specific styling"""
    logo_path = os.path.join('assets', 'FairnessFactorLogo.png')
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
            container_class = 'logo-container-login' if context == 'login' else 'logo-container-main'
            st.markdown(f"""
                <div class="{container_class}">
                    <img src="data:image/png;base64,{logo_data}" alt="Fairness Factor Logo"/>
                </div>
            """, unsafe_allow_html=True)
    else:
        logger.warning("Logo file not found")

async def handle_login(email: str, password: str) -> bool:
    """Handle user login"""
    try:
        if not await st.session_state.auth_handler.verify_email_domain(email):
            st.error("Please use your Fairness Factor email address")
            return False

        loop = asyncio.get_event_loop()
        token = await loop.run_in_executor(None, lambda: st.session_state.auth_handler.login(email, password))
        if token:
            st.session_state.user_token = token
            st.session_state.authenticated = True
            
            # Get user info and store in session state
            user_info = await st.session_state.auth_handler.verify_token(token)
            if user_info:
                st.session_state.user = user_info
                session_id = await st.session_state.session_manager.create_session(
                    email,
                    {'login_time': datetime.now().isoformat()}
                )
                st.session_state.session_id = session_id
                await st.session_state.db_handlers['analytics'].log_activity(
                    email,
                    'login',
                    {'success': True, 'session_id': session_id}
                )
                return True
        return False
    except Exception as e:
        logger.error(f"Login error for {email}: {str(e)}")
        return False

async def handle_logout():
    """Handle user logout"""
    try:
        if st.session_state.session_id:
            await st.session_state.session_manager.end_session(
                st.session_state.session_id
            )
        
        # Log logout activity
        if st.session_state.user:
            await st.session_state.db_handlers['analytics'].log_activity(
                st.session_state.user['email'],
                'logout',
                {'session_id': st.session_state.session_id}
            )
        
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
            
        initialize_session_state()
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")

async def login_page():
    """Display login page"""
    st.title("Fairness Factor Blog Generator")
    
    # Center the login form
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        display_logo('login')
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="example@fairnessfactor.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In")
            
            if submitted:
                if await handle_login(email, password):
                    st.success("Login successful!")
                    st.experimental_rerun()
                else:
                    st.error("Invalid credentials")

class AppState:
    """Application state management"""
    def __init__(self):
        self.initialized = False

    async def initialize(self):
        """Initialize application state"""
        if not self.initialized:
            try:
                async with get_db_session() as (client, db, fs):
                    if not st.session_state.get('initialized'):
                        st.session_state.db_handlers = {
                            'blog': AsyncBlogContentHandler(db),
                            'file': AsyncFileHandler(fs),
                            'analytics': AsyncAnalyticsHandler(db)
                        }
                        st.session_state.auth_handler = AsyncAuthHandler(db)
                        st.session_state.session_manager = AsyncSessionManager(db)
                        st.session_state.prompt_handler = AsyncPromptHandler(db)
                        st.session_state.llm_client = AsyncLLMClient()
                        st.session_state.initialized = True
                
                self.initialized = True
            except Exception as e:
                logger.error(f"Initialization error: {str(e)}")
                raise

async def main_app():
    """Main application runner"""
    # Initialize session state
    initialize_session_state()
    
    app_state = AppState()
    await app_state.initialize()

    # Configure Streamlit page
    st.set_page_config(
        page_title="Fairness Factor Blog Generator",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Load styling
    load_css()

    # Authentication check
    if not st.session_state.authenticated:
        await login_page()
        return
        
    # Verify authentication
    if not await check_authentication():
        await handle_logout()
        st.experimental_rerun()
        return
    
    # Main application UI
    display_logo('main')
    
    # Sidebar navigation
    with st.sidebar:
        st.write(f"Welcome, {st.session_state.user['name']}")
        
        # Navigation menu
        pages = [
            'Topic Research',
            'Topic Campaign',
            'Article Draft',
            'Editing Criteria',
            'Final Article',
            'Image Description',
            'SEO Generation'
        ]
        
        # Add User Management for admin users
        if st.session_state.user.get('role') == 'admin':
            pages.append('User Management')
        
        selected_page = st.radio("Navigation", pages)
        
        # Logout button
        if st.button("Sign Out"):
            await handle_logout()
            st.experimental_rerun()
            return
    
    # Update current page
    st.session_state.current_page = selected_page
    
    # Page routing
    try:
        if selected_page == 'User Management':
            if st.session_state.user.get('role') == 'admin':
                await user_management_page(
                    st.session_state.db_handlers,
                    st.session_state.auth_handler
                )
            else:
                st.error("Access denied")
        elif selected_page == 'Topic Research':
            await topic_research_page(
                st.session_state.db_handlers,
                st.session_state.llm_client,
                st.session_state.prompt_handler
            )
        elif selected_page == 'Topic Campaign':
            await topic_campaign_page(
                st.session_state.db_handlers,
                st.session_state.llm_client,
                st.session_state.prompt_handler
            )
        elif selected_page == 'Article Draft':
            await article_draft_page(
                st.session_state.db_handlers,
                st.session_state.llm_client,
                st.session_state.prompt_handler
            )
        elif selected_page == 'Editing Criteria':
            await editing_criteria_page(
                st.session_state.db_handlers,
                st.session_state.llm_client,
                st.session_state.prompt_handler
            )
        elif selected_page == 'Final Article':
            await final_article_page(
                st.session_state.db_handlers,
                st.session_state.llm_client,
                st.session_state.prompt_handler
            )
        elif selected_page == 'Image Description':
            await image_description_page(
                st.session_state.db_handlers,
                st.session_state.llm_client,
                st.session_state.prompt_handler
            )
        elif selected_page == 'SEO Generation':
            await seo_generation_page(
                st.session_state.db_handlers,
                st.session_state.llm_client,
                st.session_state.prompt_handler
            )
            
        # Log page access
        await st.session_state.db_handlers['analytics'].log_activity(
            st.session_state.user['email'],
            'page_access',
            {'page': selected_page}
        )
        
    except Exception as e:
        logger.error(f"Page error: {str(e)}")
        st.error(f"An error occurred: {str(e)}")

def main():
    """Application entry point"""
    # Set up event loop policy for Windows
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Create and set event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Run the application
        loop.run_until_complete(main_app())
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An unexpected error occurred")
    finally:
        loop.close()

if __name__ == "__main__":
    main()