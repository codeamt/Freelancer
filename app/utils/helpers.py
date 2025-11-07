#  General Helper Utilities
import uuid
import hashlib
from datetime import datetime

def generate_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"

def hash_data(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def utc_now_str() -> str:
    return datetime.utcnow().isoformat()