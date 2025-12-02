"""
Application Settings

Secure configuration management using Pydantic Settings.
Loads environment variables and validates configuration.
Integrates with add-on system for dynamic configuration.
"""
from typing import Optional, List, Dict, Any
from pydantic import Field, validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os


class Settings(BaseSettings):
    """
    Application settings with security best practices.
    
    Environment variables are loaded from .env file (if present).
    Secrets are masked in logs and error messages.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra env vars
    )
    
    # ============================================================================
    # Core Application Settings
    # ============================================================================
    
    app_name: str = Field(default="FastApp", description="Application name")
    app_env: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=True, description="Debug mode")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=5001, description="Server port")
    
    # ============================================================================
    # Security Settings
    # ============================================================================
    
    # JWT Configuration
    jwt_secret: SecretStr = Field(
        default=SecretStr("change-this-secret-key-in-production"),
        description="JWT secret key - MUST be changed in production"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_minutes: int = Field(default=1440, description="JWT token expiration (24 hours)")
    
    # Password Requirements
    password_min_length: int = Field(default=8, description="Minimum password length")
    password_require_uppercase: bool = Field(default=False, description="Require uppercase letters")
    password_require_lowercase: bool = Field(default=False, description="Require lowercase letters")
    password_require_numbers: bool = Field(default=False, description="Require numbers")
    password_require_special: bool = Field(default=False, description="Require special characters")
    
    # CORS Settings
    cors_origins: List[str] = Field(
        default=["http://localhost:5001", "http://127.0.0.1:5001"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    
    # ============================================================================
    # Database Settings (Optional - for production)
    # ============================================================================
    
    # MongoDB
    mongo_uri: Optional[str] = Field(default=None, description="MongoDB connection URI")
    mongo_db_name: str = Field(default="fastapp", description="MongoDB database name")
    mongo_max_pool_size: int = Field(default=10, description="MongoDB connection pool size")
    
    # PostgreSQL (if needed)
    postgres_uri: Optional[str] = Field(default=None, description="PostgreSQL connection URI")
    
    # Redis (if needed)
    redis_uri: Optional[str] = Field(default=None, description="Redis connection URI")
    
    # ============================================================================
    # Add-on Specific Settings
    # ============================================================================
    
    # Email Service (for auth add-on)
    email_provider: Optional[str] = Field(default=None, description="Email provider: smtp, sendgrid, ses, mailgun")
    smtp_host: Optional[str] = Field(default=None, description="SMTP server host")
    smtp_port: Optional[int] = Field(default=587, description="SMTP server port")
    smtp_username: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[SecretStr] = Field(default=None, description="SMTP password")
    sendgrid_api_key: Optional[SecretStr] = Field(default=None, description="SendGrid API key")
    mailgun_api_key: Optional[SecretStr] = Field(default=None, description="Mailgun API key")
    mailgun_domain: Optional[str] = Field(default=None, description="Mailgun domain")
    from_email: str = Field(default="noreply@fastapp.dev", description="Default from email")
    
    # OAuth Providers (for auth add-on)
    google_client_id: Optional[str] = Field(default=None, description="Google OAuth client ID")
    google_client_secret: Optional[SecretStr] = Field(default=None, description="Google OAuth client secret")
    github_client_id: Optional[str] = Field(default=None, description="GitHub OAuth client ID")
    github_client_secret: Optional[SecretStr] = Field(default=None, description="GitHub OAuth client secret")
    
    # Payment Processing (for commerce add-on)
    stripe_api_key: Optional[SecretStr] = Field(default=None, description="Stripe API key")
    stripe_webhook_secret: Optional[SecretStr] = Field(default=None, description="Stripe webhook secret")
    paypal_client_id: Optional[str] = Field(default=None, description="PayPal client ID")
    paypal_client_secret: Optional[SecretStr] = Field(default=None, description="PayPal client secret")
    
    # File Storage (for media add-on)
    storage_provider: Optional[str] = Field(default="local", description="Storage provider: local, s3, gcs, azure")
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS access key ID")
    aws_secret_access_key: Optional[SecretStr] = Field(default=None, description="AWS secret access key")
    aws_s3_bucket: Optional[str] = Field(default=None, description="AWS S3 bucket name")
    aws_region: str = Field(default="us-east-1", description="AWS region")
    
    # Analytics (for analytics add-on)
    google_analytics_id: Optional[str] = Field(default=None, description="Google Analytics tracking ID")
    mixpanel_token: Optional[SecretStr] = Field(default=None, description="Mixpanel project token")
    
    # ============================================================================
    # Feature Flags
    # ============================================================================
    
    enable_registration: bool = Field(default=True, description="Allow new user registration")
    enable_oauth: bool = Field(default=False, description="Enable OAuth login")
    enable_email_verification: bool = Field(default=False, description="Require email verification")
    enable_2fa: bool = Field(default=False, description="Enable two-factor authentication")
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    
    # ============================================================================
    # Validators
    # ============================================================================
    
    @validator("app_env")
    def validate_environment(cls, v):
        """Ensure environment is valid"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"app_env must be one of {allowed}")
        return v
    
    @validator("jwt_secret")
    def validate_jwt_secret_in_production(cls, v, values):
        """Ensure JWT secret is changed in production"""
        if values.get("app_env") == "production":
            default_secret = "change-this-secret-key-in-production"
            if v.get_secret_value() == default_secret:
                raise ValueError(
                    "JWT secret must be changed in production! "
                    "Set JWT_SECRET environment variable."
                )
        return v
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # ============================================================================
    # Helper Methods
    # ============================================================================
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.app_env == "production"
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.app_env == "development"
    
    def get_database_uri(self) -> Optional[str]:
        """Get the primary database URI (MongoDB or PostgreSQL)"""
        return self.mongo_uri or self.postgres_uri
    
    def has_email_configured(self) -> bool:
        """Check if email service is configured"""
        if self.email_provider == "smtp":
            return bool(self.smtp_host and self.smtp_username and self.smtp_password)
        elif self.email_provider == "sendgrid":
            return bool(self.sendgrid_api_key)
        elif self.email_provider == "mailgun":
            return bool(self.mailgun_api_key and self.mailgun_domain)
        return False
    
    def has_oauth_configured(self, provider: str) -> bool:
        """Check if OAuth provider is configured"""
        if provider == "google":
            return bool(self.google_client_id and self.google_client_secret)
        elif provider == "github":
            return bool(self.github_client_id and self.github_client_secret)
        return False
    
    def has_payment_configured(self, provider: str) -> bool:
        """Check if payment provider is configured"""
        if provider == "stripe":
            return bool(self.stripe_api_key)
        elif provider == "paypal":
            return bool(self.paypal_client_id and self.paypal_client_secret)
        return False
    
    def get_addon_config(self, addon_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific add-on.
        Returns only the settings relevant to that add-on.
        """
        configs = {
            "auth": {
                "jwt_secret": self.jwt_secret.get_secret_value() if self.jwt_secret else None,
                "jwt_algorithm": self.jwt_algorithm,
                "jwt_expiration_minutes": self.jwt_expiration_minutes,
                "enable_registration": self.enable_registration,
                "enable_oauth": self.enable_oauth,
                "enable_email_verification": self.enable_email_verification,
                "enable_2fa": self.enable_2fa,
                "password_min_length": self.password_min_length,
                "google_client_id": self.google_client_id,
                "google_client_secret": self.google_client_secret.get_secret_value() if self.google_client_secret else None,
                "github_client_id": self.github_client_id,
                "github_client_secret": self.github_client_secret.get_secret_value() if self.github_client_secret else None,
            },
            "commerce": {
                "stripe_api_key": self.stripe_api_key.get_secret_value() if self.stripe_api_key else None,
                "stripe_webhook_secret": self.stripe_webhook_secret.get_secret_value() if self.stripe_webhook_secret else None,
                "paypal_client_id": self.paypal_client_id,
                "paypal_client_secret": self.paypal_client_secret.get_secret_value() if self.paypal_client_secret else None,
            },
            "media": {
                "storage_provider": self.storage_provider,
                "aws_access_key_id": self.aws_access_key_id,
                "aws_secret_access_key": self.aws_secret_access_key.get_secret_value() if self.aws_secret_access_key else None,
                "aws_s3_bucket": self.aws_s3_bucket,
                "aws_region": self.aws_region,
            },
            "analytics": {
                "google_analytics_id": self.google_analytics_id,
                "mixpanel_token": self.mixpanel_token.get_secret_value() if self.mixpanel_token else None,
            },
            "lms": {
                "enable_certificates": True,
                "enable_discussions": True,
            }
        }
        return configs.get(addon_name, {})
    
    def validate_addon_requirements(self, addon_name: str) -> tuple[bool, Optional[str]]:
        """
        Validate that required configuration exists for an add-on.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if addon_name == "auth":
            if self.is_production() and self.jwt_secret.get_secret_value() == "change-this-secret-key-in-production":
                return False, "JWT secret must be set in production"
        
        elif addon_name == "commerce":
            if not (self.has_payment_configured("stripe") or self.has_payment_configured("paypal")):
                return False, "Commerce add-on requires Stripe or PayPal configuration"
        
        elif addon_name == "media":
            if self.storage_provider == "s3" and not self.aws_access_key_id:
                return False, "S3 storage requires AWS credentials"
        
        return True, None


# ============================================================================
# Global Settings Instance
# ============================================================================

# Create a singleton settings instance
settings = Settings()


# ============================================================================
# Helper Functions
# ============================================================================

def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings


def get_addon_settings(addon_name: str) -> Dict[str, Any]:
    """Get settings for a specific add-on"""
    return settings.get_addon_config(addon_name)


def validate_production_config() -> List[str]:
    """
    Validate configuration for production deployment.
    
    Returns:
        List of warning/error messages
    """
    warnings = []
    
    if settings.is_production():
        # Check critical security settings
        if settings.jwt_secret.get_secret_value() == "change-this-secret-key-in-production":
            warnings.append("⚠️  CRITICAL: JWT secret is using default value!")
        
        if settings.debug:
            warnings.append("⚠️  WARNING: Debug mode is enabled in production")
        
        if not settings.mongo_uri and not settings.postgres_uri:
            warnings.append("⚠️  WARNING: No database configured (using in-memory storage)")
        
        if settings.enable_oauth and not (settings.has_oauth_configured("google") or settings.has_oauth_configured("github")):
            warnings.append("⚠️  WARNING: OAuth enabled but no providers configured")
    
    return warnings