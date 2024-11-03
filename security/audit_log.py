# security/audit_log.py
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AuditLogger:
    def __init__(self, db):
        self.db = db
        self.collection = db.audit_logs
        
    async def log_event(
        self,
        user_id: str,
        action: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Log security-relevant events"""
        try:
            await self.collection.insert_one({
                'user_id': user_id,
                'action': action,
                'details': details,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'timestamp': datetime.utcnow()
            })
            return True
        except Exception as e:
            logger.error(f"Error logging audit event: {str(e)}")
            return False