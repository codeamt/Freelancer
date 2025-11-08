import strawberry
from datetime import datetime
from typing import Optional

# -----------------------------------------------------------------------------
# User Schema
# -----------------------------------------------------------------------------
@strawberry.type
class UserType:
    id: int
    email: str
    role: str
    created_at: datetime

@strawberry.input
class UserInput:
    email: str
    password: str

@strawberry.type
class MediaType:
    id: int
    title: str
    description: Optional[str]
    url: str
    uploaded_at: datetime

@strawberry.input
class MediaInput:
    title: str
    description: Optional[str] = None
    url: str