# auth/jwt_handler.py
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
from config import get_settings

logger = logging.getLogger(__name__)

class JWTHandler:
    def __init__(self, db):
        self.db = db
        self.access_secret = get_settings().JWT_SECRET_KEY
        self.refresh_secret = get_settings().JWT_REFRESH_SECRET
        self.access_expire_minutes = get_settings().JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_expire_days = get_settings().JWT_REFRESH_TOKEN_EXPIRE_DAYS

    async def create_access_token(self, user: Dict[str, Any]) -> str:
        """Create JWT access token"""
        try:
            expires_delta = timedelta(minutes=self.access_expire_minutes)
            expire = datetime.utcnow() + expires_delta
            
            payload = {
                'user_id': str(user['_id']),
                'email': user['email'],
                'role': user['role'],
                'exp': expire,
                'type': 'access'
            }
            
            return jwt.encode(payload, self.access_secret, algorithm='HS256')
            
        except Exception as e:
            logger.error(f"Error creating access token: {str(e)}")
            raise

    async def create_refresh_token(self, user: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        try:
            expires_delta = timedelta(days=self.refresh_expire_days)
            expire = datetime.utcnow() + expires_delta
            
            payload = {
                'user_id': str(user['_id']),
                'exp': expire,
                'type': 'refresh'
            }
            
            return jwt.encode(payload, self.refresh_secret, algorithm='HS256')
            
        except Exception as e:
            logger.error(f"Error creating refresh token: {str(e)}")
            raise

    async def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT access token"""
        try:
            payload = jwt.decode(token, self.access_secret, algorithms=['HS256'])
            
            if payload['type'] != 'access':
                return None
                
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Access token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid access token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error verifying access token: {str(e)}")
            return None

    async def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT refresh token"""
        try:
            payload = jwt.decode(token, self.refresh_secret, algorithms=['HS256'])
            
            if payload['type'] != 'refresh':
                return None
                
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid refresh token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error verifying refresh token: {str(e)}")
            return None

    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Get new access token using refresh token"""
        try:
            payload = await self.verify_refresh_token(refresh_token)
            if not payload:
                return None
                
            user = await self.db.users.find_one({'_id': payload['user_id']})
            if not user:
                return None
                
            access_token = await self.create_access_token(user)
            
            return {
                'access_token': access_token,
                'user': {
                    'email': user['email'],
                    'role': user['role']
                }
            }
            
        except Exception as e:
            logger.error(f"Error refreshing access token: {str(e)}")
            return None
