"""
Security Utilities

Consolidated security functions for encryption, authentication, and sanitization.
"""

import secrets
import bcrypt
import html
import re
from cryptography.fernet import Fernet
from typing import Any, Union

# Encryption
FERNET_KEY = Fernet.generate_key()
fernet = Fernet(FERNET_KEY)


# =============================================================================
# Encryption & Token Functions
# =============================================================================

def encrypt_text(plaintext: str) -> str:
    """Encrypt text using Fernet"""
    return fernet.encrypt(plaintext.encode()).decode()


def decrypt_text(ciphertext: str) -> str:
    """Decrypt text using Fernet"""
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
        return value
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
# Backward Compatibility
# =============================================================================

# aliases for backward compatibility
sanitize = sanitize_html
hash_pass = hash_password
verify_pass = verify_password
