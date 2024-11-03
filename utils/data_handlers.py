# utils/data_handlers.py
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
from bson import ObjectId

logger = logging.getLogger(__name__)

class AsyncBlogContentHandler:
    def __init__(self, db):
        self.db = db
        self.collection = db.blog_content

    async def save_content(
        self,
        user_email: str,
        content_type: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """Save blog content"""
        try:
            document = {
                'user_email': user_email,
                'type': content_type,
                'content': content,
                'metadata': metadata,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            result = await self.collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving content: {str(e)}")
            return None

    async def get_user_content(
        self,
        user_email: str,
        content_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get user's content"""
        try:
            query = {'user_email': user_email}
            if content_type:
                query['type'] = content_type
            
            cursor = self.collection.find(query).sort('created_at', -1).limit(limit)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error retrieving content: {str(e)}")
            return []

    async def update_content(
        self,
        content_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update content"""
        try:
            updates['updated_at'] = datetime.utcnow()
            result = await self.collection.update_one(
                {'_id': ObjectId(content_id)},
                {'$set': updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating content: {str(e)}")
            return False

class AsyncAnalyticsHandler:
    def __init__(self, db):
        self.db = db
        self.collection = db.analytics

    async def log_activity(
        self,
        user_email: str,
        activity_type: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Log user activity"""
        try:
            await self.collection.insert_one({
                'user_email': user_email,
                'activity_type': activity_type,
                'metadata': metadata,
                'timestamp': datetime.utcnow()
            })
        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")

    async def get_user_analytics(
        self,
        user_email: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get user analytics"""
        try:
            query = {'user_email': user_email}
            if start_date and end_date:
                query['timestamp'] = {
                    '$gte': start_date,
                    '$lte': end_date
                }
            
            cursor = self.collection.find(query).sort('timestamp', -1)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error retrieving analytics: {str(e)}")
            return []