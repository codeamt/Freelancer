"""
Core User SQLAlchemy Model

Purpose:
- Alembic migration generation
- Optional ORM queries
- Schema definition for Postgres

Note: UserRepository uses raw SQL adapters, not this ORM model.
The repository pattern and ORM can coexist:
- Use ORM for quick prototype queries
- Use Repository for production multi-DB operations
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from core.db.base_class import Base


class User(Base):
    """
    Core user model - SQLAlchemy ORM definition.
    
    Used by Alembic for migrations.
    Can be used for quick ORM queries if needed.
    """
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user", index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
    
    def to_dict(self):
        """Convert ORM model to dict (for compatibility with repositories)."""
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }