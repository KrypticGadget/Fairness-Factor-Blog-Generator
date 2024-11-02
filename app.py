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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_session_state():
    """Initialize session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'user_token' not in st.session_state:
        st.session_state.user_token = None
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None

def load_css(css_file: str) -> None:
    """Load CSS file"""
    try:
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error loading CSS file: {str(e)}")
        st.error(f"Error loading CSS file: {str(e)}")

def display_logo(context: str = 'main') -> None:
    """Display Fairness Factor logo with context-specific styling"""
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

        token = await st.session_state.auth_handler.login(email, password)
        if token:
            st.session_state.user_token = token
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
        logger.error(f"Login error: {str(e)}")
        return False

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

async def run_app():
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
    load_css('static/styles.css')

    # Authentication flow
    if not st.session_state.user_token:
        display_logo('login')
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="example@fairnessfactor.com")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                success = await handle_login(email, password)
                if success:
                    st.experimental_rerun()
    else:
        # Verify existing session
        user = await st.session_state.auth_handler.verify_token(st.session_state.user_token)
        if not user:
            # Clear session state if token is invalid
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            initialize_session_state()
            st.experimental_rerun()
        else:
            st.session_state.user = user
            
            # Main application UI
            display_logo('main')
            
            # Sidebar navigation
            with st.sidebar:
                st.write(f"Welcome, {user['name']}")
                if st.button("Sign Out"):
                    if st.session_state.session_id:
                        await st.session_state.session_manager.end_session(
                            st.session_state.session_id
                        )
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    initialize_session_state()
                    st.experimental_rerun()

                pages = [
                    'Topic Research',
                    'Topic Campaign',
                    'Article Draft',
                    'Editing Criteria',
                    'Final Article',
                    'Image Description',
                    'SEO Generation'
                ]
                
                page = st.radio("Navigation", pages)

            # Page routing
            try:
                if page == 'Topic Research':
                    await topic_research_page(
                        st.session_state.db_handlers,
                        st.session_state.llm_client,
                        st.session_state.prompt_handler
                    )
                elif page == 'Topic Campaign':
                    await topic_campaign_page(
                        st.session_state.db_handlers,
                        st.session_state.llm_client,
                        st.session_state.prompt_handler
                    )
                elif page == 'Article Draft':
                    await article_draft_page(
                        st.session_state.db_handlers,
                        st.session_state.llm_client,
                        st.session_state.prompt_handler
                    )
                elif page == 'Editing Criteria':
                    await editing_criteria_page(
                        st.session_state.db_handlers,
                        st.session_state.llm_client,
                        st.session_state.prompt_handler
                    )
                elif page == 'Final Article':
                    await final_article_page(
                        st.session_state.db_handlers,
                        st.session_state.llm_client,
                        st.session_state.prompt_handler
                    )
                elif page == 'Image Description':
                    await image_description_page(
                        st.session_state.db_handlers,
                        st.session_state.llm_client,
                        st.session_state.prompt_handler
                    )
                elif page == 'SEO Generation':
                    await seo_generation_page(
                        st.session_state.db_handlers,
                        st.session_state.llm_client,
                        st.session_state.prompt_handler
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
        loop.run_until_complete(run_app())
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An unexpected error occurred")
    finally:
        loop.close()

if __name__ == "__main__":
    main()