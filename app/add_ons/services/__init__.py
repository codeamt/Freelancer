"""
Shared Infrastructure Services

Universal services used across all domains.
These provide core functionality that domains build upon.

Services:
- auth: Universal authentication (JWT, roles, permissions)
- graphql: Universal GraphQL service (schema builder, base types)
- storage: File storage service (S3/MinIO with encryption)
- stripe: Payment processing (Stripe API operations)
- email_base: Email sending base class
- analytics_base: Event tracking base class
- notifications_base: Push notifications base class
- oauth_base: OAuth2 authentication base class
- event_bus_base: Event bus base class
- recommender_base: Recommendation engine base class
- database: Relational database (PostgreSQL) and document database (MongoDB)

Usage:
    from add_ons.services.auth import AuthService, get_current_user, require_role
    from add_ons.services.graphql import GraphQLService, get_graphql_service
    from add_ons.services.storage import StorageService
    from add_ons.services.stripe import StripeService
    from add_ons.services.postgres import PostgresService
    from add_ons.services.mongodb import MongoDBService

"""

from .auth import AuthService, get_current_user, require_role, require_permission
from .graphql import GraphQLService, get_graphql_service, BaseQuery
from .storage import StorageService
from .stripe import StripeService
from .postgres import PostgresService
from .mongodb import MongoDBService
from .analytics import AnalyticsService

__all__ = [
    "AuthService",
    "get_current_user",
    "require_role",
    "require_permission",
    "GraphQLService",
    "get_graphql_service",
    "BaseQuery",
    "StorageService",
    "StripeService",
    "PostgresService",
    "MongoDBService",
    "AnalyticsService",
]
