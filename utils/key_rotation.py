# utils/key_rotation.py
import secrets
import jwt
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class JWTKeyRotator:
    def __init__(self, db):
        self.db = db
        self.keys_collection = db.jwt_keys

    async def generate_new_key(self) -> str:
        """Generate a new JWT secret key"""
        return secrets.token_hex(32)

    async def store_key(self, key: str, expiry_days: int = 30) -> str:
        """Store a new JWT key with expiration"""
        try:
            key_doc = {
                'key': key,
                'created_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(days=expiry_days),
                'is_active': True
            }
            result = await self.keys_collection.insert_one(key_doc)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error storing JWT key: {e}")
            raise

    async def rotate_key(self, expiry_days: int = 30) -> Dict[str, Any]:
        """Generate and store a new key while deprecating the old one"""
        try:
            # Generate new key
            new_key = await self.generate_new_key()
            
            # Store new key
            new_key_id = await self.store_key(new_key, expiry_days)
            
            # Deactivate old keys
            await self.keys_collection.update_many(
                {'_id': {'$ne': new_key_id}},
                {'$set': {'is_active': False}}
            )
            
            return {
                'key_id': new_key_id,
                'key': new_key,
                'expires_at': datetime.utcnow() + timedelta(days=expiry_days)
            }
        except Exception as e:
            logger.error(f"Error rotating JWT key: {e}")
            raise

    async def get_active_key(self) -> Optional[str]:
        """Get the current active JWT key"""
        try:
            key_doc = await self.keys_collection.find_one(
                {
                    'is_active': True,
                    'expires_at': {'$gt': datetime.utcnow()}
                }
            )
            return key_doc['key'] if key_doc else None
        except Exception as e:
            logger.error(f"Error retrieving active JWT key: {e}")
            return None

    async def cleanup_expired_keys(self) -> int:
        """Remove expired keys from the database"""
        try:
            result = await self.keys_collection.delete_many(
                {'expires_at': {'$lt': datetime.utcnow()}}
            )
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up expired JWT keys: {e}")
            return 0