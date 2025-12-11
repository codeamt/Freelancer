"""
SQLAlchemy ORM Models

These models are used for:
1. Alembic migration generation
2. Optional ORM-based queries (if needed)

For production code, prefer using repositories which:
- Use raw SQL adapters
- Support multiple databases
- Better performance
- Transaction coordination

Import ORM models if you need SQLAlchemy:
    from core.db.models import User
    
Import repositories for production:
    from core.db.repositories import UserRepository
"""
from core.db.models.user import User

__all__ = ['User']
