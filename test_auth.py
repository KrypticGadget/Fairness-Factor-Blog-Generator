import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import quote_plus
import logging
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_auth_levels():
    """Test MongoDB authentication with different permission levels"""
    try:
        load_dotenv()
        uri = os.getenv('MONGODB_URI')
        
        if not uri:
            logger.error("MongoDB URI not found in environment variables")
            return False
            
        logger.info("Testing connection with provided URI...")
        logger.info(f"URI format check: {uri.split('://')[0]}://<credentials>@{uri.split('@')[1]}")
        
        client = AsyncIOMotorClient(uri)
        db = client.fairness_factor_blog
        
        # Test 1: Basic Connection
        logger.info("\nTest 1: Testing basic connection...")
        try:
            await client.admin.command('ping')
            logger.info("✅ Basic connection successful")
        except Exception as e:
            logger.error(f"❌ Basic connection failed: {str(e)}")
            return False
            
        # Test 2: Read Permission
        logger.info("\nTest 2: Testing read permission...")
        try:
            collections = await db.list_collection_names()
            logger.info(f"✅ Read permission verified. Found collections: {collections}")
        except Exception as e:
            logger.error(f"❌ Read permission failed: {str(e)}")
            
        # Test 3: Write Permission
        logger.info("\nTest 3: Testing write permission...")
        try:
            result = await db.test_collection.insert_one({"test": "data"})
            logger.info("✅ Write permission verified")
            await db.test_collection.delete_one({"test": "data"})
        except Exception as e:
            logger.error(f"❌ Write permission failed: {str(e)}")
            
        # Test 4: Index Creation
        logger.info("\nTest 4: Testing index creation permission...")
        try:
            await db.test_collection.create_index([("test_field", 1)])
            logger.info("✅ Index creation permission verified")
        except Exception as e:
            logger.error(f"❌ Index creation failed: {str(e)}")
            
        logger.info("\nPermission test summary:")
        logger.info("Please ensure your MongoDB user has:")
        logger.info("1. readWrite role on the database")
        logger.info("2. dbAdmin role for index management")
        logger.info("\nTo fix permissions in MongoDB Atlas:")
        logger.info("1. Go to Database Access")
        logger.info("2. Edit user 'KrypticGadget'")
        logger.info("3. Add 'readWrite' and 'dbAdmin' roles for database 'fairness_factor_blog'")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Overall test failed: {str(e)}")
        return False
        
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    asyncio.run(test_auth_levels())