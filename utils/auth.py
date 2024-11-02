# utils/auth.py
import os
import asyncio
from datetime import datetime, timedelta
import logging
import jwt
import bcrypt
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class AsyncAuthHandler:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.secret_key = os.getenv('JWT_SECRET_KEY')
        if not self.secret_key:
            raise ValueError("JWT_SECRET_KEY not found in environment variables")
        self.users_collection = db.users
        self.login_history_collection = db.login_history

    async def verify_email_domain(self, email: str) -> bool:
        """Verify email belongs to Fairness Factor domain."""
        return email.lower().endswith('@fairnessfactor.com')

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

            # Get current event loop
            loop = asyncio.get_running_loop()
            
            # Run bcrypt operations in executor
            salt = await loop.run_in_executor(None, bcrypt.gensalt)
            hashed = await loop.run_in_executor(None, bcrypt.hashpw, password.encode('utf-8'), salt)

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
            # Get current event loop
            loop = asyncio.get_running_loop()
            
            user = await self.users_collection.find_one({'email': email.lower()})
            if not user:
                return None

            stored_password = user['password']
            if isinstance(stored_password, str):
                stored_password = stored_password.encode('utf-8')

            # Run password check in executor to avoid blocking
            is_valid = await loop.run_in_executor(
                None, 
                bcrypt.checkpw,
                password.encode('utf-8'),
                stored_password
            )

            if is_valid:
                token = jwt.encode({
                    'email': user['email'],
                    'name': user['name'],
                    'role': user.get('role', 'user'),
                    'exp': datetime.utcnow() + timedelta(days=1)
                }, self.secret_key, algorithm='HS256')

                # Log successful login
                await self.login_history_collection.insert_one({
                    'user_email': user['email'],
                    'timestamp': datetime.now(),
                    'success': True
                })
                return token

            # Log failed login
            await self.login_history_collection.insert_one({
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
            # Get current event loop
            loop = asyncio.get_running_loop()
            
            # Run JWT decode in executor
            payload = await loop.run_in_executor(
                None,
                jwt.decode,
                token,
                self.secret_key,
                algorithms=['HS256']
            )
            
            user = await self.users_collection.find_one({'email': payload['email']})
            if user:
                return {
                    'email': user['email'],
                    'name': user['name'],
                    'role': user.get('role', 'user')
                }
            return None
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return None

    async def get_user_sessions(self, user_email: str) -> List[Dict[str, Any]]:
        """Get user's session history"""
        try:
            cursor = self.login_history_collection.find(
                {'user_email': user_email}
            ).sort('timestamp', -1).limit(10)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error retrieving user sessions: {str(e)}")
            return []

    async def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user information."""
        try:
            user = await self.users_collection.find_one({'email': email.lower()})
            if user:
                return {
                    'email': user['email'],
                    'name': user['name'],
                    'role': user.get('role', 'user'),
                    'created_at': user['created_at']
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving user {email}: {str(e)}")
            return None

    async def change_password(self, email: str, current_password: str, new_password: str) -> bool:
        """Change user password."""
        try:
            # Get current event loop
            loop = asyncio.get_running_loop()
            
            user = await self.users_collection.find_one({'email': email.lower()})
            if not user:
                return False

            stored_password = user['password']
            if isinstance(stored_password, str):
                stored_password = stored_password.encode('utf-8')

            # Run password check in executor
            is_valid = await loop.run_in_executor(
                None,
                bcrypt.checkpw,
                current_password.encode('utf-8'),
                stored_password
            )

            if is_valid:
                # Generate new password hash in executor
                salt = await loop.run_in_executor(None, bcrypt.gensalt)
                new_hashed = await loop.run_in_executor(
                    None,
                    bcrypt.hashpw,
                    new_password.encode('utf-8'),
                    salt
                )
                
                result = await self.users_collection.update_one(
                    {'email': email.lower()},
                    {'$set': {'password': new_hashed}}
                )
                return result.modified_count > 0
            return False
        except Exception as e:
            logger.error(f"Password change error for {email}: {str(e)}")
            return False