# Encryption, Token, and Random String Helpers
import secrets
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