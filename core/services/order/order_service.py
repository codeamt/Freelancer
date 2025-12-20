"""
Order Service - Order management

Handles order creation, tracking, and fulfillment.
"""
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum
from core.utils.logger import get_logger

logger = get_logger(__name__)


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class OrderItem:
    """Order item model."""
    
    def __init__(
        self,
        product_id: str,
        product_name: str,
        price: Decimal,
        quantity: int
    ):
        self.product_id = product_id
        self.product_name = product_name
        self.price = price
        self.quantity = quantity
    
    @property
    def subtotal(self) -> Decimal:
        """Calculate item subtotal."""
        return self.price * self.quantity
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "price": float(self.price),
            "quantity": self.quantity,
            "subtotal": float(self.subtotal)
        }


class Order:
    """Order model."""
    
    def __init__(
        self,
        order_id: str,
        user_id: str,
        items: List[OrderItem],
        payment_intent_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.order_id = order_id
        self.user_id = user_id
        self.items = items
        self.payment_intent_id = payment_intent_id
        self.metadata = metadata or {}
        self.status = OrderStatus.PENDING
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.paid_at: Optional[datetime] = None
    
    @property
    def total(self) -> Decimal:
        """Calculate order total."""
        return sum(item.subtotal for item in self.items)
    
    @property
    def item_count(self) -> int:
        """Get total item count."""
        return sum(item.quantity for item in self.items)
    
    def mark_as_paid(self, payment_intent_id: Optional[str] = None):
        """Mark order as paid."""
        self.status = OrderStatus.PAID
        self.paid_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if payment_intent_id:
            self.payment_intent_id = payment_intent_id
        logger.info(f"Order {self.order_id} marked as paid")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "items": [item.to_dict() for item in self.items],
            "total": float(self.total),
            "item_count": self.item_count,
            "status": self.status.value,
            "payment_intent_id": self.payment_intent_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "paid_at": self.paid_at.isoformat() if self.paid_at else None
        }


class OrderService:
    """
    Order management service.
    
    In-memory implementation for development.
    TODO: Replace with database storage for production.
    """
    
    def __init__(self):
        self._orders: Dict[str, Order] = {}
        self._order_counter = 1000
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID."""
        self._order_counter += 1
        return f"ORD-{self._order_counter}"
    
    def create_order(
        self,
        user_id: str,
        items: List[OrderItem],
        payment_intent_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Order:
        """Create a new order."""
        order_id = self._generate_order_id()
        
        order = Order(
            order_id=order_id,
            user_id=user_id,
            items=items,
            payment_intent_id=payment_intent_id,
            metadata=metadata
        )
        
        self._orders[order_id] = order
        logger.info(f"Created order {order_id} for user {user_id}, total: ${order.total}")
        return order
    
    def create_order_from_cart(
        self,
        user_id: str,
        cart,
        payment_intent_id: Optional[str] = None
    ) -> Order:
        """Create order from cart items."""
        items = []
        for cart_item in cart.items.values():
            order_item = OrderItem(
                product_id=cart_item.product_id,
                product_name=cart_item.name,
                price=cart_item.price,
                quantity=cart_item.quantity
            )
            items.append(order_item)
        
        return self.create_order(
            user_id=user_id,
            items=items,
            payment_intent_id=payment_intent_id,
            metadata={"cart_id": cart.cart_id}
        )
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self._orders.get(order_id)
    
    def get_user_orders(self, user_id: str) -> List[Order]:
        """Get all orders for a user."""
        return [
            order for order in self._orders.values()
            if order.user_id == user_id
        ]
    
    def mark_order_as_paid(self, order_id: str, payment_intent_id: Optional[str] = None) -> bool:
        """Mark order as paid."""
        order = self._orders.get(order_id)
        
        if not order:
            logger.error(f"Order {order_id} not found")
            return False
        
        order.mark_as_paid(payment_intent_id)
        return True
    
    def update_order_status(self, order_id: str, status: OrderStatus) -> bool:
        """Update order status."""
        order = self._orders.get(order_id)
        
        if not order:
            return False
        
        order.status = status
        order.updated_at = datetime.utcnow()
        logger.info(f"Updated order {order_id} status to {status.value}")
        return True
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        return self.update_order_status(order_id, OrderStatus.CANCELLED)
    
    def refund_order(self, order_id: str) -> bool:
        """Mark order as refunded."""
        return self.update_order_status(order_id, OrderStatus.REFUNDED)
