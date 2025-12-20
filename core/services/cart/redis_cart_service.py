"""
Redis-backed Cart Service - Production-ready cart management

Provides high-performance, persistent cart storage using Redis.
Supports distributed deployments and automatic expiration.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json
import os
from core.utils.logger import get_logger
from core.services.cart.cart_service import Cart, CartItem

logger = get_logger(__name__)


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
