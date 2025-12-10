"""
Product Repository - Demonstrates multi-database operations

Products have:
- Structured data in Postgres (id, name, price, inventory)
- Unstructured data in MongoDB (reviews, media, user interactions)
- Search/recommendations via GraphQL
"""
from typing import List, Optional, Dict, Any
from core.db.transaction_manager import TransactionManager, transactional
from core.db.adapters import PostgresAdapter, MongoDBAdapter
from core.utils.logger import get_logger

logger = get_logger(__name__)


class ProductRepository:
    """
    Multi-database product repository.
    
    Coordinates operations across Postgres, MongoDB, and Redis.
    """
    
    def __init__(
        self,
        postgres: PostgresAdapter,
        mongodb: MongoDBAdapter,
        redis: Optional[Any] = None
    ):
        self.postgres = postgres
        self.mongodb = mongodb
        self.redis = redis
        
    @transactional
    async def create_product(
        self,
        product_data: Dict[str, Any],
        media_data: Optional[List[Dict]] = None,
        transaction_manager: Optional[TransactionManager] = None
    ) -> str:
        """
        Create product with data across multiple databases.
        
        Transaction ensures:
        1. Product created in Postgres
        2. Media metadata stored in MongoDB
        3. Cache invalidated in Redis
        All or nothing - automatic rollback on failure.
        """
        tm = transaction_manager
        
        # 1. Insert structured product data (Postgres)
        product_id = await tm.execute(
            self.postgres,
            'insert',
            'products',
            {
                'name': product_data['name'],
                'description': product_data['description'],
                'price': product_data['price'],
                'sku': product_data['sku'],
                'category': product_data['category'],
                'is_active': True
            }
        )
        
        # 2. Insert unstructured media data (MongoDB)
        if media_data:
            await tm.execute(
                self.mongodb,
                'insert_one',
                'product_media',
                {
                    'product_id': product_id,
                    'images': media_data,
                    'videos': [],
                    'metadata': product_data.get('media_metadata', {})
                }
            )
            
        # 3. Initialize empty reviews collection (MongoDB)
        await tm.execute(
            self.mongodb,
            'insert_one',
            'product_reviews',
            {
                'product_id': product_id,
                'reviews': [],
                'average_rating': 0.0,
                'total_reviews': 0
            }
        )
        
        # 4. Invalidate product list cache (Redis)
        if self.redis:
            await tm.execute(
                self.redis,
                'delete',
                f"product_list:{product_data['category']}"
            )
            
        logger.info(f"Product {product_id} created successfully across all databases")
        return product_id
        
    async def get_product_full(self, product_id: int) -> Optional[Dict]:
        """
        Get complete product with data from all databases.
        
        Returns unified view combining Postgres + MongoDB data.
        """
        # Get structured data (Postgres)
        product = await self.postgres.fetch_one(
            "SELECT * FROM products WHERE id = $1",
            product_id
        )
        
        if not product:
            return None
            
        # Get media (MongoDB)
        media = await self.mongodb.find_one(
            'product_media',
            {'product_id': product_id}
        )
        
        # Get reviews summary (MongoDB)
        reviews = await self.mongodb.find_one(
            'product_reviews',
            {'product_id': product_id}
        )
        
        # Combine into unified view
        return {
            **product,
            'media': media.get('images', []) if media else [],
            'rating': reviews.get('average_rating', 0) if reviews else 0,
            'review_count': reviews.get('total_reviews', 0) if reviews else 0
        }
        
    @transactional
    async def add_product_review(
        self,
        product_id: int,
        review_data: Dict[str, Any],
        transaction_manager: Optional[TransactionManager] = None
    ):
        """
        Add review with atomic updates across databases.
        
        Updates both MongoDB (store review) and Redis (invalidate cache).
        """
        tm = transaction_manager
        
        # Add review to MongoDB
        await tm.execute(
            self.mongodb,
            'update_one',
            'product_reviews',
            {'product_id': product_id},
            {
                '$push': {'reviews': review_data},
                '$inc': {'total_reviews': 1}
            }
        )
        
        # Recalculate average rating
        reviews = await self.mongodb.find_one(
            'product_reviews',
            {'product_id': product_id}
        )
        
        if reviews:
            ratings = [r['rating'] for r in reviews['reviews']]
            avg_rating = sum(ratings) / len(ratings)
            
            await tm.execute(
                self.mongodb,
                'update_one',
                'product_reviews',
                {'product_id': product_id},
                {'average_rating': avg_rating}
            )
            
        # Invalidate product cache
        if self.redis:
            await tm.execute(
                self.redis,
                'delete',
                f"product:{product_id}"
            )
            
        logger.info(f"Review added to product {product_id}")