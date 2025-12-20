"""Commerce Product Model"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from core.db.base_class import Base


class Product(Base):
    """Product model for Commerce domain"""
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    sku = Column(String, unique=True)
    category = Column(String)
    tags = Column(JSONB)
    images = Column(JSONB)  # Array of image URLs
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>"
