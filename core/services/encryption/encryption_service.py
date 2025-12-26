"""
Encryption Service

Provides encryption and decryption for sensitive data.
"""

import json
import base64
from typing import Any, Dict, Optional, Union
from datetime import datetime

from .key_manager import get_key_manager
from core.utils.logger import get_logger

logger = get_logger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self):
        self.key_manager = get_key_manager()
    
    def encrypt(self, data: Union[str, bytes, Dict, Any]) -> str:
        """
        Encrypt data
        
        Args:
            data: Data to encrypt (string, bytes, dict, or any JSON-serializable object)
            
        Returns:
            Base64 encoded encrypted string
        """
        try:
            # Convert data to bytes
            if isinstance(data, dict):
                data = json.dumps(data)
            elif not isinstance(data, (str, bytes)):
                data = str(data)
            
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # Encrypt with current key
            encrypted = self.key_manager.encrypt_with_key(data)
            
            # Return base64 encoded
            return base64.b64encode(encrypted).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> Any:
        """
        Decrypt data
        
        Args:
            encrypted_data: Base64 encoded encrypted string
            
        Returns:
            Decrypted data (attempts to parse as JSON if possible)
        """
        try:
            # Decode base64
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Decrypt with key manager (tries all keys)
            decrypted_bytes, key_id = self.key_manager.decrypt_with_any_key(encrypted_bytes)
            
            # Convert to string
            decrypted_str = decrypted_bytes.decode('utf-8')
            
            # Try to parse as JSON
            try:
                return json.loads(decrypted_str)
            except json.JSONDecodeError:
                return decrypted_str
                
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_field(self, value: Any, field_name: str = None) -> Optional[str]:
        """
        Encrypt a single field value
        
        Args:
            value: Value to encrypt
            field_name: Name of the field (for logging)
            
        Returns:
            Encrypted value or None if value is None
        """
        if value is None:
            return None
        
        try:
            return self.encrypt(value)
        except Exception as e:
            logger.error(f"Failed to encrypt field {field_name}: {e}")
            raise
    
    def decrypt_field(self, encrypted_value: str, field_name: str = None) -> Any:
        """
        Decrypt a single field value
        
        Args:
            encrypted_value: Encrypted value
            field_name: Name of the field (for logging)
            
        Returns:
            Decrypted value
        """
        if encrypted_value is None:
            return None
        
        try:
            return self.decrypt(encrypted_value)
        except Exception as e:
            logger.error(f"Failed to decrypt field {field_name}: {e}")
            raise
    
    def encrypt_dict_fields(self, data: Dict, encrypted_fields: list) -> Dict:
        """
        Encrypt specific fields in a dictionary
        
        Args:
            data: Dictionary with data
            encrypted_fields: List of field names to encrypt
            
        Returns:
            Dictionary with specified fields encrypted
        """
        result = data.copy()
        
        for field in encrypted_fields:
            if field in result:
                result[field] = self.encrypt_field(result[field], field)
        
        return result
    
    def decrypt_dict_fields(self, data: Dict, encrypted_fields: list) -> Dict:
        """
        Decrypt specific fields in a dictionary
        
        Args:
            data: Dictionary with encrypted data
            encrypted_fields: List of field names to decrypt
            
        Returns:
            Dictionary with specified fields decrypted
        """
        result = data.copy()
        
        for field in encrypted_fields:
            if field in result:
                result[field] = self.decrypt_field(result[field], field)
        
        return result
    
    def rotate_encryption(self, encrypted_data: str) -> str:
        """
        Re-encrypt data with the current key
        
        Args:
            encrypted_data: Data encrypted with an old key
            
        Returns:
            Data encrypted with the current key
        """
        try:
            # Decrypt with old key
            decrypted = self.decrypt(encrypted_data)
            
            # Re-encrypt with current key
            return self.encrypt(decrypted)
            
        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            raise
    
    def get_encryption_info(self) -> Dict:
        """
        Get information about the encryption system
        
        Returns:
            Dictionary with encryption metadata
        """
        return {
            'current_key_id': self.key_manager.current_key_id,
            'total_keys': len(self.key_manager.keys),
            'keys': self.key_manager.get_all_keys()
        }


# Global encryption service instance
_encryption_service: EncryptionService = None


def get_encryption_service() -> EncryptionService:
    """Get the global encryption service instance"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


def initialize_encryption(master_key: str = None):
    """Initialize the encryption service"""
    from .key_manager import initialize_key_manager
    
    # Initialize key manager
    initialize_key_manager(master_key)
    
    # Create encryption service
    global _encryption_service
    _encryption_service = EncryptionService()
    
    logger.info("Encryption service initialized")
    return _encryption_service
