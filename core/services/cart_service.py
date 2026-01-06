"""
Cart Service - Shopping cart management

Provides cart operations for e-commerce functionality.
Supports session-based (anonymous) and user-based (authenticated) carts.
Includes both in-memory and Redis-backed implementations.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json
import os
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
    
    def create_checkout_session(self, cart_id: str, success_url: str, cancel_url: str) -> Optional[Dict]:
        """
        Create Stripe checkout session for cart.
        
        Args:
            cart_id: Cart identifier
            success_url: URL to redirect on successful payment
            cancel_url: URL to redirect on cancelled payment
            
        Returns:
            Dict with checkout session details or None if cart is empty
        """
        cart = self.get_cart(cart_id)
        if not cart or cart.is_empty:
            logger.warning(f"Cannot create checkout for empty cart {cart_id}")
            return None
        
        try:
            from core.integrations.stripe import StripeClient
            
            line_items = []
            for item in cart.items.values():
                line_items.append({
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': item.name,
                        },
                        'unit_amount': int(item.price * 100),
                    },
                    'quantity': item.quantity,
                })
            
            session = StripeClient.create_checkout_session(
                amount_cents=int(cart.total * 100),
                currency='usd',
                success_url=success_url,
                cancel_url=cancel_url
            )
            
            logger.info(f"Created checkout session for cart {cart_id}, total: ${cart.total}")
            return {
                'session_url': session,
                'cart_total': float(cart.total),
                'item_count': cart.item_count
            }
            
        except Exception as e:
            logger.error(f"Failed to create checkout session for cart {cart_id}: {e}")
            return None


class RedisCartService:
    """
    Production-ready cart service using Redis for storage.
    
    Features:
    - Persistent storage (survives restarts)
    - Distributed access (works across multiple servers)
    - Automatic expiration (TTL-based cleanup)
    - High performance (Redis is in-memory)
    - Scalable (Redis can handle millions of carts)
    
    Usage:
        cart_service = RedisCartService()
        cart = cart_service.add_to_cart(cart_id, product_id, name, price)
    """
    
    def __init__(self, redis_url: Optional[str] = None, ttl_days: int = 7):
        """
        Initialize Redis cart service.
        
        Args:
            redis_url: Redis connection URL (defaults to env var REDIS_URL)
            ttl_days: Cart expiration in days
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.ttl_seconds = ttl_days * 24 * 60 * 60
        self.redis_available = False
        
        try:
            import redis
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            self.redis.ping()
            self.redis_available = True
            logger.info("Redis cart service initialized")
        except ImportError:
            logger.warning("Redis library not installed - falling back to in-memory storage")
            self._fallback_carts: Dict[str, Cart] = {}
        except Exception as e:
            logger.warning(f"Redis connection failed: {e} - falling back to in-memory storage")
            self._fallback_carts: Dict[str, Cart] = {}
    
    def _get_key(self, cart_id: str) -> str:
        """Generate Redis key for cart."""
        return f"cart:{cart_id}"
    
    def _serialize_cart(self, cart: Cart) -> str:
        """Serialize cart to JSON."""
        return json.dumps(cart.to_dict())
    
    def _deserialize_cart(self, data: str) -> Cart:
        """Deserialize cart from JSON."""
        cart_dict = json.loads(data)
        cart = Cart(cart_id=cart_dict["cart_id"], user_id=cart_dict.get("user_id"))
        
        # Restore items
        for item_dict in cart_dict["items"]:
            item = CartItem(
                product_id=item_dict["product_id"],
                name=item_dict["name"],
                price=Decimal(str(item_dict["price"])),
                quantity=item_dict["quantity"],
                metadata=item_dict.get("metadata", {})
            )
            cart.items[item.product_id] = item
        
        # Restore timestamps
        cart.created_at = datetime.fromisoformat(cart_dict["created_at"])
        cart.updated_at = datetime.fromisoformat(cart_dict["updated_at"])
        
        return cart
    
    def get_cart(self, cart_id: str) -> Optional[Cart]:
        """Retrieve cart from Redis."""
        if not self.redis_available:
            return self._fallback_carts.get(cart_id)
        
        try:
            key = self._get_key(cart_id)
            data = self.redis.get(key)
            
            if not data:
                return None
            
            cart = self._deserialize_cart(data)
            return cart
        except Exception as e:
            logger.error(f"Failed to get cart {cart_id}: {e}")
            return None
    
    def save_cart(self, cart: Cart) -> bool:
        """Save cart to Redis with TTL."""
        if not self.redis_available:
            self._fallback_carts[cart.cart_id] = cart
            return True
        
        try:
            key = self._get_key(cart.cart_id)
            data = self._serialize_cart(cart)
            
            # Save with expiration
            self.redis.setex(key, self.ttl_seconds, data)
            return True
        except Exception as e:
            logger.error(f"Failed to save cart {cart.cart_id}: {e}")
            return False
    
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
        """Add item to cart."""
        cart = self.get_cart(cart_id)
        
        if not cart:
            cart = Cart(cart_id=cart_id, user_id=user_id)
        
        # Add or update item
        if product_id in cart.items:
            cart.items[product_id].quantity += quantity
        else:
            item = CartItem(
                product_id=product_id,
                name=name,
                price=price,
                quantity=quantity,
                metadata=metadata
            )
            cart.items[product_id] = item
        
        cart.updated_at = datetime.utcnow()
        self.save_cart(cart)
        
        logger.info(f"Added {quantity}x {name} to cart {cart_id}")
        return cart
    
    def remove_from_cart(self, cart_id: str, product_id: str) -> bool:
        """Remove item from cart."""
        cart = self.get_cart(cart_id)
        
        if not cart or product_id not in cart.items:
            return False
        
        del cart.items[product_id]
        cart.updated_at = datetime.utcnow()
        self.save_cart(cart)
        
        logger.info(f"Removed product {product_id} from cart {cart_id}")
        return True
    
    def update_quantity(self, cart_id: str, product_id: str, quantity: int) -> bool:
        """Update item quantity."""
        if quantity <= 0:
            return self.remove_from_cart(cart_id, product_id)
        
        cart = self.get_cart(cart_id)
        
        if not cart or product_id not in cart.items:
            return False
        
        cart.items[product_id].quantity = quantity
        cart.updated_at = datetime.utcnow()
        self.save_cart(cart)
        
        return True
    
    def clear_cart(self, cart_id: str) -> bool:
        """Clear all items from cart."""
        cart = self.get_cart(cart_id)
        
        if not cart:
            return False
        
        cart.items.clear()
        cart.updated_at = datetime.utcnow()
        self.save_cart(cart)
        
        return True
    
    def delete_cart(self, cart_id: str) -> bool:
        """Delete cart completely."""
        if not self.redis_available:
            if cart_id in self._fallback_carts:
                del self._fallback_carts[cart_id]
                return True
            return False
        
        try:
            key = self._get_key(cart_id)
            result = self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete cart {cart_id}: {e}")
            return False
    
    def merge_carts(self, session_cart_id: str, user_cart_id: str) -> Cart:
        """Merge session cart into user cart."""
        session_cart = self.get_cart(session_cart_id)
        user_cart = self.get_cart(user_cart_id)
        
        if not session_cart:
            return user_cart or Cart(cart_id=user_cart_id)
        
        if not user_cart:
            user_cart = Cart(cart_id=user_cart_id)
        
        # Merge items
        for product_id, item in session_cart.items.items():
            if product_id in user_cart.items:
                user_cart.items[product_id].quantity += item.quantity
            else:
                user_cart.items[product_id] = item
        
        user_cart.updated_at = datetime.utcnow()
        self.save_cart(user_cart)
        self.delete_cart(session_cart_id)
        
        logger.info(f"Merged session cart {session_cart_id} into user cart {user_cart_id}")
        return user_cart
    
    def create_checkout_session(self, cart_id: str, success_url: str, cancel_url: str) -> Optional[Dict]:
        """Create Stripe checkout session for cart."""
        cart = self.get_cart(cart_id)
        if not cart or cart.is_empty:
            logger.warning(f"Cannot create checkout for empty cart {cart_id}")
            return None
        
        try:
            from core.integrations.stripe import StripeClient
            
            session = StripeClient.create_checkout_session(
                amount_cents=int(cart.total * 100),
                currency='usd',
                success_url=success_url,
                cancel_url=cancel_url
            )
            
            logger.info(f"Created checkout session for cart {cart_id}, total: ${cart.total}")
            return {
                'session_url': session,
                'cart_total': float(cart.total),
                'item_count': cart.item_count
            }
            
        except Exception as e:
            logger.error(f"Failed to create checkout session for cart {cart_id}: {e}")
            return None
