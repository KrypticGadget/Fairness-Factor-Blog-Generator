# utils/auth_handler.py
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any, List
import asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

logger = logging.getLogger(__name__)

class AsyncAuthHandler:
    """Handles user authentication and management"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.secret_key = os.getenv('JWT_SECRET_KEY')
        if not self.secret_key:
            raise ValueError("JWT_SECRET_KEY not found in environment variables")
        self.db = db
        self.users_collection = db.users
        self.login_history_collection = db.login_history
        asyncio.create_task(self._ensure_indexes())
        asyncio.create_task(self._ensure_admin_user())

    async def delete_user(self, email: str, admin_email: str) -> bool:
        """Delete a user"""
        try:
            # Don't allow deletion of the last admin user
            if email.lower() == os.getenv('ADMIN_EMAIL', 'admin@fairnessfactor.com').lower():
                admin_count = await self.users_collection.count_documents({'role': 'admin'})
                if admin_count <= 1:
                    raise ValueError("Cannot delete the last admin user")

            result = await self.users_collection.delete_one({'email': email.lower()})
            
            if result.deleted_count > 0:
                # Log user deletion
                await self.db.user_activity.insert_one({
                    'user_email': email.lower(),
                    'activity_type': 'user_deleted',
                    'deleted_by': admin_email,  # Use passed admin email instead of session state
                    'timestamp': datetime.now()
                })
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting user {email}: {str(e)}")
            return False

    async def update_user(
        self, 
        email: str, 
        updates: Dict[str, Any],
        admin_email: str  # Add admin_email parameter
    ) -> bool:
        """Update user information"""
        try:
            # Don't allow role change for the last admin
            if 'role' in updates and email.lower() == os.getenv('ADMIN_EMAIL', '').lower():
                admin_count = await self.users_collection.count_documents({'role': 'admin'})
                if admin_count <= 1 and updates['role'] != 'admin':
                    raise ValueError("Cannot change role of the last admin user")

            result = await self.users_collection.update_one(
                {'email': email.lower()},
                {'$set': {
                    **updates,
                    'updated_at': datetime.now()
                }}
            )
            
            if result.modified_count > 0:
                # Log user update
                await self.db.user_activity.insert_one({
                    'user_email': email.lower(),
                    'activity_type': 'user_updated',
                    'updated_by': admin_email,  # Use passed admin email instead of session state
                    'updates': updates,
                    'timestamp': datetime.now()
                })
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating user {email}: {str(e)}")
            return False

    # ... [rest of the existing methods remain the same]

    async def _ensure_indexes(self):
        """Create necessary database indexes"""
        try:
            await self.users_collection.create_index([("email", 1)], unique=True)
            await self.users_collection.create_index([("created_at", -1)])
            await self.login_history_collection.create_index([("user_email", 1)])
            await self.login_history_collection.create_index([("timestamp", -1)])
            logger.info("Auth indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating auth indexes: {str(e)}")

    async def _ensure_admin_user(self):
        """Ensure admin user exists"""
        try:
            admin_email = os.getenv('ADMIN_EMAIL', 'admin@fairnessfactor.com')
            admin_password = os.getenv('ADMIN_PASSWORD', '1122Kryptic$')
            
            admin_exists = await self.users_collection.find_one({'email': admin_email})
            if not admin_exists:
                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), salt)
                
                await self.users_collection.insert_one({
                    'email': admin_email,
                    'password': hashed_password,
                    'name': 'Admin User',
                    'role': 'admin',
                    'created_at': datetime.now(),
                    'created_by': 'system',
                    'last_login': None,
                    'status': 'active'
                })
                logger.info("Created default admin user")
        except Exception as e:
            logger.error(f"Error ensuring admin user: {str(e)}")

    async def verify_email_domain(self, email: str) -> bool:
        """Verify email belongs to Fairness Factor domain."""
        try:
            email = email.lower()
            allowed_domains = ['fairnessfactor.com']
            domain = email.split('@')[-1]
            return domain in allowed_domains
        except Exception as e:
            logger.error(f"Email verification error: {str(e)}")
            return False

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
            hashed = await loop.run_in_executor(
                None, 
                bcrypt.hashpw, 
                password.encode('utf-8'), 
                salt
            )

            await self.users_collection.insert_one({
                'email': email.lower(),
                'password': hashed,
                'name': name,
                'role': role,
                'created_at': datetime.now(),
                'created_by': added_by,
                'last_login': None,
                'status': 'active',
                'failed_login_attempts': 0,
                'last_password_change': datetime.now()
            })
            
            # Log user creation
            await self.db.user_activity.insert_one({
                'user_email': email.lower(),
                'activity_type': 'user_created',
                'created_by': added_by,
                'timestamp': datetime.now()
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
                await self._log_failed_login(email, 'user_not_found')
                return None

            if user.get('status') != 'active':
                await self._log_failed_login(email, 'account_inactive')
                return None

            # Check failed login attempts
            if user.get('failed_login_attempts', 0) >= 5:
                last_attempt = user.get('last_failed_login')
                if last_attempt and (datetime.now() - last_attempt).total_seconds() < 1800:  # 30 minutes
                    await self._log_failed_login(email, 'account_locked')
                    return None

            # Get current event loop
            loop = asyncio.get_running_loop()

            stored_password = user['password']
            if isinstance(stored_password, str):
                stored_password = stored_password.encode('utf-8')

            # Run password check in executor
            is_valid = await loop.run_in_executor(
                None,
                bcrypt.checkpw,
                password.encode('utf-8'),
                stored_password
            )

            if is_valid:
                # Reset failed login attempts
                await self.users_collection.update_one(
                    {'email': email.lower()},
                    {
                        '$set': {
                            'failed_login_attempts': 0,
                            'last_login': datetime.now()
                        }
                    }
                )

                # Generate token
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
                    'success': True,
                    'ip_address': None,  # Could be added if needed
                    'user_agent': None   # Could be added if needed
                })

                return token

            # Handle failed login
            await self._handle_failed_login(email)
            return None

        except Exception as e:
            logger.error(f"Login error for {email}: {str(e)}")
            return None

    async def _handle_failed_login(self, email: str):
        """Handle failed login attempt"""
        try:
            await self.users_collection.update_one(
                {'email': email.lower()},
                {
                    '$inc': {'failed_login_attempts': 1},
                    '$set': {'last_failed_login': datetime.now()}
                }
            )
            await self._log_failed_login(email, 'invalid_password')
        except Exception as e:
            logger.error(f"Error handling failed login: {str(e)}")

    async def _log_failed_login(self, email: str, reason: str):
        """Log failed login attempt"""
        try:
            await self.login_history_collection.insert_one({
                'user_email': email,
                'timestamp': datetime.now(),
                'success': False,
                'reason': reason
            })
        except Exception as e:
            logger.error(f"Error logging failed login: {str(e)}")

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
            if user and user.get('status') == 'active':
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

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        try:
            cursor = self.users_collection.find(
                {},
                {
                    'password': 0,
                    'failed_login_attempts': 0,
                    'last_failed_login': 0
                }
            ).sort('created_at', -1)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error getting users: {str(e)}")
            return []

    async def delete_user(self, email: str) -> bool:
        """Delete a user"""
        try:
            # Don't allow deletion of the last admin user
            if email.lower() == os.getenv('ADMIN_EMAIL', 'admin@fairnessfactor.com').lower():
                admin_count = await self.users_collection.count_documents({'role': 'admin'})
                if admin_count <= 1:
                    raise ValueError("Cannot delete the last admin user")

            result = await self.users_collection.delete_one({'email': email.lower()})
            
            if result.deleted_count > 0:
                # Log user deletion
                await self.db.user_activity.insert_one({
                    'user_email': email.lower(),
                    'activity_type': 'user_deleted',
                    'deleted_by': st.session_state.user['email'],
                    'timestamp': datetime.now()
                })
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting user {email}: {str(e)}")
            return False

    async def update_user(
        self, 
        email: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update user information"""
        try:
            # Don't allow role change for the last admin
            if 'role' in updates and email.lower() == os.getenv('ADMIN_EMAIL').lower():
                admin_count = await self.users_collection.count_documents({'role': 'admin'})
                if admin_count <= 1 and updates['role'] != 'admin':
                    raise ValueError("Cannot change role of the last admin user")

            result = await self.users_collection.update_one(
                {'email': email.lower()},
                {'$set': {
                    **updates,
                    'updated_at': datetime.now()
                }}
            )
            
            if result.modified_count > 0:
                # Log user update
                await self.db.user_activity.insert_one({
                    'user_email': email.lower(),
                    'activity_type': 'user_updated',
                    'updated_by': st.session_state.user['email'],
                    'updates': updates,
                    'timestamp': datetime.now()
                })
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating user {email}: {str(e)}")
            return False

    async def change_password(
        self, 
        email: str, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """Change user password"""
        try:
            user = await self.users_collection.find_one({'email': email.lower()})
            if not user:
                return False

            # Get current event loop
            loop = asyncio.get_running_loop()

            # Verify current password
            is_valid = await loop.run_in_executor(
                None,
                bcrypt.checkpw,
                current_password.encode('utf-8'),
                user['password']
            )

            if not is_valid:
                return False

            # Hash new password
            salt = await loop.run_in_executor(None, bcrypt.gensalt)
            new_hash = await loop.run_in_executor(
                None,
                bcrypt.hashpw,
                new_password.encode('utf-8'),
                salt
            )

            # Update password
            result = await self.users_collection.update_one(
                {'email': email.lower()},
                {
                    '$set': {
                        'password': new_hash,
                        'last_password_change': datetime.now()
                    }
                }
            )

            if result.modified_count > 0:
                # Log password change
                await self.db.user_activity.insert_one({
                    'user_email': email.lower(),
                    'activity_type': 'password_changed',
                    'timestamp': datetime.now()
                })
                return True
            return False

        except Exception as e:
            logger.error(f"Error changing password for {email}: {str(e)}")
            return False

    async def get_user_activity(
        self, 
        email: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user activity history"""
        try:
            cursor = self.db.user_activity.find(
                {'user_email': email.lower()}
            ).sort('timestamp', -1).limit(limit)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error retrieving user activity: {str(e)}")
            return []

    async def get_login_history(
        self, 
        email: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get user login history"""
        try:
            cursor = self.login_history_collection.find(
                {'user_email': email.lower()}
            ).sort('timestamp', -1).limit(limit)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error retrieving login history: {str(e)}")
            return []