"""
Tests for encryption functionality
"""

import pytest
import json
import base64
import os
from unittest.mock import patch

from core.services.encryption import (
    EncryptionService,
    KeyManager,
    encrypt_field,
    decrypt_field,
    EncryptedField,
    get_encryption_service,
    initialize_encryption
)
from core.services.auth.models_encrypted import (
    EncryptedUserModel,
    EncryptedUserCreate,
    SENSITIVE_USER_FIELDS
)


class TestKeyManager:
    """Test key management functionality"""
    
    def test_key_generation(self):
        """Test key generation"""
        manager = KeyManager("test-master-key")
        
        assert manager.current_key_id is not None
        assert manager.get_current_key() is not None
        assert len(manager.keys) == 1
    
    def test_key_rotation(self):
        """Test key rotation"""
        manager = KeyManager("test-master-key")
        old_key_id = manager.current_key_id
        
        # Rotate key
        new_key_id = manager.rotate_key()
        
        assert new_key_id != old_key_id
        assert manager.current_key_id == new_key_id
        assert len(manager.keys) == 2
        assert manager.keys[old_key_id]['status'] == 'deprecated'
    
    def test_encrypt_decrypt_with_current_key(self):
        """Test encryption/decryption with current key"""
        manager = KeyManager("test-master-key")
        
        data = b"sensitive data"
        encrypted = manager.encrypt_with_key(data)
        decrypted, key_id = manager.decrypt_with_any_key(encrypted)
        
        assert decrypted == data
        assert key_id == manager.current_key_id
    
    def test_encrypt_decrypt_with_old_key(self):
        """Test decryption with old key after rotation"""
        manager = KeyManager("test-master-key")
        old_key_id = manager.current_key_id
        
        # Encrypt with old key
        data = b"sensitive data"
        encrypted = manager.encrypt_with_key(data, old_key_id)
        
        # Rotate key
        manager.rotate_key()
        
        # Should still decrypt with old key
        decrypted, key_id = manager.decrypt_with_any_key(encrypted)
        
        assert decrypted == data
        assert key_id == old_key_id


class TestEncryptionService:
    """Test encryption service functionality"""
    
    @pytest.fixture
    def encryption_service(self):
        """Create encryption service with test key"""
        with patch.dict(os.environ, {'ENCRYPTION_MASTER_KEY': 'test-master-key-123'}):
            initialize_encryption()
            return get_encryption_service()
    
    def test_encrypt_string(self, encryption_service):
        """Test encrypting a string"""
        data = "sensitive information"
        encrypted = encryption_service.encrypt(data)
        
        assert isinstance(encrypted, str)
        assert encrypted != data
        
        # Should be base64 encoded
        assert len(base64.b64decode(encrypted)) > 0
    
    def test_encrypt_bytes(self, encryption_service):
        """Test encrypting bytes"""
        data = b"sensitive bytes"
        encrypted = encryption_service.encrypt(data)
        
        assert isinstance(encrypted, str)
        assert encrypted != data.decode()
    
    def test_encrypt_dict(self, encryption_service):
        """Test encrypting a dictionary"""
        data = {"ssn": "123-45-6789", "credit_card": "4111-1111-1111-1111"}
        encrypted = encryption_service.encrypt(data)
        
        assert isinstance(encrypted, str)
        assert encrypted != json.dumps(data)
    
    def test_decrypt_string(self, encryption_service):
        """Test decrypting a string"""
        original = "sensitive information"
        encrypted = encryption_service.encrypt(original)
        decrypted = encryption_service.decrypt(encrypted)
        
        assert decrypted == original
    
    def test_decrypt_dict(self, encryption_service):
        """Test decrypting a dictionary"""
        original = {"ssn": "123-45-6789", "credit_card": "4111-1111-1111-1111"}
        encrypted = encryption_service.encrypt(original)
        decrypted = encryption_service.decrypt(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_field_none(self, encryption_service):
        """Test encrypting None value"""
        result = encryption_service.encrypt_field(None)
        assert result is None
    
    def test_decrypt_field_none(self, encryption_service):
        """Test decrypting None value"""
        result = encryption_service.decrypt_field(None)
        assert result is None
    
    def test_encrypt_dict_fields(self, encryption_service):
        """Test encrypting specific fields in dict"""
        data = {
            "name": "John Doe",
            "ssn": "123-45-6789",
            "email": "john@example.com"
        }
        
        encrypted = encryption_service.encrypt_dict_fields(data, ["ssn"])
        
        assert encrypted["name"] == "John Doe"  # Not encrypted
        assert encrypted["email"] == "john@example.com"  # Not encrypted
        assert encrypted["ssn"] != "123-45-6789"  # Encrypted
    
    def test_decrypt_dict_fields(self, encryption_service):
        """Test decrypting specific fields in dict"""
        # First encrypt
        data = {
            "name": "John Doe",
            "ssn": "123-45-6789",
            "email": "john@example.com"
        }
        encrypted = encryption_service.encrypt_dict_fields(data, ["ssn"])
        
        # Then decrypt
        decrypted = encryption_service.decrypt_dict_fields(encrypted, ["ssn"])
        
        assert decrypted["name"] == "John Doe"
        assert decrypted["email"] == "john@example.com"
        assert decrypted["ssn"] == "123-45-6789"
    
    def test_rotate_encryption(self, encryption_service):
        """Test key rotation for encrypted data"""
        original = "sensitive data"
        encrypted = encryption_service.encrypt(original)
        
        # Rotate key
        encryption_service.key_manager.rotate_key()
        
        # Re-encrypt with new key
        re_encrypted = encryption_service.rotate_encryption(encrypted)
        
        # Should decrypt to same value
        decrypted = encryption_service.decrypt(re_encrypted)
        assert decrypted == original


class TestEncryptedField:
    """Test encrypted field decorator"""
    
    def test_encrypted_field_set_get(self):
        """Test setting and getting encrypted field"""
        with patch.dict(os.environ, {'ENCRYPTION_MASTER_KEY': 'test-master-key-123'}):
            initialize_encryption()
            
            class TestClass:
                phone = EncryptedField("phone")
            
            obj = TestClass()
            
            # Set value
            obj.phone = "555-123-4567"
            
            # Should get decrypted value
            assert obj.phone == "555-123-4567"
            
            # Encrypted value should be stored
            assert obj.get_encrypted() is not None
            assert obj.get_encrypted() != "555-123-4567"
    
    def test_encrypted_field_none(self):
        """Test encrypted field with None value"""
        with patch.dict(os.environ, {'ENCRYPTION_MASTER_KEY': 'test-master-key-123'}):
            initialize_encryption()
            
            class TestClass:
                phone = EncryptedField("phone")
            
            obj = TestClass()
            obj.phone = None
            
            assert obj.phone is None
            assert obj.get_encrypted() is None


class TestEncryptedUserModel:
    """Test encrypted user model"""
    
    @pytest.fixture
    def encryption_service(self):
        """Initialize encryption for tests"""
        with patch.dict(os.environ, {'ENCRYPTION_MASTER_KEY': 'test-master-key-123'}):
            initialize_encryption()
            return get_encryption_service()
    
    def test_encrypted_user_properties(self, encryption_service):
        """Test encrypted user properties"""
        user = EncryptedUserModel(
            id=1,
            email="test@example.com",
            role="user"
        )
        
        # Set encrypted fields
        user.phone = "555-123-4567"
        user.address = "123 Main St"
        user.ssn = "123-45-6789"
        
        # Get decrypted values
        assert user.phone == "555-123-4567"
        assert user.address == "123 Main St"
        assert user.ssn == "123-45-6789"
        
        # Check encrypted storage
        encrypted = user.get_encrypted_fields()
        assert encrypted['phone'] is not None
        assert encrypted['phone'] != "555-123-4567"
        assert encrypted['address'] is not None
        assert encrypted['address'] != "123 Main St"
    
    def test_encrypted_user_create(self, encryption_service):
        """Test creating user with encrypted fields"""
        user_data = EncryptedUserCreate(
            email="test@example.com",
            password="password123",
            phone="555-123-4567",
            ssn="123-45-6789",
            personal_info={"dob": "1990-01-01", "gender": "M"}
        )
        
        # Encrypt sensitive fields
        encrypted = user_data.encrypt_sensitive_fields()
        
        assert encrypted['phone'] is not None
        assert encrypted['phone'] != "555-123-4567"
        assert encrypted['ssn'] is not None
        assert encrypted['ssn'] != "123-45-6789"
        assert encrypted['personal_info'] is not None
        assert encrypted['personal_info'] != json.dumps({"dob": "1990-01-01", "gender": "M"})
    
    def test_to_dict_encrypted(self, encryption_service):
        """Test converting to dict with encrypted values"""
        user = EncryptedUserModel(
            id=1,
            email="test@example.com",
            role="user"
        )
        
        user.phone = "555-123-4567"
        user.ssn = "123-45-6789"
        
        data = user.to_dict_encrypted()
        
        assert data['phone'] is not None
        assert data['phone'] != "555-123-4567"
        assert data['ssn'] is not None
        assert data['ssn'] != "123-45-6789"
    
    def test_to_dict_decrypted(self, encryption_service):
        """Test converting to dict with decrypted values"""
        user = EncryptedUserModel(
            id=1,
            email="test@example.com",
            role="user"
        )
        
        user.phone = "555-123-4567"
        user.ssn = "123-45-6789"
        
        # First get encrypted
        encrypted_data = user.to_dict_encrypted()
        
        # Set encrypted values
        user.set_encrypted_fields({
            'phone': encrypted_data['phone'],
            'ssn': encrypted_data['ssn']
        })
        
        # Get decrypted
        data = user.to_dict_decrypted()
        
        assert data['phone'] == "555-123-4567"
        assert data['ssn'] == "123-45-6789"


class TestEncryptionIntegration:
    """Test encryption integration"""
    
    def test_encrypt_decrypt_functions(self):
        """Test standalone encrypt/decrypt functions"""
        with patch.dict(os.environ, {'ENCRYPTION_MASTER_KEY': 'test-master-key-123'}):
            initialize_encryption()
            
            original = "sensitive data"
            encrypted = encrypt_field(original)
            decrypted = decrypt_field(encrypted)
            
            assert encrypted != original
            assert decrypted == original
    
    def test_sensitive_fields_list(self):
        """Test sensitive fields list is defined"""
        assert len(SENSITIVE_USER_FIELDS) > 0
        assert 'phone' in SENSITIVE_USER_FIELDS
        assert 'ssn' in SENSITIVE_USER_FIELDS
        assert 'credit_card' in SENSITIVE_USER_FIELDS
