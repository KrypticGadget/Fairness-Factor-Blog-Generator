# utils/mongo_manager.py
import os
import motor.motor_asyncio
import asyncio
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
import logging
from typing import Tuple, Any

logger = logging.getLogger(__name__)

def ensure_event_loop():
    """Ensure an event loop exists in the current thread"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

class AsyncMongoManager:
    def __init__(self):
        self.uri = os.getenv('MONGODB_URI')
        if not self.uri:
            raise ValueError("MONGODB_URI not found in environment variables")

        # Ensure event loop exists
        ensure_event_loop()
        
        # Initialize client
        self.client = motor.motor_asyncio.AsyncIOMotorClient(self.uri)
        self.db = self.client.fairness_factor_blog

    async def get_fs(self):
        """Get GridFS bucket lazily"""
        if not hasattr(self, 'fs'):
            self.fs = AsyncIOMotorGridFSBucket(self.db)
        return self.fs

    async def _ensure_index(self, collection, keys, **kwargs):
        """Safely create an index if it doesn't exist"""
        try:
            # Drop any existing index with the same key pattern
            await collection.drop_index([(k, v) for k, v in keys])
        except:
            # Ignore errors from dropping non-existent indexes
            pass

        try:
            # Create new index
            await collection.create_index([(k, v) for k, v in keys], **kwargs)
        except Exception as e:
            logger.warning(f"Error creating index on {collection.name}: {str(e)}")

    async def initialize(self):
        """Initialize database connection and indexes"""
        try:
            # Test connection
            await self.client.admin.command('ping')
            
            # Create indexes safely
            await self._ensure_index(self.db.users, [('email', 1)], unique=True, name='unique_email')
            await self._ensure_index(self.db.blog_content, [('user_email', 1)], name='blog_user_email')
            await self._ensure_index(self.db.blog_content, [('created_at', -1)], name='blog_created_at')
            await self._ensure_index(self.db.analytics, [('timestamp', -1)], name='analytics_timestamp')

            # Initialize GridFS
            fs = await self.get_fs()
            
            logger.info("Successfully connected to MongoDB and initialized indexes")
            return self.client, self.db, fs
            
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB: {e}")
            await self.close()
            raise

    async def close(self):
        """Close database connection"""
        if hasattr(self, 'client'):
            self.client.close()

class AsyncDatabaseSession:
    def __init__(self):
        self.manager = None

    async def __aenter__(self) -> Tuple[Any, Any, Any]:
        # Create manager and initialize connection
        self.manager = AsyncMongoManager()
        return await self.manager.initialize()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.manager:
            await self.manager.close()

def get_db_session() -> AsyncDatabaseSession:
    """Get database session"""
    return AsyncDatabaseSession()