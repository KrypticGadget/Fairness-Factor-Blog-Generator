# auth/two_factor.py
import pyotp
import base64
from typing import Optional, Dict, Any
import logging
from cryptography.fernet import Fernet
from config import settings

logger = logging.getLogger(__name__)

class TwoFactorAuth:
    def __init__(self, db):
        self.db = db
        self.fernet = Fernet(settings.security.TWO_FACTOR_ENCRYPTION_KEY.encode())

    async def generate_secret(self) -> str:
        """Generate new TOTP secret"""
        return pyotp.random_base32()

    async def encrypt_secret(self, secret: str) -> str:
        """Encrypt 2FA secret"""
        try:
            return self.fernet.encrypt(secret.encode()).decode()
        except Exception as e:
            logger.error(f"Error encrypting 2FA secret: {str(e)}")
            raise

    async def decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt 2FA secret"""
        try:
            return self.fernet.decrypt(encrypted_secret.encode()).decode()
        except Exception as e:
            logger.error(f"Error decrypting 2FA secret: {str(e)}")
            raise

    async def enable_2fa(self, user_id: str) -> Dict[str, str]:
        """Enable 2FA for user"""
        try:
            secret = await self.generate_secret()
            encrypted_secret = await self.encrypt_secret(secret)
            
            await self.db.users.update_one(
                {'_id': user_id},
                {
                    '$set': {
                        'two_factor_enabled': True,
                        'two_factor_secret': encrypted_secret
                    }
                }
            )
            
            return {
                'secret': secret,
                'qr_code': pyotp.totp.TOTP(secret).provisioning_uri(
                    name="Fairness Factor",
                    issuer_name="Fairness Factor Blog Generator"
                )
            }
            
        except Exception as e:
            logger.error(f"Error enabling 2FA: {str(e)}")
            raise

    async def verify_2fa(self, user_id: str, token: str) -> bool:
        """Verify 2FA token"""
        try:
            user = await self.db.users.find_one({'_id': user_id})
            if not user or not user.get('two_factor_enabled'):
                return False
                
            encrypted_secret = user['two_factor_secret']
            secret = await self.decrypt_secret(encrypted_secret)
            
            totp = pyotp.TOTP(secret)
            return totp.verify(token)
            
        except Exception as e:
            logger.error(f"Error verifying 2FA token: {str(e)}")
            return False

    async def disable_2fa(self, user_id: str) -> bool:
        """Disable 2FA for user"""
        try:
            result = await self.db.users.update_one(
                {'_id': user_id},
                {
                    '$set': {'two_factor_enabled': False},
                    '$unset': {'two_factor_secret': ''}
                }
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error disabling 2FA: {str(e)}")
            return False