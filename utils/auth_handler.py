# utils/auth_handler.py
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any
import asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

class AsyncAuthHandler:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.secret_key = os.getenv('JWT_SECRET_KEY')
        if not self.secret_key:
            raise ValueError("JWT_SECRET_KEY not found in environment variables")
        self.db = db
        self.users_collection = db.users
        asyncio.create_task(self._ensure_admin_user())

    async def _ensure_admin_user(self):
        """Ensure admin user exists"""
        admin_email = 'zack@fairnessfactor.com'
        admin_exists = await self.users_collection.find_one({'email': admin_email})
        
        if not admin_exists:
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw("1122Kryptic$".encode('utf-8'), salt)
            
            await self.users_collection.insert_one({
                'email': admin_email,
                'password': hashed_password,
                'name': 'Admin User',
                'role': 'admin',
                'created_at': datetime.now(),
                'created_by': 'system'
            })
            logger.info("Created default admin user")

    async def verify_email_domain(self, email: str) -> bool:
        """Verify email belongs to Fairness Factor domain."""
        email = email.lower()
        return email.endswith('fairnessfactor.com')

    async def add_user(
        self, 
        email: str, 
        password: str, 
        name: str, 
        added_by: str, 
        role: str = 'user'
    ) -> bool:
        """Add a new user to the system."""
        try:
            if not await self.verify_email_domain(email):
                raise ValueError("Only Fairness Factor email addresses are allowed")

            existing_user = await self.users_collection.find_one({'email': email.lower()})
            if existing_user:
                raise ValueError("User already exists")

            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

            await self.users_collection.insert_one({
                'email': email.lower(),
                'password': hashed,
                'name': name,
                'role': role,
                'created_at': datetime.now(),
                'created_by': added_by
            })
            return True

        except Exception as e:
            logger.error(f"Error adding user {email}: {str(e)}")
            raise

    async def login(self, email: str, password: str) -> Optional[str]:
        """Authenticate user and return JWT token."""
        try:
            user = await self.users_collection.find_one({'email': email.lower()})
            if not user:
                return None

            stored_password = user['password']
            if isinstance(stored_password, str):
                stored_password = stored_password.encode('utf-8')

            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                token = jwt.encode({
                    'email': user['email'],
                    'name': user['name'],
                    'role': user.get('role', 'user'),
                    'exp': datetime.utcnow() + timedelta(days=1)
                }, self.secret_key, algorithm='HS256')

                # Log successful login
                await self.db.login_history.insert_one({
                    'user_email': user['email'],
                    'timestamp': datetime.now(),
                    'success': True
                })

                return token

            # Log failed login attempt
            await self.db.login_history.insert_one({
                'user_email': email,
                'timestamp': datetime.now(),
                'success': False,
                'reason': 'invalid_password'
            })
            return None

        except Exception as e:
            logger.error(f"Login error for {email}: {str(e)}")
            return None

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user info."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            user = await self.users_collection.find_one({'email': payload['email']})

            if user:
                return {
                    'email': user['email'],
                    'name': user['name'],
                    'role': user.get('role', 'user')
                }

            return None

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return None

    async def get_user_sessions(self, user_email: str) -> List[Dict[str, Any]]:
        """Get user's session history"""
        try:
            cursor = self.db.login_history.find(
                {'user_email': user_email}
            ).sort('timestamp', -1).limit(10)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error retrieving user sessions: {str(e)}")
            return []