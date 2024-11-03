# security/rate_limiter.py
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging
from config import settings

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, db):
        self.db = db
        self.collection = db.rate_limits
        self.max_requests = settings.security.RATE_LIMIT_REQUESTS
        self.period = settings.security.RATE_LIMIT_PERIOD

    async def is_rate_limited(self, key: str) -> bool:
        """Check if request should be rate limited"""
        try:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=self.period)
            
            # Get request count in window
            count = await self.collection.count_documents({
                'key': key,
                'timestamp': {'$gte': window_start}
            })
            
            return count >= self.max_requests
            
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            return False

    async def add_request(self, key: str) -> None:
        """Record new request"""
        try:
            await self.collection.insert_one({
                'key': key,
                'timestamp': datetime.utcnow()
            })
            
        except Exception as e:
            logger.error(f"Error recording request: {str(e)}")

    async def cleanup_old_records(self) -> None:
        """Remove expired rate limit records"""
        try:
            window_start = datetime.utcnow() - timedelta(seconds=self.period)
            await self.collection.delete_many({
                'timestamp': {'$lt': window_start}
            })
            
        except Exception as e:
            logger.error(f"Error cleaning up rate limit records: {str(e)}")
