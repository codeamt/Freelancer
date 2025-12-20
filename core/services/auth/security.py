# app/core/services/auth/security.py
import bcrypt
import os
from typing import Union
from core.utils.logger import get_logger

logger = get_logger(__name__)

class SecurityService:
    def __init__(self):
        # Configurable work factor for production (12-14 recommended)
        self.salt_rounds = int(os.getenv("BCRYPT_SALT_ROUNDS", "12"))
        
    def hash_password(self, password: str) -> str:
        """Securely hash a password using bcrypt"""
        try:
            salt = bcrypt.gensalt(rounds=self.salt_rounds)
            return bcrypt.hashpw(password.encode(), salt).decode()
        except Exception as e:
            logger.error(f"Password hashing failed: {e}")
            raise ValueError("Could not hash password")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(
                plain_password.encode(), 
                hashed_password.encode()
            )
        except Exception as e:
            logger.warning(f"Password verification failed: {e}")
            return False

    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return os.urandom(length).hex()

# Singleton instance for easy import
security = SecurityService()