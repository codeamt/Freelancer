"""
Encryption Service for sensitive settings

Uses Fernet (symmetric encryption) from cryptography library.
Encryption keys are stored securely and rotated periodically.
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from core.utils.logger import get_logger

logger = get_logger(__name__)


class EncryptionService:
    """
    Service for encrypting/decrypting sensitive data.
    
    Uses Fernet symmetric encryption with key derivation.
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption service.
        
        Args:
            master_key: Master key for encryption (from env or generate)
        """
        # Get or generate master key
        if master_key:
            self._master_key = master_key.encode()
        else:
            # Try to load from environment
            env_key = os.getenv("ENCRYPTION_MASTER_KEY")
            if env_key:
                self._master_key = env_key.encode()
            else:
                # Generate new key (should be stored securely!)
                self._master_key = Fernet.generate_key()
                logger.warning(
                    "Generated new encryption key. Store ENCRYPTION_MASTER_KEY "
                    "in environment: " + self._master_key.decode()
                )
        
        # Create Fernet cipher
        self._cipher = Fernet(self._master_key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64 encoded encrypted string
            
        Example:
            encrypted = encryption_service.encrypt("my_secret_key")
            # Returns: "gAAAAABhkY3z..."
        """
        if not plaintext:
            return ""
        
        try:
            encrypted_bytes = self._cipher.encrypt(plaintext.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt encrypted string.
        
        Args:
            encrypted: Base64 encoded encrypted string
            
        Returns:
            Decrypted plaintext string
            
        Raises:
            InvalidToken: If decryption fails (wrong key or corrupted data)
        """
        if not encrypted:
            return ""
        
        try:
            decrypted_bytes = self._cipher.decrypt(encrypted.encode())
            return decrypted_bytes.decode()
        except InvalidToken:
            logger.error("Decryption failed: Invalid token or wrong key")
            raise
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def rotate_key(self, new_master_key: str) -> Fernet:
        """
        Rotate encryption key.
        
        This would require re-encrypting all existing encrypted data.
        Should be done as a maintenance operation.
        
        Args:
            new_master_key: New master key
            
        Returns:
            New Fernet cipher
        """
        logger.warning("Key rotation initiated")
        new_cipher = Fernet(new_master_key.encode())
        
        # Note: Caller must re-encrypt all data with new cipher
        # This is intentionally not automatic to avoid data loss
        
        return new_cipher
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new Fernet key.
        
        Returns:
            Base64 encoded key suitable for Fernet
        """
        return Fernet.generate_key().decode()
    
    @staticmethod
    def derive_key(password: str, salt: Optional[bytes] = None) -> str:
        """
        Derive a Fernet key from a password.
        
        Useful for user-specific encryption or deriving keys from
        passwords rather than storing raw keys.
        
        Args:
            password: Password to derive key from
            salt: Salt for key derivation (generate if not provided)
            
        Returns:
            Base64 encoded derived key
        """
        if not salt:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode()
    
    def encrypt_dict(self, data: dict, keys_to_encrypt: list) -> dict:
        """
        Encrypt specific keys in a dictionary.
        
        Args:
            data: Dictionary with data
            keys_to_encrypt: List of keys to encrypt
            
        Returns:
            Dictionary with specified keys encrypted
            
        Example:
            data = {
                "username": "admin",
                "password": "secret123",
                "api_key": "sk_live_abc"
            }
            
            encrypted = encryption_service.encrypt_dict(
                data,
                ["password", "api_key"]
            )
            
            # Result:
            # {
            #     "username": "admin",
            #     "password": "gAAAAAB...",
            #     "api_key": "gAAAAAB..."
            # }
        """
        result = data.copy()
        
        for key in keys_to_encrypt:
            if key in result and result[key]:
                result[key] = self.encrypt(str(result[key]))
        
        return result
    
    def decrypt_dict(self, data: dict, keys_to_decrypt: list) -> dict:
        """
        Decrypt specific keys in a dictionary.
        
        Args:
            data: Dictionary with encrypted data
            keys_to_decrypt: List of keys to decrypt
            
        Returns:
            Dictionary with specified keys decrypted
        """
        result = data.copy()
        
        for key in keys_to_decrypt:
            if key in result and result[key]:
                try:
                    result[key] = self.decrypt(result[key])
                except InvalidToken:
                    logger.error(f"Failed to decrypt key: {key}")
                    result[key] = None
        
        return result
    
    def is_encrypted(self, value: str) -> bool:
        """
        Check if a value appears to be Fernet encrypted.
        
        Fernet tokens start with 'gAAAAA' in base64.
        
        Args:
            value: String to check
            
        Returns:
            True if value looks like Fernet encrypted data
        """
        if not value or len(value) < 20:
            return False
        
        # Fernet tokens have specific prefix
        return value.startswith("gAAAAA")


# Global encryption service instance
# Initialized with key from environment or generates new one
encryption_service = EncryptionService()


# ============================================================================
# Utility Functions
# ============================================================================

def encrypt_value(value: str) -> str:
    """Convenience function to encrypt a value"""
    return encryption_service.encrypt(value)


def decrypt_value(encrypted: str) -> str:
    """Convenience function to decrypt a value"""
    return encryption_service.decrypt(encrypted)


def is_encrypted(value: str) -> bool:
    """Check if value is encrypted"""
    return encryption_service.is_encrypted(value)