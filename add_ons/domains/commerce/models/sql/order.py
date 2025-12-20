"""Commerce Order Models"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.db.base_class import Base
import enum


class OrderStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Order(Base):
    """Order model for Commerce domain"""
    
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, default=0.0)
    shipping = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    payment_id = Column(String)  # Stripe payment intent ID
    shipping_address = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, total={self.total}, status={self.status})>"


class OrderItem(Base):
    """Order item model for Commerce domain"""
    
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # Price at time of purchase
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"
