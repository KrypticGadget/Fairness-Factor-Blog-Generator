# auth/permissions.py
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class PermissionHandler:
    def __init__(self, db):
        self.db = db
        self.default_permissions = {
            'user': [
                'read:content',
                'write:content',
                'edit:own_content'
            ],
            'admin': ['*']  # All permissions
        }

    async def get_user_permissions(self, user_id: str) -> List[str]:
        """Get user's permissions"""
        try:
            user = await self.db.users.find_one({'_id': user_id})
            if not user:
                return []
                
            role = user.get('role', 'user')
            custom_permissions = user.get('permissions', [])
            
            # Combine default role permissions with custom permissions
            permissions = set(self.default_permissions.get(role, []))
            permissions.update(custom_permissions)
            
            return list(permissions)
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {str(e)}")
            return []

    async def check_permission(self, user_id: str, required_permission: str) -> bool:
        """Check if user has specific permission"""
        try:
            permissions = await self.get_user_permissions(user_id)
            
            # Admin has all permissions
            if '*' in permissions:
                return True
                
            return required_permission in permissions
            
        except Exception as e:
            logger.error(f"Error checking permission: {str(e)}")
            return False

    async def add_permission(self, user_id: str, permission: str) -> bool:
        """Add permission to user"""
        try:
            result = await self.db.users.update_one(
                {'_id': user_id},
                {'$addToSet': {'permissions': permission}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error adding permission: {str(e)}")
            return False

    async def remove_permission(self, user_id: str, permission: str) -> bool:
        """Remove permission from user"""
        try:
            result = await self.db.users.update_one(
                {'_id': user_id},
                {'$pull': {'permissions': permission}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error removing permission: {str(e)}")
            return False