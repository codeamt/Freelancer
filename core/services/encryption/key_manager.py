"""
Key Management for Encryption

Handles encryption key generation, rotation, and storage.
"""

import os
import json
import base64
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from core.utils.logger import get_logger

logger = get_logger(__name__)


class KeyManager:
    """Manages encryption keys for the application"""
    
    def __init__(self, master_key: str = None):
        """
        Initialize key manager
        
        Args:
            master_key: Master encryption key (from environment)
        """
        self.master_key = master_key or os.getenv('ENCRYPTION_MASTER_KEY')
        if not self.master_key:
            logger.warning("No encryption master key provided, generating temporary key")
            self.master_key = self._generate_temp_key()
        
        self.keys: Dict[str, Dict] = {}
        self.current_key_id: str = None
        self._load_keys()
    
    def _generate_temp_key(self) -> str:
        """Generate a temporary encryption key"""
        import secrets
        temp_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        logger.warning(f"Generated temporary encryption key: {temp_key}")
        logger.warning("Store ENCRYPTION_MASTER_KEY in environment for production!")
        return temp_key
    
    def _load_keys(self):
        """Load encryption keys from storage"""
        # For now, use in-memory storage
        # In production, this could load from a secure key store
        
        # Generate initial key if none exists
        if not self.keys:
            self._generate_new_key("default")
            self.current_key_id = "default"
    
    def _generate_new_key(self, key_id: str) -> str:
        """Generate a new encryption key"""
        # Derive key from master key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=f"fastapp-{key_id}".encode(),
            iterations=100000,
            backend=default_backend()
        )
        
        key = kdf.derive(self.master_key.encode())
        
        # Store key metadata
        self.keys[key_id] = {
            'key': key,
            'created_at': datetime.utcnow(),
            'status': 'active'
        }
        
        logger.info(f"Generated new encryption key: {key_id}")
        return key
    
    def get_current_key(self) -> bytes:
        """Get the current active encryption key"""
        if not self.current_key_id:
            raise ValueError("No active encryption key")
        
        return self.keys[self.current_key_id]['key']
    
    def get_key(self, key_id: str) -> bytes:
        """Get a specific encryption key"""
        if key_id not in self.keys:
            raise ValueError(f"Key {key_id} not found")
        
        return self.keys[key_id]['key']
    
    def rotate_key(self) -> str:
        """
        Rotate to a new encryption key
        
        Returns:
            New key ID
        """
        # Generate timestamp-based key ID
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        new_key_id = f"key_{timestamp}"
        
        # Generate new key
        self._generate_new_key(new_key_id)
        
        # Update current key
        old_key_id = self.current_key_id
        self.current_key_id = new_key_id
        
        # Mark old key as deprecated
        if old_key_id:
            self.keys[old_key_id]['status'] = 'deprecated'
        
        logger.info(f"Rotated encryption key from {old_key_id} to {new_key_id}")
        return new_key_id
    
    def get_all_keys(self) -> List[Dict]:
        """Get information about all keys"""
        return [
            {
                'key_id': key_id,
                'created_at': key_data['created_at'].isoformat(),
                'status': key_data['status']
            }
            for key_id, key_data in self.keys.items()
        ]
    
    def decrypt_with_any_key(self, encrypted_data: bytes) -> tuple[bytes, str]:
        """
        Attempt to decrypt data with any available key
        
        Returns:
            Tuple of (decrypted_data, key_id_used)
        """
        # Extract IV and data
        # Format: iv(16):data
        if len(encrypted_data) < 16:
            raise ValueError("Invalid encrypted data format")
        
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        # Try each key
        for key_id, key_data in self.keys.items():
            try:
                # Decrypt with this key
                cipher = Cipher(
                    algorithms.AES(key_data['key']),
                    modes.CBC(iv),
                    backend=default_backend()
                )
                decryptor = cipher.decryptor()
                
                decrypted = decryptor.update(ciphertext) + decryptor.finalize()
                
                # Remove padding
                padding_len = decrypted[-1]
                decrypted = decrypted[:-padding_len]
                
                return decrypted, key_id
                
            except Exception:
                continue
        
        raise ValueError("Unable to decrypt data with any available key")
    
    def encrypt_with_key(self, data: bytes, key_id: str = None) -> bytes:
        """
        Encrypt data with specific key
        
        Args:
            data: Data to encrypt
            key_id: Key ID to use (default: current key)
            
        Returns:
            Encrypted data with IV
        """
        if key_id is None:
            key_id = self.current_key_id
        
        key = self.get_key(key_id)
        
        # Generate random IV
        iv = os.urandom(16)
        
        # Pad data to block size
        pad_len = 16 - (len(data) % 16)
        data = data + bytes([pad_len] * pad_len)
        
        # Encrypt
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        # Format: iv(16):data
        return iv + ciphertext


# Global key manager instance
_key_manager: KeyManager = None


def get_key_manager() -> KeyManager:
    """Get the global key manager instance"""
    global _key_manager
    if _key_manager is None:
        _key_manager = KeyManager()
    return _key_manager


def initialize_key_manager(master_key: str = None):
    """Initialize the global key manager"""
    global _key_manager
    _key_manager = KeyManager(master_key)
    return _key_manager
