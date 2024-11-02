import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import quote_plus
import logging
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mongodb_connection():
    """Test MongoDB connection with updated URI format"""
    try:
        # Connection parameters
        username = "KrypticGadget"
        password = "1629609804"  # In production, get from environment
        cluster = "fairness-factor-cluster.p0tsa.mongodb.net"
        
        # Properly escape credentials
        username = quote_plus(username)
        password = quote_plus(password)
        
        # Construct URI with updated format
        uri = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority&appName=fairness-factor-cluster"
        
        logger.info("Testing connection with new URI format...")
        client = AsyncIOMotorClient(uri)
        
        # Test basic connection
        logger.info("Testing basic connection...")
        await client.admin.command('ping')
        logger.info("✅ Basic connection successful!")
        
        # Select database
        db = client.fairness_factor_blog
        logger.info("Selecting database: fairness_factor_blog")
        
        # Test database operations
        logger.info("Testing database operations...")
        try:
            # Test read
            collections = await db.list_collection_names()
            logger.info(f"📚 Existing collections: {collections}")
            
            # Test write
            result = await db.connection_test.insert_one({"test": "data"})
            logger.info("✅ Write test successful")
            await db.connection_test.delete_one({"test": "data"})
            logger.info("✅ Delete test successful")
            
            # Test index creation
            await db.connection_test.create_index([("test_field", 1)])
            logger.info("✅ Index creation successful")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database operation failed: {str(e)}")
            logger.info("\nTroubleshooting steps:")
            logger.info("1. Verify user permissions in MongoDB Atlas")
            logger.info("2. Check database name is correct")
            logger.info("3. Ensure IP whitelist includes your current IP")
            return False
            
    except Exception as e:
        logger.error(f"❌ Connection failed: {str(e)}")
        return False
        
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    asyncio.run(test_mongodb_connection())