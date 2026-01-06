"""
Product Service - Product catalog management

Provides product CRUD operations for e-commerce functionality.
"""
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
from core.utils.logger import get_logger

logger = get_logger(__name__)


class Product:
    """Product model."""
    
    def __init__(
        self,
        product_id: str,
        name: str,
        description: str,
        price: Decimal,
        category: str,
        stock: int = 0,
        image_url: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.product_id = product_id
        self.name = name
        self.description = description
        self.price = price
        self.category = category
        self.stock = stock
        self.image_url = image_url
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.is_active = True
    
    @property
    def in_stock(self) -> bool:
        """Check if product is in stock."""
        return self.stock > 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "category": self.category,
            "stock": self.stock,
            "in_stock": self.in_stock,
            "image_url": self.image_url,
            "metadata": self.metadata,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class ProductService:
    """
    Product catalog management service.
    
    In-memory implementation for development.
    TODO: Replace with database storage for production.
    """
    
    def __init__(self):
        self._products: Dict[str, Product] = {}
        self._initialize_sample_products()
    
    def _initialize_sample_products(self):
        """Initialize with sample products for development."""
        sample_products = [
            # Commerce products
            Product(
                product_id="prod_001",
                name="Premium Course Bundle",
                description="Complete access to all premium courses",
                price=Decimal("99.99"),
                category="education",
                stock=999,
                image_url="/static/images/course-bundle.jpg"
            ),
            Product(
                product_id="prod_002",
                name="Monthly Subscription",
                description="Monthly access to all content",
                price=Decimal("29.99"),
                category="subscription",
                stock=999,
                image_url="/static/images/subscription.jpg"
            ),
            Product(
                product_id="prod_003",
                name="E-Book Collection",
                description="Digital library of 50+ e-books",
                price=Decimal("49.99"),
                category="digital",
                stock=999,
                image_url="/static/images/ebooks.jpg"
            ),
            
            # LMS courses
            Product(
                product_id="course_001",
                name="Python for Beginners",
                description="Learn Python programming from scratch. Perfect for beginners with no coding experience.",
                price=Decimal("49.99"),
                category="course",
                stock=999,
                image_url="/static/images/python-course.jpg",
                metadata={"duration": "8 weeks", "level": "beginner", "lessons": 40}
            ),
            Product(
                product_id="course_002",
                name="Web Development Bootcamp",
                description="Master HTML, CSS, JavaScript, and React. Build real-world projects.",
                price=Decimal("79.99"),
                category="course",
                stock=999,
                image_url="/static/images/web-dev-course.jpg",
                metadata={"duration": "12 weeks", "level": "intermediate", "lessons": 60}
            ),
            Product(
                product_id="course_003",
                name="Data Science Fundamentals",
                description="Learn data analysis, visualization, and machine learning basics.",
                price=Decimal("89.99"),
                category="course",
                stock=999,
                image_url="/static/images/data-science-course.jpg",
                metadata={"duration": "10 weeks", "level": "intermediate", "lessons": 50}
            ),
            Product(
                product_id="course_004",
                name="Advanced JavaScript",
                description="Deep dive into JavaScript: async programming, design patterns, and performance.",
                price=Decimal("69.99"),
                category="course",
                stock=999,
                image_url="/static/images/js-advanced-course.jpg",
                metadata={"duration": "6 weeks", "level": "advanced", "lessons": 35}
            ),
        ]
        
        for product in sample_products:
            self._products[product.product_id] = product
        
        logger.info(f"Initialized {len(sample_products)} sample products")
    
    def create_product(
        self,
        product_id: str,
        name: str,
        description: str,
        price: Decimal,
        category: str,
        stock: int = 0,
        image_url: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Product:
        """Create a new product."""
        if product_id in self._products:
            raise ValueError(f"Product {product_id} already exists")
        
        product = Product(
            product_id=product_id,
            name=name,
            description=description,
            price=price,
            category=category,
            stock=stock,
            image_url=image_url,
            metadata=metadata
        )
        
        self._products[product_id] = product
        logger.info(f"Created product {product_id}: {name}")
        return product
    
    def get_product(self, product_id: str) -> Optional[Product]:
        """Get product by ID."""
        return self._products.get(product_id)
    
    def list_products(
        self,
        category: Optional[str] = None,
        active_only: bool = True
    ) -> List[Product]:
        """List all products with optional filtering."""
        products = list(self._products.values())
        
        if active_only:
            products = [p for p in products if p.is_active]
        
        if category:
            products = [p for p in products if p.category == category]
        
        return products
    
    def update_product(
        self,
        product_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        price: Optional[Decimal] = None,
        stock: Optional[int] = None,
        image_url: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Product]:
        """Update product details."""
        product = self._products.get(product_id)
        
        if not product:
            return None
        
        if name is not None:
            product.name = name
        if description is not None:
            product.description = description
        if price is not None:
            product.price = price
        if stock is not None:
            product.stock = stock
        if image_url is not None:
            product.image_url = image_url
        if is_active is not None:
            product.is_active = is_active
        
        product.updated_at = datetime.utcnow()
        logger.info(f"Updated product {product_id}")
        return product
    
    def delete_product(self, product_id: str) -> bool:
        """Delete product (soft delete by marking inactive)."""
        product = self._products.get(product_id)
        
        if not product:
            return False
        
        product.is_active = False
        product.updated_at = datetime.utcnow()
        logger.info(f"Deleted product {product_id}")
        return True
    
    def decrease_stock(self, product_id: str, quantity: int) -> bool:
        """Decrease product stock (for order fulfillment)."""
        product = self._products.get(product_id)
        
        if not product:
            logger.error(f"Product {product_id} not found")
            return False
        
        if product.stock < quantity:
            logger.error(f"Insufficient stock for product {product_id}")
            return False
        
        product.stock -= quantity
        product.updated_at = datetime.utcnow()
        logger.info(f"Decreased stock for {product_id} by {quantity}")
        return True
    
    def increase_stock(self, product_id: str, quantity: int) -> bool:
        """Increase product stock (for restocking or refunds)."""
        product = self._products.get(product_id)
        
        if not product:
            return False
        
        product.stock += quantity
        product.updated_at = datetime.utcnow()
        logger.info(f"Increased stock for {product_id} by {quantity}")
        return True
