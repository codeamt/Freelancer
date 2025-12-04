# app/add_ons/services/graphql/service.py
from typing import Dict, List, Optional
from graphql import build_schema, graphql_sync
import os
from add_ons.config import ENABLED_ADDONS

class GraphQLService:
    def __init__(self):
        self.schema = self._build_schema()
        self.loaders = DataLoaderRegistry()
        self._resolvers = self._load_resolvers()

    def _build_schema(self) -> str:
        # Core schema
        schema_parts = [self._load_schema_file('core/schema.graphql')]
        
        # Add enabled domains
        for domain in ENABLED_ADDONS:
            domain_path = f'domains/{domain}/schema.graphql'
            if os.path.exists(domain_path):
                schema_parts.append(self._load_schema_file(domain_path))
                
        return build_schema('\n'.join(schema_parts))

    def _load_resolvers(self) -> Dict:
        resolvers = {}
        for domain in ENABLED_ADDONS:
            try:
                module = __import__(f'add_ons.domains.{domain}.resolvers')
                resolvers.update(getattr(module, 'resolvers'))
            except ImportError:
                continue
        return resolvers

    async def execute(self, query: str, context: Dict = None):
        return await graphql_sync(
            self.schema,
            query,
            context_value={
                **context,
                'loaders': self.loaders,
                'services': self._resolvers
            }
        )