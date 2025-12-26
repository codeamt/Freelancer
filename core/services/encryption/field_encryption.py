"""
Field Encryption Utilities

Provides decorators and utilities for encrypting model fields.
"""

from typing import Any, Callable, Optional, Union
from functools import wraps
import json

from .encryption_service import get_encryption_service
from core.utils.logger import get_logger

logger = get_logger(__name__)


class EncryptedField:
    """
    A field that automatically encrypts/decrypts values
    """
    
    def __init__(self, field_name: str = None, encrypt_on_save: bool = True):
        """
        Initialize encrypted field
        
        Args:
            field_name: Name of the field (auto-detected if not provided)
            encrypt_on_save: Whether to encrypt when setting value
        """
        self.field_name = field_name
        self.encrypt_on_save = encrypt_on_save
        self.encrypted_value = None
        self.decrypted_value = None
        self.is_encrypted = False
    
    def __get__(self, obj, objtype=None):
        """Get the decrypted value"""
        if obj is None:
            return self
        
        if not self.is_encrypted:
            return self.decrypted_value
        
        # Decrypt on access
        if self.encrypted_value:
            try:
                encryption_service = get_encryption_service()
                self.decrypted_value = encryption_service.decrypt(self.encrypted_value)
            except Exception as e:
                logger.error(f"Failed to decrypt field {self.field_name}: {e}")
                return None
        
        return self.decrypted_value
    
    def __set__(self, obj, value):
        """Set and optionally encrypt the value"""
        self.decrypted_value = value
        
        if self.encrypt_on_save and value is not None:
            try:
                encryption_service = get_encryption_service()
                self.encrypted_value = encryption_service.encrypt(value)
                self.is_encrypted = True
            except Exception as e:
                logger.error(f"Failed to encrypt field {self.field_name}: {e}")
                self.encrypted_value = None
                self.is_encrypted = False
        else:
            self.encrypted_value = value
            self.is_encrypted = False
    
    def get_encrypted(self) -> Optional[str]:
        """Get the encrypted value for storage"""
        return self.encrypted_value if self.is_encrypted else None
    
    def set_encrypted(self, encrypted_value: str):
        """Set the encrypted value from storage"""
        self.encrypted_value = encrypted_value
        self.decrypted_value = None
        self.is_encrypted = True


def encrypt_field(value: Any) -> Optional[str]:
    """
    Encrypt a field value
    
    Args:
        value: Value to encrypt
        
    Returns:
        Encrypted value or None if value is None
    """
    if value is None:
        return None
    
    encryption_service = get_encryption_service()
    return encryption_service.encrypt_field(value)


def decrypt_field(encrypted_value: str) -> Any:
    """
    Decrypt a field value
    
    Args:
        encrypted_value: Encrypted value
        
    Returns:
        Decrypted value
    """
    if encrypted_value is None:
        return None
    
    encryption_service = get_encryption_service()
    return encryption_service.decrypt_field(encrypted_value)


def encrypted_property(field_name: str = None):
    """
    Decorator to create an encrypted property
    
    Usage:
        @encrypted_property('ssn')
        def ssn(self):
            return self._ssn
        
        @ssn.setter
        def ssn(self, value):
            self._ssn = value
    """
    def decorator(func):
        # Store the encrypted field name
        encrypted_field_name = f'_encrypted_{field_name or func.__name__}'
        
        @wraps(func)
        def getter(self):
            # Get encrypted value
            encrypted_value = getattr(self, encrypted_field_name, None)
            
            if encrypted_value:
                try:
                    encryption_service = get_encryption_service()
                    return encryption_service.decrypt(encrypted_value)
                except Exception as e:
                    logger.error(f"Failed to decrypt property {field_name}: {e}")
                    return None
            
            return None
        
        def setter(self, value):
            if value is not None:
                try:
                    encryption_service = get_encryption_service()
                    encrypted_value = encryption_service.encrypt(value)
                    setattr(self, encrypted_field_name, encrypted_value)
                except Exception as e:
                    logger.error(f"Failed to encrypt property {field_name}: {e}")
                    raise
            else:
                setattr(self, encrypted_field_name, None)
        
        # Create property
        prop = property(getter, setter)
        return prop
    
    return decorator


def encrypt_model_data(data: dict, encrypted_fields: list) -> dict:
    """
    Encrypt specific fields in model data
    
    Args:
        data: Model data dictionary
        encrypted_fields: List of field names to encrypt
        
    Returns:
        Data with encrypted fields
    """
    encryption_service = get_encryption_service()
    return encryption_service.encrypt_dict_fields(data, encrypted_fields)


def decrypt_model_data(data: dict, encrypted_fields: list) -> dict:
    """
    Decrypt specific fields in model data
    
    Args:
        data: Model data dictionary with encrypted fields
        encrypted_fields: List of field names to decrypt
        
    Returns:
        Data with decrypted fields
    """
    encryption_service = get_encryption_service()
    return encryption_service.decrypt_dict_fields(data, encrypted_fields)


class EncryptionMixin:
    """
    Mixin class for models that need encryption
    """
    
    # Define which fields should be encrypted
    _encrypted_fields = []
    
    def encrypt_sensitive_fields(self):
        """Encrypt all sensitive fields in this model"""
        encryption_service = get_encryption_service()
        
        for field in self._encrypted_fields:
            if hasattr(self, field):
                value = getattr(self, field)
                if value is not None:
                    encrypted = encryption_service.encrypt_field(value, field)
                    setattr(self, f'_encrypted_{field}', encrypted)
    
    def decrypt_sensitive_fields(self):
        """Decrypt all sensitive fields in this model"""
        encryption_service = get_encryption_service()
        
        for field in self._encrypted_fields:
            encrypted_field = f'_encrypted_{field}'
            if hasattr(self, encrypted_field):
                encrypted_value = getattr(self, encrypted_field)
                if encrypted_value is not None:
                    decrypted = encryption_service.decrypt_field(encrypted_value, field)
                    setattr(self, field, decrypted)
    
    def to_dict_encrypted(self) -> dict:
        """Convert to dictionary with encrypted fields"""
        data = {}
        
        for key, value in self.__dict__.items():
            if key.startswith('_encrypted_'):
                # This is already encrypted
                field_name = key[11:]  # Remove '_encrypted_' prefix
                data[field_name] = value
            elif key in self._encrypted_fields:
                # Encrypt this field
                if value is not None:
                    encryption_service = get_encryption_service()
                    data[key] = encryption_service.encrypt_field(value, key)
            else:
                # Regular field
                data[key] = value
        
        return data
    
    def to_dict_decrypted(self) -> dict:
        """Convert to dictionary with decrypted fields"""
        data = {}
        
        for key, value in self.__dict__.items():
            if key.startswith('_encrypted_'):
                # Decrypt this field
                field_name = key[11:]  # Remove '_encrypted_' prefix
                if value is not None:
                    encryption_service = get_encryption_service()
                    data[field_name] = encryption_service.decrypt_field(value, field_name)
            else:
                # Regular field
                data[key] = value
        
        return data
