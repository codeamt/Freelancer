"""
GraphQL Schema Registry

Central management for GraphQL schemas from all domains.
Enables schema federation and cross-domain queries.
"""
from typing import Dict, List, Any
import strawberry
from strawberry.federation import Schema
from core.utils.logger import get_logger

logger = get_logger(__name__)


class SchemaRegistry:
    """
    Registry for GraphQL schemas from different domains.
    
    Allows each domain to register its types and resolvers,
    then combines them into a federated schema.
    """
    
    def __init__(self):
        self._queries: Dict[str, Any] = {}
        self._mutations: Dict[str, Any] = {}
        self._types: Dict[str, Any] = {}
        self._resolvers: Dict[str, Any] = {}
        self._schema: Optional[Schema] = None
        
    def register_domain(
        self,
        domain_name: str,
        queries: Optional[type] = None,
        mutations: Optional[type] = None,
        types: Optional[List[type]] = None,
        resolvers: Optional[Dict] = None
    ):
        """
        Register a domain's GraphQL schema components.
        
        Example:
            schema_registry.register_domain(
                'commerce',
                queries=CommerceQueries,
                mutations=CommerceMutations,
                types=[Product, Order],
                resolvers={'recommendations': get_recommendations}
            )
        """
        logger.info(f"Registering GraphQL domain: {domain_name}")
        
        if queries:
            self._queries[domain_name] = queries
        if mutations:
            self._mutations[domain_name] = mutations
        if types:
            self._types[domain_name] = types
        if resolvers:
            self._resolvers[domain_name] = resolvers
            
    def build_schema(self) -> Schema:
        """
        Build federated schema from all registered domains.
        
        Creates a unified GraphQL API that spans all domains.
        """
        # Combine all query classes
        query_fields = {}
        for domain, query_class in self._queries.items():
            for field_name in dir(query_class):
                if not field_name.startswith('_'):
                    query_fields[f"{domain}_{field_name}"] = getattr(query_class, field_name)
                    
        # Create unified Query type
        @strawberry.type
        class Query:
            pass
        
        for name, field in query_fields.items():
            setattr(Query, name, field)
            
        # Same for mutations
        mutation_fields = {}
        for domain, mutation_class in self._mutations.items():
            for field_name in dir(mutation_class):
                if not field_name.startswith('_'):
                    mutation_fields[f"{domain}_{field_name}"] = getattr(mutation_class, field_name)
                    
        @strawberry.type
        class Mutation:
            pass
        
        for name, field in mutation_fields.items():
            setattr(Mutation, name, field)
            
        # Build schema
        self._schema = strawberry.Schema(
            query=Query,
            mutation=Mutation
        )
        
        logger.info(f"GraphQL schema built with {len(query_fields)} queries and {len(mutation_fields)} mutations")
        return self._schema
        
    @property
    def schema(self) -> Schema:
        """Get built schema (builds if not already built)"""
        if not self._schema:
            return self.build_schema()
        return self._schema


# Global registry instance
schema_registry = SchemaRegistry()