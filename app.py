# app.py
import streamlit as st
import asyncio
import os
from datetime import datetime
import base64
from config import Config
from test_mongodb import test_connection
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
from pages import (
    topic_research, 
    topic_campaign, 
    article_draft, 
    editing_criteria, 
    final_article, 
    image_description, 
    seo_generation
)
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_database():
    """Check database connection on startup"""
    connected = await test_connection()
    if not connected:
        st.error("⚠️ Failed to connect to database. Please check configuration.")
        st.stop()

def load_css(css_file: str) -> None:
    """Load CSS file"""
    try:
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error loading CSS file: {str(e)}")
        st.error(f"Error loading CSS file: {str(e)}")

def load_image(image_path: str) -> str:
    """Load and encode image file"""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        logger.error(f"Error loading image: {str(e)}")
        return None

def display_logo(context: str = 'main') -> None:
    """Display Fairness Factor logo with context-specific styling"""
    logo_path = './assets/FairnessFactorLogo.PNG'
    logo_data = load_image(logo_path)
    
    if logo_data:
        container_class = 'logo-container-login' if context == 'login' else 'logo-container-main'
        st.markdown(f"""
            <div class="{container_class}">
                <img src="data:image/png;base64,{logo_data}" alt="Fairness Factor Logo"/>
            </div>
        """, unsafe_allow_html=True)

async def initialize_session_state(mongo_manager: AsyncMongoManager):
    """Initialize session state with database handlers"""
    if 'initialized' not in st.session_state:
        try:
            async with get_db_session() as (client, db, fs):
                st.session_state.db_handlers = {
                    'blog': AsyncBlogContentHandler(db),
                    'file': AsyncFileHandler(fs),
                    'analytics': AsyncAnalyticsHandler(db),
                }
                st.session_state.auth_handler = AsyncAuthHandler(db)
                st.session_state.session_manager = AsyncSessionManager(db)
                st.session_state.prompt_handler = AsyncPromptHandler(db)
                st.session_state.llm_client = AsyncLLMClient()
                st.session_state.initialized = True
                
        except Exception as e:
            logger.error(f"Error initializing session state: {str(e)}")
            st.error("Failed to initialize application. Please try again.")
            st.stop()

async def handle_login(
    email: str,
    password: str,
    auth_handler: AsyncAuthHandler,
    session_manager: AsyncSessionManager,
    analytics_handler: AsyncAnalyticsHandler
) -> bool:
    """Handle user login process"""
    try:
        # Verify email domain
        if not await auth_handler.verify_email_domain(email):
            st.error("Please use your Fairness Factor email address")
            return False

        # Attempt login
        token = await auth_handler.login(email, password)
        if token:
            st.session_state.user_token = token
            
            # Create new session
            session_id = await session_manager.create_session(
                email,
                {'login_time': datetime.now().isoformat()}
            )
            st.session_state.session_id = session_id
            
            # Log activity
            await analytics_handler.log_activity(
                email,
                'login',
                {'success': True, 'session_id': session_id}
            )
            
            return True
        else:
            # Log failed attempt
            await analytics_handler.log_activity(
                email,
                'login_failed',
                {'reason': 'invalid_credentials'}
            )
            st.error("Invalid credentials")
            return False
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        st.error("An error occurred during login")
        return False

async def handle_logout(
    user_email: str,
    session_manager: AsyncSessionManager,
    analytics_handler: AsyncAnalyticsHandler
) -> None:
    """Handle user logout process"""
    try:
        if 'session_id' in st.session_state:
            await session_manager.end_session(st.session_state.session_id)
            await analytics_handler.log_activity(
                user_email,
                'logout',
                {'session_id': st.session_state.session_id}
            )
        
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
            
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")

async def main():
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        st.error(f"⚠️ Configuration error: {str(e)}")
        st.stop()
        
    # Check database connection
    await check_database()

    # Configure Streamlit page
    st.set_page_config(
        page_title="Fairness Factor Blog Generator",
        page_icon="./assets/FairnessFactorLogo Icon.ico",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Load styling
    load_css('static/styles.css')
    
    # Initialize MongoDB and session state
    mongo_manager = AsyncMongoManager()
    await initialize_session_state(mongo_manager)
    
    # Authentication check
    if 'user_token' not in st.session_state:
        display_logo('login')
        st.markdown(
            '<h1 class="login-header">Welcome to Fairness Factor Blog Generator</h1>',
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            with st.form("login_form"):
                st.markdown("""
                    <div class="login-container">
                        <h3>Sign in with your Fairness Factor account</h3>
                    </div>
                """, unsafe_allow_html=True)

                email = st.text_input("Email", placeholder="example@fairnessfactor.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In")

                if submitted:
                    if not email or not password:
                        st.error("Please enter both email and password")
                    else:
                        success = await handle_login(
                            email,
                            password,
                            st.session_state.auth_handler,
                            st.session_state.session_manager,
                            st.session_state.analytics_handler
                        )
                        if success:
                            st.experimental_rerun()

        st.stop()

    # Rest of your existing main() function code...
    [Previous main function code continues unchanged...]

if __name__ == "__main__":
    # Validate configuration and check database before running the app
    asyncio.run(main())

    # Verify token and get user info
    user = await st.session_state.auth_handler.verify_token(st.session_state.user_token)
    if not user:
        await handle_logout(
            st.session_state.get('user', {}).get('email'),
            st.session_state.session_manager,
            st.session_state.analytics_handler
        )
        st.experimental_rerun()

    display_logo('main')

    # Sidebar navigation
    with st.sidebar:
        st.markdown(
            f'<div class="user-welcome">Welcome, {user["name"]}</div>',
            unsafe_allow_html=True
        )
        
        if st.button("Sign Out", key="logout"):
            await handle_logout(
                user['email'],
                st.session_state.session_manager,
                st.session_state.analytics_handler
            )
            st.experimental_rerun()

        st.markdown('<div class="nav-header">Navigation</div>', unsafe_allow_html=True)
        
        pages = [
            'Topic Research',
            'Topic Campaign',
            'Article Draft',
            'Editing Criteria',
            'Final Article',
            'Image Description',
            'SEO Generation'
        ]
        
        if user.get('role') == 'admin':
            pages.append('User Management')

        page = st.radio("", pages)

    # Page routing with analytics
    try:
        if page == 'Topic Research':
            await topic_research.topic_research_page(
                st.session_state.db_handlers,
                st.session_state.llm_client,
                st.session_state.prompt_handler
            )
        elif page == 'Topic Campaign':
            await topic_campaign.topic_campaign_page(
                st.session_state.db_handlers,
                st.session_state.llm_client,
                st.session_state.prompt_handler
            )
        elif page == 'Article Draft':
            await article_draft.article_draft_page(
                st.session_state.db_handlers,
                st.session_state.llm_client,
                st.session_state.prompt_handler
            )
        elif page == 'Editing Criteria':
            await editing_criteria.editing_criteria_page(
                st.session_state.db_handlers,
                st.session_state.llm_client,
                st.session_state.prompt_handler
            )
        elif page == 'Final Article':
            await final_article.final_article_page(
                st.session_state.db_handlers,
                st.session_state.llm_client,
                st.session_state.prompt_handler
            )
        elif page == 'Image Description':
            await image_description.image_description_page(
                st.session_state.db_handlers,
                st.session_state.llm_client,
                st.session_state.prompt_handler
            )
        elif page == 'SEO Generation':
            await seo_generation.seo_generation_page(
                st.session_state.db_handlers,
                st.session_state.llm_client,
                st.session_state.prompt_handler
            )

        # Log page view
        await st.session_state.analytics_handler.log_activity(
            user['email'],
            'page_view',
            {
                'page': page,
                'session_id': st.session_state.session_id
            }
        )

    except Exception as e:
        logger.error(f"Error in page routing: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
        await st.session_state.analytics_handler.log_activity(
            user['email'],
            'error',
            {
                'page': page,
                'error': str(e),
                'session_id': st.session_state.session_id
            }
        )

    # Footer
    st.markdown("""
        <div class="footer">
            <p>© 2024 Fairness Factor. All rights reserved.</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    asyncio.run(main())