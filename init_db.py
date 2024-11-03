# init_db.py
import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import bcrypt
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_database():
    """Initialize database with required collections and indexes"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(settings.database.MONGODB_URI)
        db = client[settings.database.DATABASE_NAME]
        
        # Create collections
        collections = [
            'users',
            'sessions',
            'blog_content',
            'analytics',
            'audit_logs',
            'rate_limits'
        ]
        
        for collection in collections:
            if collection not in await db.list_collection_names():
                await db.create_collection(collection)
                logger.info(f"Created collection: {collection}")
        
        # Create indexes
        await db.users.create_index([("email", 1)], unique=True)
        await db.sessions.create_index([("user_email", 1)])
        await db.sessions.create_index([("created_at", -1)])
        await db.blog_content.create_index([("user_email", 1)])
        await db.analytics.create_index([("timestamp", -1)])
        await db.audit_logs.create_index([("timestamp", -1)])
        await db.rate_limits.create_index([("timestamp", -1)])
        
        # Create admin user if not exists
        admin_email = settings.app.ADMIN_EMAIL
        admin_exists = await db.users.find_one({"email": admin_email})
        
        if not admin_exists:
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(
                settings.app.ADMIN_PASSWORD.encode('utf-8'),
                salt
            )
            
            await db.users.insert_one({
                "email": admin_email,
                "name": "Admin User",
                "password_hash": hashed_password,
                "role": "admin",
                "created_at": datetime.utcnow(),
                "status": "active",
                "two_factor_enabled": False
            })
            logger.info("Created admin user")
        
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        return False
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(init_database())