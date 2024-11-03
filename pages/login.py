# pages/login.py
import streamlit as st
import asyncio
from typing import Optional, Dict, Any
import logging
from auth.authenticator import AsyncAuthenticator
from security.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

async def login_page(auth_handler: AsyncAuthenticator, rate_limiter: RateLimiter):
    """Login page handler"""
    st.title("Fairness Factor Blog Generator")
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="example@fairnessfactor.com")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Sign In"):
            try:
                # Check rate limiting
                if await rate_limiter.is_rate_limited(email):
                    st.error("Too many login attempts. Please try again later.")
                    return
                
                # Record login attempt
                await rate_limiter.add_request(email)
                
                # Authenticate user
                result = await auth_handler.authenticate_user(email, password)
                
                if not result:
                    st.error("Invalid credentials")
                    return
                
                if result.get('requires_2fa'):
                    # Handle 2FA
                    st.session_state['pending_2fa'] = True
                    st.session_state['temp_user_id'] = result['user_id']
                    st.rerun()
                    return
                
                # Set session state
                st.session_state['authenticated'] = True
                st.session_state['user'] = result['user']
                st.session_state['access_token'] = result['access_token']
                st.session_state['refresh_token'] = result['refresh_token']
                
                st.success("Login successful!")
                st.rerun()
                
            except Exception as e:
                logger.error(f"Login error: {str(e)}")
                st.error("An error occurred during login")

async def two_factor_page(auth_handler: AsyncAuthenticator):
    """2FA verification page"""
    st.title("Two-Factor Authentication")
    
    with st.form("2fa_form"):
        token = st.text_input("Enter 2FA Code")
        
        if st.form_submit_button("Verify"):
            try:
                user_id = st.session_state.get('temp_user_id')
                if not user_id:
                    st.error("Invalid session")
                    return
                
                # Verify 2FA token
                if await auth_handler.two_factor.verify_2fa(user_id, token):
                    # Complete authentication
                    user = await auth_handler.db.users.find_one({'_id': user_id})
                    
                    access_token = await auth_handler.jwt_handler.create_access_token(user)
                    refresh_token = await auth_handler.jwt_handler.create_refresh_token(user)
                    
                    # Update session state
                    st.session_state['authenticated'] = True
                    st.session_state['user'] = {
                        'email': user['email'],
                        'name': user['name'],
                        'role': user['role']
                    }
                    st.session_state['access_token'] = access_token
                    st.session_state['refresh_token'] = refresh_token
                    
                    # Clean up temporary state
                    del st.session_state['pending_2fa']
                    del st.session_state['temp_user_id']
                    
                    st.success("Authentication successful!")
                    st.rerun()
                else:
                    st.error("Invalid 2FA code")
                    
            except Exception as e:
                logger.error(f"2FA verification error: {str(e)}")
                st.error("An error occurred during verification")