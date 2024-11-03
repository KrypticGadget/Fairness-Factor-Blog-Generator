# database/mongo_manager.py
import motor.motor_asyncio
import asyncio
from typing import Optional, Tuple, Any
import logging
from config import settings

logger = logging.getLogger(__name__)

class AsyncMongoManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.uri = settings.database.MONGODB_URI
            self.client = None
            self.db = None
            self.initialized = False

    async def initialize(self) -> Tuple[Any, Any]:
        """Initialize database connection"""
        if not self.initialized:
            try:
                # Create client
                self.client = motor.motor_asyncio.AsyncIOMotorClient(
                    self.uri,
                    maxPoolSize=settings.database.MAX_CONNECTIONS,
                    minPoolSize=settings.database.MIN_CONNECTIONS
                )
                
                # Get database
                self.db = self.client[settings.database.DATABASE_NAME]
                
                # Test connection
                await self.client.admin.command('ping')
                
                # Create indexes
                await self._create_indexes()
                
                self.initialized = True
                logger.info("MongoDB connection initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize MongoDB: {str(e)}")
                raise

        return self.client, self.db

    async def _create_indexes(self):
        """Create necessary database indexes"""
        try:
            # Users collection indexes
            await self.db.users.create_index([("email", 1)], unique=True)
            await self.db.users.create_index([("created_at", -1)])

            # Sessions collection indexes
            await self.db.sessions.create_index([("user_id", 1)])
            await self.db.sessions.create_index([("access_token", 1)])
            await self.db.sessions.create_index([("refresh_token", 1)])
            await self.db.sessions.create_index([("expires_at", 1)])

            # Audit logs collection indexes
            await self.db.audit_logs.create_index([("user_id", 1)])
            await self.db.audit_logs.create_index([("timestamp", -1)])
            await self.db.audit_logs.create_index([("action", 1)])

            logger.info("Database indexes created successfully")

        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")
            raise

    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            self.initialized = False
            logger.info("MongoDB connection closed")

class AsyncDatabaseSession:
    """Async context manager for database sessions"""
    
    def __init__(self):
        self.manager = AsyncMongoManager()

    async def __aenter__(self) -> Tuple[Any, Any]:
        return await self.manager.initialize()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.manager.close()

def get_db_session() -> AsyncDatabaseSession:
    """Get database session"""
    return AsyncDatabaseSession()