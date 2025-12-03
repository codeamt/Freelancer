"""
Core User Model

The only model that belongs in core.
All other models should be in their respective domains.
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from core.db.base_class import Base


class User(Base):
    """Core user model - used across all domains"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
