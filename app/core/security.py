# Password hashing utilities
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a password using Argon2"""
    return ph.hash(password)


def verify_password(hash: str, password: str) -> bool:
    """Verify a password against its hash"""
    try:
        ph.verify(hash, password)
        return True
    except VerifyMismatchError:
        return False
