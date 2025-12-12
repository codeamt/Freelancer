"""
Cart Service - Shopping cart management

Provides cart operations for e-commerce functionality.
Supports session-based (anonymous) and user-based (authenticated) carts.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from core.utils.logger import get_logger

logger = get_logger(__name__)


class CartItem:
    """Cart item representation."""
    
    def __init__(
        self,
        product_id: str,
        name: str,
        price: Decimal,
        quantity: int = 1,
        metadata: Optional[Dict] = None
    ):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.quantity = quantity
        self.metadata = metadata or {}
        self.added_at = datetime.utcnow()
    
    @property
    def subtotal(self) -> Decimal:
        """Calculate item subtotal."""
        return self.price * self.quantity
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "price": float(self.price),
            "quantity": self.quantity,
            "subtotal": float(self.subtotal),
            "metadata": self.metadata,
            "added_at": self.added_at.isoformat()
        }


class Cart:
    """Shopping cart."""
    
    def __init__(self, cart_id: str, user_id: Optional[str] = None):
        self.cart_id = cart_id
        self.user_id = user_id
        self.items: Dict[str, CartItem] = {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.metadata: Dict = {}
    
    def add_item(self, item: CartItem) -> None:
        """Add item to cart or update quantity if exists."""
        if item.product_id in self.items:
            self.items[item.product_id].quantity += item.quantity
        else:
            self.items[item.product_id] = item
        
        self.updated_at = datetime.utcnow()
        logger.info(f"Added {item.quantity}x {item.name} to cart {self.cart_id}")
    
    def remove_item(self, product_id: str) -> bool:
        """Remove item from cart."""
        if product_id in self.items:
            del self.items[product_id]
            self.updated_at = datetime.utcnow()
            logger.info(f"Removed product {product_id} from cart {self.cart_id}")
            return True
        return False
    
    def update_quantity(self, product_id: str, quantity: int) -> bool:
        """Update item quantity."""
        if product_id in self.items:
            if quantity <= 0:
                return self.remove_item(product_id)
            
            self.items[product_id].quantity = quantity
            self.updated_at = datetime.utcnow()
            logger.info(f"Updated product {product_id} quantity to {quantity} in cart {self.cart_id}")
            return True
        return False
    
    def clear(self) -> None:
        """Clear all items from cart."""
        self.items.clear()
        self.updated_at = datetime.utcnow()
        logger.info(f"Cleared cart {self.cart_id}")
    
    @property
    def item_count(self) -> int:
        """Total number of items."""
        return sum(item.quantity for item in self.items.values())
    
    @property
    def total(self) -> Decimal:
        """Calculate cart total."""
        return sum(item.subtotal for item in self.items.values())
    
    @property
    def is_empty(self) -> bool:
        """Check if cart is empty."""
        return len(self.items) == 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "cart_id": self.cart_id,
            "user_id": self.user_id,
            "items": [item.to_dict() for item in self.items.values()],
            "item_count": self.item_count,
            "total": float(self.total),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }


class CartService:
    """
    Cart service for managing shopping carts.
    
    Supports:
    - Session-based carts (anonymous users)
    - User-based carts (authenticated users)
    - Cart persistence (in-memory with optional DB backend)
    - Cart merging (session -> user on login)
    """
    
    def __init__(self, db_service=None):
        """
        Initialize cart service.
        
        Args:
            db_service: Optional database service for persistence
        """
        self.db = db_service
        self._carts: Dict[str, Cart] = {}  # In-memory cache
        self._cart_expiry = timedelta(days=7)  # Cart expiration
    
    def get_or_create_cart(self, cart_id: str, user_id: Optional[str] = None) -> Cart:
        """
        Get existing cart or create new one.
        
        Args:
            cart_id: Cart identifier (session ID or user ID)
            user_id: Optional user ID for authenticated carts
            
        Returns:
            Cart instance
        """
        if cart_id in self._carts:
            cart = self._carts[cart_id]
            if user_id and not cart.user_id:
                cart.user_id = user_id
            return cart
        
        cart = Cart(cart_id, user_id)
        self._carts[cart_id] = cart
        
        logger.info(f"Created new cart {cart_id} for user {user_id or 'anonymous'}")
        return cart
    
    def get_cart(self, cart_id: str) -> Optional[Cart]:
        """Get cart by ID."""
        return self._carts.get(cart_id)
    
    def add_to_cart(
        self,
        cart_id: str,
        product_id: str,
        name: str,
        price: Decimal,
        quantity: int = 1,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Cart:
        """
        Add item to cart.
        
        Args:
            cart_id: Cart identifier
            product_id: Product ID
            name: Product name
            price: Product price
            quantity: Quantity to add
            user_id: Optional user ID
            metadata: Optional item metadata
            
        Returns:
            Updated cart
        """
        cart = self.get_or_create_cart(cart_id, user_id)
        item = CartItem(product_id, name, price, quantity, metadata)
        cart.add_item(item)
        
        return cart
    
    def remove_from_cart(self, cart_id: str, product_id: str) -> bool:
        """Remove item from cart."""
        cart = self.get_cart(cart_id)
        if not cart:
            return False
        
        return cart.remove_item(product_id)
    
    def update_quantity(self, cart_id: str, product_id: str, quantity: int) -> bool:
        """Update item quantity in cart."""
        cart = self.get_cart(cart_id)
        if not cart:
            return False
        
        return cart.update_quantity(product_id, quantity)
    
    def clear_cart(self, cart_id: str) -> bool:
        """Clear all items from cart."""
        cart = self.get_cart(cart_id)
        if not cart:
            return False
        
        cart.clear()
        return True
    
    def merge_carts(self, session_cart_id: str, user_cart_id: str) -> Cart:
        """
        Merge session cart into user cart (on login).
        
        Args:
            session_cart_id: Anonymous session cart ID
            user_cart_id: Authenticated user cart ID
            
        Returns:
            Merged user cart
        """
        session_cart = self.get_cart(session_cart_id)
        user_cart = self.get_or_create_cart(user_cart_id)
        
        if session_cart and not session_cart.is_empty:
            for item in session_cart.items.values():
                user_cart.add_item(item)
            
            del self._carts[session_cart_id]
            logger.info(f"Merged session cart {session_cart_id} into user cart {user_cart_id}")
        
        return user_cart
    
    def delete_cart(self, cart_id: str) -> bool:
        """Delete cart."""
        if cart_id in self._carts:
            del self._carts[cart_id]
            logger.info(f"Deleted cart {cart_id}")
            return True
        return False
    
    def cleanup_expired_carts(self) -> int:
        """
        Remove expired carts.
        
        Returns:
            Number of carts removed
        """
        now = datetime.utcnow()
        expired = [
            cart_id for cart_id, cart in self._carts.items()
            if now - cart.updated_at > self._cart_expiry
        ]
        
        for cart_id in expired:
            del self._carts[cart_id]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired carts")
        
        return len(expired)