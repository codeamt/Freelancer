"""
Universal GraphQL Service

Provides base GraphQL infrastructure for domains to extend.
Each domain adds its own types, queries, and mutations.

Usage:
    from add_ons.services.graphql import GraphQLService, BaseTypes
    
    # In domain
    @strawberry.type
    class ProductQuery:
        @strawberry.field
        async def products(self) -> List[Product]:
            return await get_products()
    
    # Register with service
    graphql = GraphQLService()
    graphql.add_query(ProductQuery)
"""

import strawberry
from typing import List, Optional, Type, Any
from datetime import datetime
from core.utils.logger import get_logger

logger = get_logger(__name__)


# -----------------------------------------------------------------------------
# Base Types (Common across all domains)
# -----------------------------------------------------------------------------

@strawberry.type
class UserType:
    """Base user type - domains can extend this"""
    id: str
    email: str
    username: Optional[str] = None
    roles: List[str] = strawberry.field(default_factory=list)
    created_at: datetime


@strawberry.input
class UserInput:
    """Base user input - for mutations"""
    email: str
    password: str
    username: Optional[str] = None


@strawberry.type
class MediaType:
    """Base media type - for file uploads"""
    id: str
    title: str
    description: Optional[str] = None
    url: str
    mime_type: Optional[str] = None
    size: Optional[int] = None
    uploaded_at: datetime


@strawberry.input
class MediaInput:
    """Base media input - for uploads"""
    title: str
    description: Optional[str] = None
    url: str


@strawberry.type
class PaginationInfo:
    """Pagination metadata"""
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


@strawberry.type
class ErrorType:
    """Standard error type"""
    message: str
    code: Optional[str] = None
    field: Optional[str] = None


# -----------------------------------------------------------------------------
# Base Query (Empty - domains add their own)
# -----------------------------------------------------------------------------

@strawberry.type
class BaseQuery:
    """
    Base query type - domains extend this with their own queries.
    
    Example:
        @strawberry.type
        class ProductQuery(BaseQuery):
            @strawberry.field
            async def products(self) -> List[Product]:
                return await get_products()
    """
    
    @strawberry.field
    async def health(self) -> str:
        """Health check endpoint"""
        return "ok"


# -----------------------------------------------------------------------------
# GraphQL Service (Schema Builder)
# -----------------------------------------------------------------------------

class GraphQLService:
    """
    GraphQL service for building domain-specific schemas.
    
    Domains register their queries, mutations, and types.
    Service builds the final schema.
    """
    
    def __init__(self):
        """Initialize GraphQL service"""
        self._queries: List[Type] = [BaseQuery]
        self._mutations: List[Type] = []
        self._types: List[Type] = [
            UserType,
            MediaType,
            PaginationInfo,
            ErrorType,
        ]
        self._schema: Optional[strawberry.Schema] = None
        logger.info("GraphQL service initialized")
    
    def add_query(self, query_class: Type) -> None:
        """
        Add a query class to the schema.
        
        Args:
            query_class: Strawberry query type class
        """
        if query_class not in self._queries:
            self._queries.append(query_class)
            self._schema = None  # Invalidate cached schema
            logger.info(f"Added query: {query_class.__name__}")
    
    def add_mutation(self, mutation_class: Type) -> None:
        """
        Add a mutation class to the schema.
        
        Args:
            mutation_class: Strawberry mutation type class
        """
        if mutation_class not in self._mutations:
            self._mutations.append(mutation_class)
            self._schema = None  # Invalidate cached schema
            logger.info(f"Added mutation: {mutation_class.__name__}")
    
    def add_type(self, type_class: Type) -> None:
        """
        Add a custom type to the schema.
        
        Args:
            type_class: Strawberry type class
        """
        if type_class not in self._types:
            self._types.append(type_class)
            logger.info(f"Added type: {type_class.__name__}")
    
    def build_schema(self) -> strawberry.Schema:
        """
        Build the final GraphQL schema.
        
        Returns:
            Strawberry schema with all registered queries/mutations
        """
        if self._schema is not None:
            return self._schema
        
        # Merge all queries into one
        if len(self._queries) > 1:
            # Create combined query class
            query_fields = {}
            for query_class in self._queries:
                for field_name in dir(query_class):
                    if not field_name.startswith('_'):
                        field = getattr(query_class, field_name)
                        if hasattr(field, '__strawberry_field__'):
                            query_fields[field_name] = field
            
            @strawberry.type
            class CombinedQuery:
                pass
            
            # Add all fields to combined query
            for field_name, field in query_fields.items():
                setattr(CombinedQuery, field_name, field)
            
            query = CombinedQuery
        else:
            query = self._queries[0]
        
        # Merge all mutations if any
        mutation = None
        if self._mutations:
            if len(self._mutations) > 1:
                mutation_fields = {}
                for mutation_class in self._mutations:
                    for field_name in dir(mutation_class):
                        if not field_name.startswith('_'):
                            field = getattr(mutation_class, field_name)
                            if hasattr(field, '__strawberry_field__'):
                                mutation_fields[field_name] = field
                
                @strawberry.type
                class CombinedMutation:
                    pass
                
                for field_name, field in mutation_fields.items():
                    setattr(CombinedMutation, field_name, field)
                
                mutation = CombinedMutation
            else:
                mutation = self._mutations[0]
        
        # Build schema
        self._schema = strawberry.Schema(
            query=query,
            mutation=mutation,
            types=self._types
        )
        
        logger.info(f"GraphQL schema built with {len(self._queries)} queries, {len(self._mutations)} mutations")
        return self._schema
    
    def get_schema(self) -> strawberry.Schema:
        """
        Get the current schema (builds if not cached).
        
        Returns:
            Strawberry schema
        """
        return self.build_schema()


# -----------------------------------------------------------------------------
# Singleton Instance (Optional)
# -----------------------------------------------------------------------------

_graphql_service: Optional[GraphQLService] = None


def get_graphql_service() -> GraphQLService:
    """
    Get singleton GraphQL service instance.
    
    Returns:
        GraphQLService instance
    """
    global _graphql_service
    if _graphql_service is None:
        _graphql_service = GraphQLService()
    return _graphql_service


# -----------------------------------------------------------------------------
# Helper Decorators
# -----------------------------------------------------------------------------

def graphql_query(func):
    """
    Decorator to register a function as a GraphQL query.
    
    Usage:
        @graphql_query
        async def get_products() -> List[Product]:
            return await fetch_products()
    """
    service = get_graphql_service()
    
    @strawberry.type
    class QueryWrapper:
        pass
    
    setattr(QueryWrapper, func.__name__, strawberry.field(func))
    service.add_query(QueryWrapper)
    
    return func


def graphql_mutation(func):
    """
    Decorator to register a function as a GraphQL mutation.
    
    Usage:
        @graphql_mutation
        async def create_product(input: ProductInput) -> Product:
            return await save_product(input)
    """
    service = get_graphql_service()
    
    @strawberry.type
    class MutationWrapper:
        pass
    
    setattr(MutationWrapper, func.__name__, strawberry.field(func))
    service.add_mutation(MutationWrapper)
    
    return func


# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = [
    # Service
    "GraphQLService",
    "get_graphql_service",
    
    # Base Types
    "UserType",
    "UserInput",
    "MediaType",
    "MediaInput",
    "PaginationInfo",
    "ErrorType",
    "BaseQuery",
    
    # Decorators
    "graphql_query",
    "graphql_mutation",
]
