# scripts/rotate_jwt_key.py
import asyncio
import os
from dotenv import load_dotenv
from utils.mongo_manager import AsyncMongoManager
from utils.key_rotation import JWTKeyRotator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def rotate_jwt_key():
    """Rotate JWT key and update environment"""
    try:
        # Initialize MongoDB connection
        mongo_manager = AsyncMongoManager()
        async with mongo_manager.get_connection() as (_, db, _):
            key_rotator = JWTKeyRotator(db)
            
            # Rotate key
            new_key_data = await key_rotator.rotate_key()
            
            # Update .env file
            env_path = '.env'
            temp_env_path = '.env.temp'
            
            with open(env_path, 'r') as env_file:
                env_contents = env_file.readlines()
            
            with open(temp_env_path, 'w') as temp_file:
                for line in env_contents:
                    if line.startswith('JWT_SECRET_KEY='):
                        temp_file.write(f'JWT_SECRET_KEY={new_key_data["key"]}\n')
                    else:
                        temp_file.write(line)
            
            # Replace old .env with new one
            os.replace(temp_env_path, env_path)
            
            # Clean up expired keys
            deleted_count = await key_rotator.cleanup_expired_keys()
            
            logger.info(f"JWT key rotated successfully. Expires: {new_key_data['expires_at']}")
            logger.info(f"Cleaned up {deleted_count} expired keys")
            
    except Exception as e:
        logger.error(f"Error rotating JWT key: {e}")
        raise

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(rotate_jwt_key())