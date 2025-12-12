"""
Example: Commerce Domain GraphQL Integration

Shows how a domain adds its own GraphQL queries and types.
"""

import strawberry
from typing import List, Optional
from datetime import datetime
from add_ons.services.graphql import GraphQLService, BaseQuery

# -----------------------------------------------------------------------------
# Commerce Types
# -----------------------------------------------------------------------------

@strawberry.type
class Product:
    """Product type for e-commerce"""
    id: str
    name: str
    description: Optional[str] = None
    price: float
    category: str
    image_url: Optional[str] = None
    in_stock: bool = True
    created_at: datetime


@strawberry.type
class Order:
    """Order type for e-commerce"""
    id: str
    user_id: str
    products: List[Product]
    total: float
    status: str
    created_at: datetime


@strawberry.input
class ProductInput:
    """Input for creating/updating products"""
    name: str
    description: Optional[str] = None
    price: float
    category: str
    image_url: Optional[str] = None


# -----------------------------------------------------------------------------
# Commerce Queries
# -----------------------------------------------------------------------------

@strawberry.type
class CommerceQuery(BaseQuery):
    """Commerce-specific GraphQL queries"""
    
    @strawberry.field
    async def products(
        self,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10
    ) -> List[Product]:
        """Get products with optional filters"""
        # TODO: Implement actual database query
        return []
    
    @strawberry.field
    async def product(self, id: str) -> Optional[Product]:
        """Get a single product by ID"""
        # TODO: Implement actual database query
        return None
    
    @strawberry.field
    async def orders(self, user_id: str) -> List[Order]:
        """Get orders for a user"""
        # TODO: Implement actual database query
        return []


# -----------------------------------------------------------------------------
# Commerce Mutations
# -----------------------------------------------------------------------------

@strawberry.type
class CommerceMutation:
    """Commerce-specific GraphQL mutations"""
    
    @strawberry.field
    async def create_product(self, input: ProductInput) -> Product:
        """Create a new product"""
        from core.services import get_db_service
        db = get_db_service()
        
        product_data = {
            "name": input.name,
            "description": input.description,
            "price": input.price,
            "stock": input.stock
        }
        
        result = await db.insert("products", product_data)
        
        return Product(
            id=str(result.get("id", result.get("_id"))),
            name=result["name"],
            description=input.description,
            price=input.price,
            category=input.category,
            image_url=input.image_url,
            created_at=datetime.utcnow()
        )
    
    @strawberry.field
    async def update_product(self, id: str, input: ProductInput) -> Product:
        """Update an existing product"""
        from core.services import get_db_service
        db = get_db_service()
        
        update_data = {
            "name": input.name,
            "description": input.description,
            "price": input.price,
            "stock": input.stock
        }
        
        result = await db.update("products", id, update_data)
        
        return Product(
            id=str(result.get("id", result.get("_id"))),
            name=result["name"],
            description=input.description,
            price=input.price,
            category=input.category,
            image_url=input.image_url,
            created_at=datetime.utcnow()
        )


# -----------------------------------------------------------------------------
# Register with GraphQL Service
# -----------------------------------------------------------------------------

def register_commerce_graphql():
    """Register commerce GraphQL types with the service"""
    graphql = GraphQLService()
    
    # Add queries
    graphql.add_query(CommerceQuery)
    
    # Add mutations
    graphql.add_mutation(CommerceMutation)
    
    # Add types
    graphql.add_type(Product)
    graphql.add_type(Order)
    
    return graphql


# Usage in domain app:
# from .graphql_example import register_commerce_graphql
# graphql = register_commerce_graphql()
# schema = graphql.build_schema()
