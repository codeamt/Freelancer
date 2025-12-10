"""Commerce Inventory Model"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.db.base_class import Base


class Inventory(Base):
    """Inventory tracking model for Commerce domain"""
    
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=True)
    stock = Column(Integer, default=0)
    reserved = Column(Integer, default=0)  # Items in pending orders
    available = Column(Integer, default=0)  # stock - reserved
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    product = relationship("Product")
    
    def __repr__(self):
        return f"<Inventory(product_id={self.product_id}, stock={self.stock}, available={self.available})>"
