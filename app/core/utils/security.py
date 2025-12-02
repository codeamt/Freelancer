# Encryption, Token, and Random String Helpers
import secrets
import bcrypt
from cryptography.fernet import Fernet

FERNET_KEY = Fernet.generate_key()
fernet = Fernet(FERNET_KEY)

def encrypt_text(plaintext: str) -> str:
    return fernet.encrypt(plaintext.encode()).decode()

def decrypt_text(ciphertext: str) -> str:
    return fernet.decrypt(ciphertext.encode()).decode()

def generate_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)

def is_valid_token(token: str) -> bool:
    return len(token) > 10 and all(c.isalnum() or c in ('-', '_') for c in token)

# Password hashing functions
def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        password: Plain text password to verify
        hashed: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False