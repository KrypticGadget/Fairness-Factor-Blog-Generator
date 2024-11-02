# utils/mongo_manager.py
import os
import motor.motor_asyncio
import asyncio
from typing import Optional, Tuple, Any
from threading import Lock
import logging
import gridfs
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

logger = logging.getLogger(__name__)

class AsyncMongoManager:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AsyncMongoManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.client = None
        self.db = None
        self.fs = None
        
        # Remove this line
        # asyncio.create_task(self._connect())
        
        # Instead, initialize connection in an async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._connect())

    async def _connect(self) -> None:
        """Establish async connection to MongoDB"""
        try:
            uri = os.getenv('MONGODB_URI')
            if not uri:
                raise ValueError("MONGODB_URI not found in environment variables")

            self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
            self.db = self.client.fairness_factor_blog
            self.fs = AsyncIOMotorGridFSBucket(self.db)
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")

            # Create indexes
            await self._create_indexes()

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def _create_indexes(self):
        """Create necessary indexes"""
        try:
            # Blog content indexes
            await self.db.blog_content.create_index([("user_email", 1)])
            await self.db.blog_content.create_index([("created_at", -1)])
            await self.db.blog_content.create_index([("type", 1)])

            # User session indexes
            await self.db.user_sessions.create_index([("user_email", 1)])
            await self.db.user_sessions.create_index([("created_at", -1)])

            # Analytics indexes
            await self.db.analytics.create_index([("user_email", 1)])
            await self.db.analytics.create_index([("timestamp", -1)])
            await self.db.analytics.create_index([("activity_type", 1)])

            # LLM logs indexes
            await self.db.llm_logs.create_index([("user_email", 1)])
            await self.db.llm_logs.create_index([("timestamp", -1)])

            logger.info("Successfully created MongoDB indexes")

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise

    async def get_connection(self):
        """Get async database connection"""
        if not self.client:
            await self._connect()
        return self.client, self.db

    async def get_fs(self):
        """Get GridFS bucket"""
        if not self.fs:
            await self._connect()
        return self.fs

    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.fs = None

class AsyncDatabaseSession:
    """Async context manager for database sessions"""
    
    def __init__(self):
        self.mongo_manager = AsyncMongoManager()
        self.client = None
        self.db = None
        self.fs = None

    async def __aenter__(self):
        self.client, self.db = await self.mongo_manager.get_connection()
        self.fs = await self.mongo_manager.get_fs()
        return self.client, self.db, self.fs

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Connection handled by MongoManager
        pass

def get_db_session():
    """Get database session for use in application"""
    return AsyncDatabaseSession()