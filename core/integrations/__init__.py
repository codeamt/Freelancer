"""
Core Integrations

Centralized management of third-party service integrations.
"""

from .registry import (
    IntegrationRegistry,
    IntegrationConfig,
    IntegrationStatus,
    get_integration_registry,
    validate_integrations,
    get_integration_status,
    set_integration_status
)

# Import individual integrations
from . import analytics
from . import email
from . import huggingface
from . import instagram
from . import mailchimp
from . import shippo
from . import storage
from . import stripe
from . import web3

__all__ = [
    # Registry
    'IntegrationRegistry',
    'IntegrationConfig', 
    'IntegrationStatus',
    'get_integration_registry',
    'validate_integrations',
    'get_integration_status',
    'set_integration_status',
    
    # Integration modules
    'analytics',
    'email',
    'huggingface',
    'instagram',
    'mailchimp',
    'shippo',
    'storage',
    'stripe',
    'web3'
]
