# utils/session_manager.py

from datetime import datetime
import logging
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

logger = logging.getLogger(__name__)

class AsyncSessionManager:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.sessions_collection = db.sessions

    async def create_session(
        self, 
        user_email: str, 
        session_data: Dict[str, Any]
    ) -> Optional[str]:
        try:
            result = await self.sessions_collection.insert_one({
                'user_email': user_email,
                'data': session_data,
                'created_at': datetime.now(),
                'last_accessed': datetime.now(),
                'active': True
            })
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            return None

    async def update_session(
        self, 
        session_id: str, 
        session_data: Dict[str, Any]
    ) -> bool:
        try:
            result = await self.sessions_collection.update_one(
                {'_id': ObjectId(session_id)},
                {
                    '$set': {
                        'data': session_data,
                        'last_accessed': datetime.now()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating session: {str(e)}")
            return False

    async def end_session(self, session_id: str) -> bool:
        try:
            result = await self.sessions_collection.update_one(
                {'_id': ObjectId(session_id)},
                {
                    '$set': {
                        'active': False,
                        'ended_at': datetime.now()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error ending session: {str(e)}")
            return False

    async def get_active_sessions(self, user_email: str) -> List[Dict[str, Any]]:
        try:
            cursor = self.sessions_collection.find({
                'user_email': user_email,
                'active': True
            }).sort('last_accessed', -1)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error retrieving active sessions: {str(e)}")
            return []

    async def cleanup_expired_sessions(self, expiry_hours: int = 24) -> int:
        """Clean up expired sessions"""
        try:
            expiry_time = datetime.now() - timedelta(hours=expiry_hours)
            result = await self.sessions_collection.update_many(
                {
                    'active': True,
                    'last_accessed': {'$lt': expiry_time}
                },
                {
                    '$set': {
                        'active': False,
                        'ended_at': datetime.now()
                    }
                }
            )
            return result.modified_count
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
            return 0