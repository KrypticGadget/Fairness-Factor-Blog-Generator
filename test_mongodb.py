import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection():
    """Test MongoDB connection"""
    try:
        load_dotenv()
        uri = os.getenv('MONGODB_URI')
        
        if not uri:
            logger.error("MongoDB URI not found in environment variables")
            return False
            
        client = AsyncIOMotorClient(uri)
        
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
        logger.error(f"❌ Connection error: {str(e)}")
        return False
    
    finally:
        if 'client' in locals():
            client.close()

# For direct script execution
if __name__ == "__main__":
    asyncio.run(test_connection())