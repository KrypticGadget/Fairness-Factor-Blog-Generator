# utils/data_handlers.py
from datetime import datetime
from bson import ObjectId
import logging
from typing import Optional, List, Dict, Any
import pandas as pd
import io
import asyncio

logger = logging.getLogger(__name__)

class AsyncBlogContentHandler:
    def __init__(self, db):
        self.db = db
        self.collection = db.blog_content

    async def save_research(self, user_email: str, document_contents: List[str], analysis: str) -> str:
        try:
            document = {
                'type': 'research',
                'user_email': user_email,
                'document_contents': document_contents,
                'analysis': analysis,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            result = await self.collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving research: {e}")
            raise

    async def save_article_draft(
        self, 
        user_email: str, 
        research_id: str, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> str:
        try:
            document = {
                'type': 'draft',
                'user_email': user_email,
                'research_id': research_id,
                'content': content,
                'metadata': metadata,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            result = await self.collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving article draft: {e}")
            raise

    async def get_user_content(
        self, 
        user_email: str, 
        content_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        try:
            query = {'user_email': user_email}
            if content_type:
                query['type'] = content_type
            cursor = self.collection.find(query).sort('created_at', -1).limit(limit)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error retrieving user content: {e}")
            return []

    async def update_content(
        self, 
        content_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        try:
            updates['updated_at'] = datetime.now()
            result = await self.collection.update_one(
                {'_id': ObjectId(content_id)},
                {'$set': updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating content: {e}")
            return False

class AsyncFileHandler:
    def __init__(self, fs):
        self.fs = fs

    async def save_file(
        self, 
        filename: str, 
        file_data: bytes, 
        metadata: Dict[str, Any]
    ) -> str:
        try:
            file_id = await self.fs.upload_from_stream(
                filename,
                file_data,
                metadata={
                    **metadata,
                    'uploaded_at': datetime.now()
                }
            )
            return str(file_id)
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise

    async def get_file(self, file_id: str) -> Optional[bytes]:
        try:
            grid_out = await self.fs.open_download_stream(ObjectId(file_id))
            return await grid_out.read()
        except Exception as e:
            logger.error(f"Error retrieving file: {e}")
            return None

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
        try:
            document = {
                'user_email': user_email,
                'activity_type': activity_type,
                'metadata': metadata,
                'timestamp': datetime.now()
            }
            await self.collection.insert_one(document)
        except Exception as e:
            logger.error(f"Error logging activity: {e}")

    async def get_user_analytics(
        self, 
        user_email: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        try:
            pipeline = [
                {'$match': {
                    'user_email': user_email,
                    **({'timestamp': {
                        '$gte': start_date,
                        '$lte': end_date
                    }} if start_date and end_date else {})
                }},
                {'$group': {
                    '_id': '$activity_type',
                    'count': {'$sum': 1},
                    'last_activity': {'$max': '$timestamp'}
                }}
            ]
            cursor = self.collection.aggregate(pipeline)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error retrieving analytics: {e}")
            return []