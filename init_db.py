import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import bcrypt
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_collections(uri: str):
    """Initialize database collections with required indexes"""
    try:
        client = AsyncIOMotorClient(uri)
        db = client.fairness_factor_blog
        
        # Required collections
        collections = {
            'users': [
                [('email', 1)],  # Unique index on email
                [('created_at', -1)]
            ],
            'blog_content': [
                [('user_email', 1)],
                [('type', 1)],
                [('created_at', -1)]
            ],
            'analytics': [
                [('user_email', 1)],
                [('activity_type', 1)],
                [('timestamp', -1)]
            ],
            'sessions': [
                [('user_email', 1)],
                [('active', 1)],
                [('created_at', -1)]
            ],
            'jwt_keys': [
                [('created_at', -1)],
                [('is_active', 1)]
            ]
        }
        
        # Create collections and indexes
        for coll_name, indexes in collections.items():
            logger.info(f"Setting up collection: {coll_name}")
            
            # Create collection if it doesn't exist
            if coll_name not in await db.list_collection_names():
                await db.create_collection(coll_name)
            
            # Create indexes
            for index in indexes:
                await db[coll_name].create_index(index)
        
        # Create default admin user if not exists
        admin_email = 'zack@fairnessfactor.com'
        if not await db.users.find_one({'email': admin_email}):
            salt = bcrypt.gensalt()
            password = "1122Kryptic$"  # Change this in production!
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            
            await db.users.insert_one({
                'email': admin_email,
                'password': hashed,
                'name': 'Admin User',
                'role': 'admin',
                'created_at': datetime.now(),
                'created_by': 'system'
            })
            logger.info("Created default admin user")
        
        logger.info("✅ Database initialization complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        return False
        
    finally:
        client.close()

if __name__ == "__main__":
    # Get MongoDB URI from environment or use default
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    uri = os.getenv('MONGODB_URI')
    
    if not uri:
        logger.error("MongoDB URI not found in environment variables")
        exit(1)
    
    asyncio.run(init_collections(uri))