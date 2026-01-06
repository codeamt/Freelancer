"""
Integration Registry

Centralized management of all third-party service integrations.
Provides configuration validation, health checks, and metadata.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import os
from core.utils.logger import get_logger

logger = get_logger(__name__)


class IntegrationStatus(Enum):
    """Integration status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class IntegrationConfig:
    """Integration configuration metadata"""
    name: str
    display_name: str
    description: str
    required_env_vars: List[str]
    optional_env_vars: List[str]
    health_check_path: Optional[str] = None
    initialization_function: Optional[str] = None
    dependencies: List[str] = None
    category: str = "general"


class IntegrationRegistry:
    """Registry for managing integrations"""
    
    def __init__(self):
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.statuses: Dict[str, IntegrationStatus] = {}
        self._register_default_integrations()
    
    def _register_default_integrations(self):
        """Register all default integrations"""
        
        # Analytics
        self.register(IntegrationConfig(
            name="analytics",
            display_name="Analytics",
            description="Website analytics and tracking",
            required_env_vars=["ANALYTICS_TRACKING_ID"],
            optional_env_vars=["ANALYTICS_ENABLED", "ANALYTICS_CONSENT_REQUIRED"],
            health_check_path="analytics.analytics_client",
            category="analytics"
        ))
        
        # Email
        self.register(IntegrationConfig(
            name="email",
            display_name="Email Service",
            description="Email sending and templating",
            required_env_vars=["EMAIL_PROVIDER", "EMAIL_HOST", "EMAIL_PORT"],
            optional_env_vars=["EMAIL_USERNAME", "EMAIL_PASSWORD", "EMAIL_FROM"],
            health_check_path="email.base",
            category="communication"
        ))
        
        # HuggingFace
        self.register(IntegrationConfig(
            name="huggingface",
            display_name="HuggingFace",
            description="AI/ML model integration",
            required_env_vars=["HUGGINGFACE_API_KEY"],
            optional_env_vars=["HUGGINGFACE_MODEL"],
            health_check_path="huggingface.huggingface_client",
            category="ai"
        ))
        
        # Instagram
        self.register(IntegrationConfig(
            name="instagram",
            display_name="Instagram",
            description="Instagram social media integration",
            required_env_vars=["INSTAGRAM_CLIENT_ID", "INSTAGRAM_CLIENT_SECRET"],
            optional_env_vars=["INSTAGRAM_REDIRECT_URI"],
            health_check_path="instagram.client",
            category="social"
        ))
        
        # Mailchimp
        self.register(IntegrationConfig(
            name="mailchimp",
            display_name="Mailchimp",
            description="Email marketing and campaigns",
            required_env_vars=["MAILCHIMP_API_KEY", "MAILCHIMP_SERVER_PREFIX"],
            optional_env_vars=[],
            health_check_path="mailchimp.client",
            category="marketing"
        ))
        
        # Shippo
        self.register(IntegrationConfig(
            name="shippo",
            display_name="Shippo",
            description="Shipping and logistics",
            required_env_vars=["SHIPPO_API_KEY"],
            optional_env_vars=["SHIPPO_TEST_MODE"],
            health_check_path="shippo.client",
            category="logistics"
        ))
        
        # Storage (S3/MinIO)
        self.register(IntegrationConfig(
            name="storage",
            display_name="Object Storage",
            description="File storage and CDN",
            required_env_vars=["S3_ENDPOINT", "S3_ACCESS_KEY", "S3_SECRET_KEY", "S3_BUCKET"],
            optional_env_vars=["S3_REGION"],
            health_check_path="storage.s3_client",
            category="storage"
        ))
        
        # Stripe
        self.register(IntegrationConfig(
            name="stripe",
            display_name="Stripe",
            description="Payment processing",
            required_env_vars=["STRIPE_API_KEY"],
            optional_env_vars=["STRIPE_WEBHOOK_SECRET", "STRIPE_PUBLISHABLE_KEY"],
            health_check_path="stripe.stripe_client",
            category="payments"
        ))
        
        # Web3
        self.register(IntegrationConfig(
            name="web3",
            display_name="Web3",
            description="Blockchain and cryptocurrency",
            required_env_vars=["WEB3_PROVIDER_URL"],
            optional_env_vars=["WEB3_CHAIN_ID", "WEB3_CONTRACT_ADDRESS"],
            health_check_path="web3.web3_client",
            category="blockchain"
        ))
    
    def register(self, config: IntegrationConfig):
        """Register an integration"""
        self.integrations[config.name] = config
        self.statuses[config.name] = IntegrationStatus.INACTIVE
        logger.info(f"Registered integration: {config.name}")
    
    def get_integration(self, name: str) -> Optional[IntegrationConfig]:
        """Get integration configuration by name"""
        return self.integrations.get(name)
    
    def list_integrations(self, category: str = None) -> List[IntegrationConfig]:
        """List all integrations, optionally filtered by category"""
        integrations = list(self.integrations.values())
        if category:
            integrations = [i for i in integrations if i.category == category]
        return integrations
    
    def validate_integration(self, name: str) -> Dict[str, Any]:
        """Validate integration configuration"""
        integration = self.get_integration(name)
        if not integration:
            return {"valid": False, "errors": [f"Integration {name} not found"]}
        
        errors = []
        warnings = []
        
        # Check required environment variables
        for env_var in integration.required_env_vars:
            if not os.getenv(env_var):
                errors.append(f"Missing required environment variable: {env_var}")
        
        # Check optional environment variables
        for env_var in integration.optional_env_vars:
            if not os.getenv(env_var):
                warnings.append(f"Missing optional environment variable: {env_var}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def validate_all_integrations(self) -> Dict[str, Dict[str, Any]]:
        """Validate all integrations"""
        results = {}
        for name in self.integrations:
            results[name] = self.validate_integration(name)
        return results
    
    def get_status(self, name: str) -> IntegrationStatus:
        """Get integration status"""
        return self.statuses.get(name, IntegrationStatus.DISABLED)
    
    def set_status(self, name: str, status: IntegrationStatus):
        """Set integration status"""
        if name in self.integrations:
            self.statuses[name] = status
            logger.info(f"Integration {name} status: {status.value}")
    
    def get_active_integrations(self) -> List[str]:
        """Get list of active integrations"""
        return [name for name, status in self.statuses.items() if status == IntegrationStatus.ACTIVE]
    
    def get_integrations_by_category(self) -> Dict[str, List[IntegrationConfig]]:
        """Get integrations grouped by category"""
        categories = {}
        for integration in self.integrations.values():
            if integration.category not in categories:
                categories[integration.category] = []
            categories[integration.category].append(integration)
        return categories
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of all integration configurations"""
        validation_results = self.validate_all_integrations()
        
        summary = {
            "total_integrations": len(self.integrations),
            "active_integrations": len(self.get_active_integrations()),
            "categories": self.get_integrations_by_category(),
            "validation_results": validation_results,
            "statuses": {name: status.value for name, status in self.statuses.items()}
        }
        
        return summary


# Global registry instance
_registry: IntegrationRegistry = None


def get_integration_registry() -> IntegrationRegistry:
    """Get the global integration registry"""
    global _registry
    if _registry is None:
        _registry = IntegrationRegistry()
    return _registry


def validate_integrations() -> Dict[str, Dict[str, Any]]:
    """Validate all integrations"""
    registry = get_integration_registry()
    return registry.validate_all_integrations()


def get_integration_status(name: str) -> IntegrationStatus:
    """Get integration status"""
    registry = get_integration_registry()
    return registry.get_status(name)


def set_integration_status(name: str, status: IntegrationStatus):
    """Set integration status"""
    registry = get_integration_registry()
    registry.set_status(name, status)
