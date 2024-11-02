# E:\Kryptic Gadget Github Repos\Fairness-Factor-Blog-Generator\test_mongodb.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection():
    client = None
    try:
        # Validate config
        Config.validate()
        
        # Create client
        client = AsyncIOMotorClient(Config.MONGODB_URI)
        
        # Test connection
        await client.admin.command('ping')
        logger.info("✅ Successfully connected to MongoDB!")
        
        # Get database
        db = client.fairness_factor_blog
        
        # List collections
        collections = await db.list_collection_names()
        logger.info(f"📚 Available collections: {collections}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error connecting to MongoDB: {str(e)}")
        return False
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    asyncio.run(test_connection())