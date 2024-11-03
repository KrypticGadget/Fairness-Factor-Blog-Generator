# security/encryption.py

from cryptography.fernet import Fernet
import base64
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class EncryptionHandler:
    def __init__(self):
        self.key = self._load_or_generate_key()
        self.cipher_suite = Fernet(self.key)

    def _load_or_generate_key(self) -> bytes:
        """Load existing encryption key or generate new one."""
        key_path = '.streamlit/encryption.key'
        try:
            if os.path.exists(key_path):
                with open(key_path, 'rb') as key_file:
                    return base64.urlsafe_b64decode(key_file.read())
            else:
                key = Fernet.generate_key()
                with open(key_path, 'wb') as key_file:
                    key_file.write(base64.urlsafe_b64encode(key))
                return key
        except Exception as e:
            logger.error(f"Encryption key error: {e}")
            raise

    def encrypt(self, data: str) -> Optional[str]:
        """Encrypt sensitive data."""
        try:
            return self.cipher_suite.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return None

    def decrypt(self, encrypted_data: str) -> Optional[str]:
        """Decrypt encrypted data."""
        try:
            return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return None