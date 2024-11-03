# database/migrations/001_initial_setup.py
from datetime import datetime
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
from config import settings
import logging

logger = logging.getLogger(__name__)

async def run_migration(db):
    """Run initial database setup"""
    try:
        # Create collections if they don't exist
        collections = [
            'users',
            'sessions',
            'audit_logs',
            'blog_content',
            'analytics',
            'prompts'
        ]
        
        for collection in collections:
            if collection not in await db.list_collection_names():
                await db.create_collection(collection)
                logger.info(f"Created collection: {collection}")

        # Create admin user if it doesn't exist
        admin_email = settings.app.ADMIN_EMAIL
        admin_exists = await db.users.find_one({'email': admin_email})
        
        if not admin_exists:
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(
                settings.app.ADMIN_PASSWORD.encode('utf-8'),
                salt
            )
            
            await db.users.insert_one({
                'email': admin_email,
                'name': 'Admin User',
                'password_hash': hashed_password,
                'role': 'admin',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'status': 'active',
                'permissions': ['*'],
                'two_factor_enabled': False
            })
            logger.info("Created admin user")

        logger.info("Initial migration completed successfully")
        return True

    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        return False

if __name__ == "__main__":
    async def main():
        client = AsyncIOMotorClient(settings.database.MONGODB_URI)
        db = client[settings.database.DATABASE_NAME]
        
        success = await run_migration(db)
        if success:
            print("Migration completed successfully")
        else:
            print("Migration failed")
        
        client.close()

    asyncio.run(main())