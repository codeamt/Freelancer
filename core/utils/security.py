"""
Security Utilities

Consolidated security functions for encryption, authentication, and sanitization.
Includes both simple and advanced encryption capabilities.
"""

import secrets
import bcrypt
import html
import re
import json
import base64
import os
from typing import Any, Union, Optional, Dict, List
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Simple Encryption (Fernet-based)
FERNET_KEY = Fernet.generate_key()
fernet = Fernet(FERNET_KEY)

# Advanced Encryption (AES-based)
class KeyManager:
    """Manages encryption keys for the application"""
    
    def __init__(self, master_key: str = None):
        self.master_key = master_key or os.getenv('ENCRYPTION_MASTER_KEY')
        if not self.master_key:
            # Generate temporary key if none provided
            self.master_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        
        self.keys: Dict[str, Dict] = {}
        self.current_key_id: str = None
        self._load_keys()
    
    def _load_keys(self):
        """Load encryption keys from storage"""
        if not self.keys:
            self._generate_new_key("default")
            self.current_key_id = "default"
    
    def _generate_new_key(self, key_id: str) -> str:
        """Generate a new encryption key"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=f"fastapp-{key_id}".encode(),
            iterations=100000,
            backend=default_backend()
        )
        
        key = kdf.derive(self.master_key.encode())
        
        self.keys[key_id] = {
            'key': key,
            'created_at': datetime.utcnow(),
            'status': 'active'
        }
        
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
    
    def encrypt_with_key(self, data: bytes, key_id: str = None) -> bytes:
        """Encrypt data with specific key"""
        if key_id is None:
            key_id = self.current_key_id
        
        key = self.get_key(key_id)
        iv = os.urandom(16)
        
        # Pad data to block size
        pad_len = 16 - (len(data) % 16)
        data = data + bytes([pad_len] * pad_len)
        
        # Encrypt
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        return iv + ciphertext
    
    def decrypt_with_any_key(self, encrypted_data: bytes) -> tuple[bytes, str]:
        """Attempt to decrypt data with any available key"""
        if len(encrypted_data) < 16:
            raise ValueError("Invalid encrypted data format")
        
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        for key_id, key_data in self.keys.items():
            try:
                cipher = Cipher(algorithms.AES(key_data['key']), modes.CBC(iv), backend=default_backend())
                decryptor = cipher.decryptor()
                decrypted = decryptor.update(ciphertext) + decryptor.finalize()
                
                # Remove padding
                padding_len = decrypted[-1]
                decrypted = decrypted[:-padding_len]
                
                return decrypted, key_id
            except Exception:
                continue
        
        raise ValueError("Unable to decrypt data with any available key")

# Global instances
_key_manager: KeyManager = None

def get_key_manager() -> KeyManager:
    """Get the global key manager instance"""
    global _key_manager
    if _key_manager is None:
        _key_manager = KeyManager()
    return _key_manager

# =============================================================================
# Simple Encryption Functions (Fernet-based)
# =============================================================================

def encrypt_text(plaintext: str) -> str:
    """Encrypt text using Fernet (simple)"""
    return fernet.encrypt(plaintext.encode()).decode()

def decrypt_text(ciphertext: str) -> str:
    """Decrypt text using Fernet (simple)"""
    return fernet.decrypt(ciphertext.encode()).decode()

def generate_token(length: int = 32) -> str:
    """Generate secure random token"""
    return secrets.token_urlsafe(length)

def is_valid_token(token: str) -> bool:
    """Validate token format"""
    return len(token) > 10 and all(c.isalnum() or c in ('-', '_') for c in token)

# =============================================================================
# Password Functions
# =============================================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# =============================================================================
# Advanced Encryption Functions (AES-based)
# =============================================================================

def encrypt_data(data: Union[str, bytes, Dict, Any]) -> str:
    """
    Encrypt data using advanced AES encryption
    
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
        key_manager = get_key_manager()
        encrypted = key_manager.encrypt_with_key(data)
        
        # Return base64 encoded
        return base64.b64encode(encrypted).decode('utf-8')
        
    except Exception as e:
        from core.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.error(f"Encryption failed: {e}")
        raise

def decrypt_data(encrypted_data: str) -> Any:
    """
    Decrypt data using advanced AES encryption
    
    Args:
        encrypted_data: Base64 encoded encrypted string
        
    Returns:
        Decrypted data (attempts to parse as JSON if possible)
    """
    try:
        # Decode base64
        encrypted_bytes = base64.b64decode(encrypted_data)
        
        # Decrypt with key manager
        key_manager = get_key_manager()
        decrypted_bytes, key_id = key_manager.decrypt_with_any_key(encrypted_bytes)
        
        # Convert to string
        decrypted_str = decrypted_bytes.decode('utf-8')
        
        # Try to parse as JSON
        try:
            return json.loads(decrypted_str)
        except json.JSONDecodeError:
            return decrypted_str
            
    except Exception as e:
        from core.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.error(f"Decryption failed: {e}")
        raise

def encrypt_field(value: Any) -> Optional[str]:
    """Encrypt a single field value"""
    if value is None:
        return None
    return encrypt_data(value)

def decrypt_field(encrypted_value: str) -> Any:
    """Decrypt a single field value"""
    if encrypted_value is None:
        return None
    return decrypt_data(encrypted_value)

# =============================================================================
# Sanitization Functions
# =============================================================================

def sanitize_html(value: str) -> str:
    """Sanitize HTML to prevent XSS"""
    if not isinstance(value, str):
        return value
    # Escape HTML special characters
    safe = html.escape(value, quote=True)
    # Remove remaining tags
    return re.sub(r'<.*?>', '', safe)

def sanitize_css_value(value: str) -> str:
    """Sanitize CSS values to prevent injection"""
    if not isinstance(value, str):
        return value
    # Prevent JS injection in CSS
    value_lower = value.lower()
    if any(bad in value_lower for bad in ["javascript:", "expression(", "url("]):
        return ""
    # Strip all but safe CSS characters
    return re.sub(r'[^a-zA-Z0-9#(),.%\-\s]', '', value)

def sanitize_sql_input(value: str) -> str:
    """Basic SQL injection prevention"""
    if not isinstance(value, str):
        return value
    # Remove dangerous SQL patterns
    dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'EXEC', 'UNION', 'SELECT']
    value_upper = value.upper()
    for danger in dangerous:
        if danger in value_upper:
            raise ValueError(f"Potentially dangerous SQL pattern detected: {danger}")
    return value.strip()

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for secure storage"""
    if not isinstance(filename, str):
        return filename
    # Remove path separators
    filename = filename.replace('/', '_').replace('..', '_')
    # Remove dangerous characters
    return re.sub(r'[^\w\-_\.]', '', filename)

def sanitize_user_input(value: str, max_length: int = 1000) -> str:
    """General user input sanitization"""
    if not isinstance(value, str):
        return value
    # Limit length
    if len(value) > max_length:
        value = value[:max_length]
    # Strip control characters
    return ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')

# =============================================================================
# Validation Functions
# =============================================================================

def is_valid_email(email: str) -> bool:
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_safe_url(url: str) -> bool:
    """Check if URL is safe (no javascript)"""
    if not isinstance(url, str):
        return False
    url_lower = url.lower()
    return not url_lower.startswith(('javascript:', 'data:', 'vbscript:'))

def validate_password_strength(password: str) -> dict:
    """Validate password strength"""
    result = {
        'valid': True,
        'errors': [],
        'score': 0
    }
    
    if len(password) < 8:
        result['errors'].append('Password must be at least 8 characters')
        result['valid'] = False
    else:
        result['score'] += 1
    
    if not re.search(r'[A-Z]', password):
        result['errors'].append('Password must contain uppercase letter')
        result['valid'] = False
    else:
        result['score'] += 1
    
    if not re.search(r'[a-z]', password):
        result['errors'].append('Password must contain lowercase letter')
        result['valid'] = False
    else:
        result['score'] += 1
    
    if not re.search(r'\d', password):
        result['errors'].append('Password must contain number')
        result['valid'] = False
    else:
        result['score'] += 1
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result['errors'].append('Password must contain special character')
        result['valid'] = False
    else:
        result['score'] += 1
    
    return result

# =============================================================================
# Rate Limiting & Security Headers
# =============================================================================

def get_security_headers() -> dict:
    """Get standard security headers"""
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }

def generate_csrf_token() -> str:
    """Generate CSRF token"""
    return generate_token(32)

def verify_csrf_token(token: str, session_token: str) -> bool:
    """Verify CSRF token"""
    return secrets.compare_digest(token, session_token)

# =============================================================================
# Encryption Service Compatibility
# =============================================================================

class EncryptionService:
    """Compatibility class for existing encryption service usage"""
    
    def __init__(self):
        self.key_manager = get_key_manager()
    
    def encrypt(self, data: Union[str, bytes, Dict, Any]) -> str:
        """Encrypt data (compatibility method)"""
        return encrypt_data(data)
    
    def decrypt(self, encrypted_data: str) -> Any:
        """Decrypt data (compatibility method)"""
        return decrypt_data(encrypted_data)
    
    def encrypt_field(self, value: Any, field_name: str = None) -> Optional[str]:
        """Encrypt a field value (compatibility method)"""
        return encrypt_field(value)
    
    def decrypt_field(self, encrypted_value: str, field_name: str = None) -> Any:
        """Decrypt a field value (compatibility method)"""
        return decrypt_field(encrypted_value)
    
    def encrypt_dict_fields(self, data: Dict, encrypted_fields: list) -> Dict:
        """Encrypt specific fields in a dictionary"""
        result = data.copy()
        for field in encrypted_fields:
            if field in result:
                result[field] = self.encrypt_field(result[field], field)
        return result
    
    def decrypt_dict_fields(self, data: Dict, encrypted_fields: list) -> Dict:
        """Decrypt specific fields in a dictionary"""
        result = data.copy()
        for field in encrypted_fields:
            if field in result:
                result[field] = self.decrypt_field(result[field], field)
        return result
    
    def get_encryption_info(self) -> Dict:
        """Get encryption system information"""
        return {
            'current_key_id': self.key_manager.current_key_id,
            'total_keys': len(self.key_manager.keys),
            'keys': [
                {
                    'key_id': key_id,
                    'created_at': key_data['created_at'].isoformat(),
                    'status': key_data['status']
                }
                for key_id, key_data in self.key_manager.keys.items()
            ]
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
    """Initialize the encryption service (compatibility function)"""
    global _key_manager, _encryption_service
    _key_manager = KeyManager(master_key)
    _encryption_service = EncryptionService()
    
    from core.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Encryption service initialized")
    return _encryption_service

# =============================================================================
# Field Encryption Support
# =============================================================================

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
                from core.utils.logger import get_logger
                logger = get_logger(__name__)
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
                from core.utils.logger import get_logger
                logger = get_logger(__name__)
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

# =============================================================================
# Backward Compatibility
# =============================================================================

# aliases for backward compatibility
sanitize = sanitize_html
hash_pass = hash_password
verify_pass = verify_password
