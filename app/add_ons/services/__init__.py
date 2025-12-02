"""
Base Service Classes

Abstract base classes for common services that can be implemented
by specific add-ons or client projects.

Available base services:
- auth_base: Authentication service interface
- oauth_base: OAuth provider integration
- email_base: Email service interface
- event_bus_base: Event-driven architecture
- analytics_base: Analytics tracking
- notifications_base: Push/email notifications
- recommender_base: Recommendation engine
- stripe_base: Payment processing
- storage_base: File storage (S3, local, etc.)

Each base class defines the interface that implementations should follow.
"""
