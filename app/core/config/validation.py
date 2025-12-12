"""
Startup Configuration Validation

Validates that all required environment variables and secrets are properly configured
before the application starts. Fails fast with clear error messages.
"""
import os
import sys
from typing import List, Dict, Optional
from core.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid"""
    pass


class ConfigValidator:
    """Validates application configuration at startup"""
    
    # Required secrets that MUST be set in production
    REQUIRED_SECRETS = {
        "JWT_SECRET": {
            "description": "Secret key for JWT token signing",
            "min_length": 32,
            "forbidden_values": ["devsecret", "your-secret-key-change-in-production"],
        },
        "APP_MEDIA_KEY": {
            "description": "Encryption key for media storage (Fernet key)",
            "min_length": 32,
            "forbidden_values": [],
        },
    }
    
    # Optional but recommended secrets
    RECOMMENDED_SECRETS = {
        "POSTGRES_PASSWORD": "Database password for PostgreSQL",
        "REDIS_PASSWORD": "Password for Redis",
        "AWS_SECRET_ACCESS_KEY": "AWS secret key for S3/storage",
    }
    
    def __init__(self, environment: Optional[str] = None):
        """
        Initialize validator
        
        Args:
            environment: Environment name (development, staging, production)
        """
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_secret(self, name: str, config: Dict) -> bool:
        """
        Validate a single secret
        
        Args:
            name: Environment variable name
            config: Configuration dict with validation rules
            
        Returns:
            True if valid, False otherwise
        """
        value = os.getenv(name)
        
        # Check if secret exists
        if not value:
            self.errors.append(
                f"❌ {name} is not set. {config['description']}. "
                f"Set it in your .env file or environment."
            )
            return False
        
        # Check minimum length
        if len(value) < config.get("min_length", 0):
            self.errors.append(
                f"❌ {name} is too short (minimum {config['min_length']} characters). "
                f"Current length: {len(value)}"
            )
            return False
        
        # Check forbidden values (insecure defaults)
        if value in config.get("forbidden_values", []):
            self.errors.append(
                f"❌ {name} is set to an insecure default value: '{value}'. "
                f"Generate a secure secret with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
            return False
        
        return True
    
    def validate_required_secrets(self) -> bool:
        """
        Validate all required secrets
        
        Returns:
            True if all valid, False otherwise
        """
        all_valid = True
        
        for name, config in self.REQUIRED_SECRETS.items():
            if not self.validate_secret(name, config):
                all_valid = False
        
        return all_valid
    
    def check_recommended_secrets(self):
        """Check recommended secrets and add warnings if missing"""
        for name, description in self.RECOMMENDED_SECRETS.items():
            value = os.getenv(name)
            if not value:
                self.warnings.append(
                    f"⚠️  {name} is not set. {description}. "
                    f"This is recommended for production."
                )
    
    def validate(self, strict: bool = None) -> bool:
        """
        Run full validation
        
        Args:
            strict: If True, enforce strict validation. If None, auto-detect based on environment.
            
        Returns:
            True if validation passes, False otherwise
            
        Raises:
            ConfigurationError: If validation fails in strict mode
        """
        # Auto-detect strict mode based on environment
        if strict is None:
            strict = self.environment in ["production", "staging"]
        
        logger.info(f"🔍 Validating configuration for environment: {self.environment}")
        
        # Validate required secrets
        secrets_valid = self.validate_required_secrets()
        
        # Check recommended secrets
        self.check_recommended_secrets()
        
        # Report results
        if self.errors:
            logger.error("❌ Configuration validation failed:")
            for error in self.errors:
                logger.error(f"  {error}")
        
        if self.warnings:
            logger.warning("⚠️  Configuration warnings:")
            for warning in self.warnings:
                logger.warning(f"  {warning}")
        
        # In strict mode, fail on errors
        if strict and self.errors:
            error_msg = "\n".join(self.errors)
            raise ConfigurationError(
                f"Configuration validation failed:\n{error_msg}\n\n"
                f"Fix these issues before starting the application."
            )
        
        # In development, just warn
        if not strict and self.errors:
            logger.warning(
                "⚠️  Running in development mode with configuration errors. "
                "These MUST be fixed before deploying to production!"
            )
            return False
        
        if secrets_valid:
            logger.info("✅ Configuration validation passed")
        
        return secrets_valid


def validate_config(environment: Optional[str] = None, strict: bool = None) -> bool:
    """
    Convenience function to validate configuration
    
    Args:
        environment: Environment name
        strict: Enforce strict validation
        
    Returns:
        True if valid, False otherwise
    """
    validator = ConfigValidator(environment)
    return validator.validate(strict=strict)


def generate_secret_key() -> str:
    """
    Generate a secure secret key
    
    Returns:
        Hex-encoded secret key (64 characters)
    """
    import secrets
    return secrets.token_hex(32)


if __name__ == "__main__":
    # CLI tool to validate config
    try:
        validate_config(strict=True)
        print("✅ All configuration checks passed!")
        sys.exit(0)
    except ConfigurationError as e:
        print(f"❌ Configuration validation failed:\n{e}")
        sys.exit(1)
