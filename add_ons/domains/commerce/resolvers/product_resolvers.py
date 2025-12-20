"""Commerce Product GraphQL Resolvers"""
import strawberry
from typing import List, Optional
from .types import Product, ProductRecommendation
from ..repositories import ProductRepository

@strawberry.type
class CommerceQueries:
    """GraphQL queries for commerce domain"""
    
    @strawberry.field
    async def product(self, id: int) -> Optional[Product]:
        """Get product by ID"""
        # Inject repository from context
        repo: ProductRepository = self.context['product_repo']
        product_data = await repo.get_product_full(id)
        
        if not product_data:
            return None
            
        return Product(**product_data)
        
    @strawberry.field
    async def product_recommendations(
        self,
        product_id: int,
        limit: int = 5
    ) -> List[ProductRecommendation]:
        """
        Get ML-powered product recommendations.
        
        Uses DuckDB for analytics queries on historical data.
        """
        # This would call your recommendation service
        # which queries DuckDB for user behavior patterns
        pass


@strawberry.type
class CommerceMutations:
    """GraphQL mutations for commerce domain"""
    
    @strawberry.mutation
    async def create_product(
        self,
        name: str,
        description: str,
        price: float,
        category: str
    ) -> Product:
        """Create new product"""
        repo: ProductRepository = self.context['product_repo']
        
        product_id = await repo.create_product({
            'name': name,
            'description': description,
            'price': price,
            'category': category
        })
        
        product_data = await repo.get_product_full(product_id)
        return Product(**product_data)