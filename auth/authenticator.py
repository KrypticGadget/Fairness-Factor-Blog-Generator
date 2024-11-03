# auth/authenticator.py
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from .jwt_handler import JWTHandler
from .permissions import PermissionHandler
from .two_factor import TwoFactorAuth

logger = logging.getLogger(__name__)

class AsyncAuthenticator:
    def __init__(self, db):
        self.db = db
        self.jwt_handler = JWTHandler(db)
        self.permissions = PermissionHandler(db)
        self.two_factor = TwoFactorAuth(db)
        
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        try:
            # Basic authentication
            user = await self.jwt_handler.verify_credentials(email, password)
            if not user:
                return None
                
            # Check 2FA if enabled
            if user.get('two_factor_enabled'):
                return {
                    'requires_2fa': True,
                    'user_id': str(user['_id'])
                }
                
            # Generate tokens
            access_token = await self.jwt_handler.create_access_token(user)
            refresh_token = await self.jwt_handler.create_refresh_token(user)
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'email': user['email'],
                    'name': user['name'],
                    'role': user['role']
                }
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None
            
    async def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify access token and return user info"""
        return await self.jwt_handler.verify_access_token(token)
        
    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Get new access token using refresh token"""
        return await self.jwt_handler.refresh_access_token(refresh_token)
        
    async def verify_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has specific permission"""
        return await self.permissions.check_permission(user_id, permission)
        
    async def verify_access(self, user_role: str, application: str) -> bool:
        """Check user role and application access"""
        try:
            # Check user role
            if user_role == 'admin':
                return True
            elif user_role == 'content_writer' and application in ['Blog Generator', 'Social Media Scheduler', 'Reddit Monitoring']:
                return True
            elif user_role == 'viewer' and application == 'Blog Generator':
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Access verification error: {str(e)}")
            return False
