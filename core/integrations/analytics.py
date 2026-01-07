"""
Analytics Integration

Flattened module containing analytics client and consent manager.
"""

import json
import os
import hashlib
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, List, Any, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from core.services.auth.context import UserContext


# ===== CONSENT MANAGER =====

class PrivacyRegime(Enum):
    """Privacy regulation regimes."""
    GDPR = "gdpr"       # EU - strict opt-in
    CCPA = "ccpa"       # California - opt-out
    LGPD = "lgpd"       # Brazil - opt-in
    DEFAULT = "default"


class CookieCategory(str, Enum):
    """Cookie categories for consent management."""
    NECESSARY = "necessary"      # Essential cookies
    ANALYTICS = "analytics"      # Analytics and tracking
    MARKETING = "marketing"      # Marketing and advertising
    PREFERENCES = "preferences"  # User preferences
    FUNCTIONAL = "functional"    # Enhanced functionality


@dataclass
class ConsentState:
    """User consent state for cookie categories."""
    analytics: bool = False
    marketing: bool = False
    preferences: bool = False
    functional: bool = False
    necessary: bool = True  # Always true for essential cookies
    timestamp: Optional[datetime] = None
    regime: PrivacyRegime = PrivacyRegime.DEFAULT
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class ConsentManager:
    """
    Manages cookie consent based on privacy regulations.
    
    Handles consent state, banner display, and category permissions.
    """
    
    def __init__(self, user_context: 'UserContext'):
        self.user_context = user_context
        self.consent_state = ConsentState()
        self._detect_privacy_regime()
    
    def _detect_privacy_regime(self):
        """Detect applicable privacy regime based on user location."""
        # In a real implementation, this would use IP geolocation or user preferences
        # For now, default to GDPR for compliance
        self.consent_state.regime = PrivacyRegime.GDPR
    
    def update_consent(self, categories: Dict[str, bool]) -> ConsentState:
        """Update user consent for cookie categories."""
        for category, granted in categories.items():
            if hasattr(self.consent_state, category):
                setattr(self.consent_state, category, granted)
        
        self.consent_state.timestamp = datetime.utcnow()
        return self.consent_state
    
    def get_consent(self, category: CookieCategory) -> bool:
        """Get consent status for a specific category."""
        return getattr(self.consent_state, category.value, False)
    
    def should_show_banner(self) -> bool:
        """Determine if consent banner should be shown."""
        # Show banner if no consent has been given for non-necessary categories
        return not any([
            self.consent_state.analytics,
            self.consent_state.marketing,
            self.consent_state.preferences,
            self.consent_state.functional
        ])
    
    def get_consent_json(self) -> str:
        """Get consent state as JSON for client-side."""
        return json.dumps({
            'analytics': self.consent_state.analytics,
            'marketing': self.consent_state.marketing,
            'preferences': self.consent_state.preferences,
            'functional': self.consent_state.functional,
            'necessary': self.consent_state.necessary,
            'timestamp': self.consent_state.timestamp.isoformat(),
            'regime': self.consent_state.regime.value
        })
    
    def is_analytics_allowed(self) -> bool:
        """Check if analytics tracking is allowed."""
        return self.get_consent(CookieCategory.ANALYTICS)
    
    def is_marketing_allowed(self) -> bool:
        """Check if marketing tracking is allowed."""
        return self.get_consent(CookieCategory.MARKETING)


# ===== ANALYTICS CLIENT =====

class AnalyticsProvider(str, Enum):
    """Analytics service providers."""
    GOOGLE_ANALYTICS = "google_analytics"
    MIXPANEL = "mixpanel"
    AMPLITUDE = "amplitude"
    SEGMENT = "segment"
    CUSTOM = "custom"


@dataclass
class AnalyticsEvent:
    """Analytics event model."""
    event_name: str
    properties: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class UserProperties:
    """User properties for analytics."""
    user_id: str
    properties: Dict[str, Any]
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class AnalyticsClient:
    """
    Analytics client with consent management and multiple provider support.
    """
    
    def __init__(self, provider: AnalyticsProvider = AnalyticsProvider.GOOGLE_ANALYTICS):
        self.provider = provider
        self.tracking_id = os.getenv("ANALYTICS_TRACKING_ID")
        self.api_key = os.getenv("ANALYTICS_API_KEY")
        self.consent_manager: Optional[ConsentManager] = None
        self.enabled = bool(self.tracking_id)
        
        if not self.enabled:
            print("Analytics disabled - missing ANALYTICS_TRACKING_ID")
    
    def set_consent_manager(self, consent_manager: ConsentManager):
        """Set consent manager for privacy compliance."""
        self.consent_manager = consent_manager
    
    def _can_track(self) -> bool:
        """Check if tracking is allowed based on consent."""
        if not self.enabled:
            return False
        
        if self.consent_manager:
            return self.consent_manager.is_analytics_allowed()
        
        # If no consent manager, assume consent in development
        return os.getenv("ENVIRONMENT", "development") == "development"
    
    def track_event(self, event: AnalyticsEvent) -> bool:
        """Track an analytics event."""
        if not self._can_track():
            return False
        
        try:
            if self.provider == AnalyticsProvider.GOOGLE_ANALYTICS:
                return self._track_google_analytics(event)
            elif self.provider == AnalyticsProvider.MIXPANEL:
                return self._track_mixpanel(event)
            elif self.provider == AnalyticsProvider.CUSTOM:
                return self._track_custom(event)
            else:
                print(f"Provider {self.provider} not implemented")
                return False
        except Exception as e:
            print(f"Analytics tracking error: {e}")
            return False
    
    def identify_user(self, user_properties: UserProperties) -> bool:
        """Identify user with properties."""
        if not self._can_track():
            return False
        
        try:
            if self.provider == AnalyticsProvider.GOOGLE_ANALYTICS:
                return self._identify_google_analytics(user_properties)
            elif self.provider == AnalyticsProvider.MIXPANEL:
                return self._identify_mixpanel(user_properties)
            else:
                print(f"User identification not implemented for {self.provider}")
                return False
        except Exception as e:
            print(f"User identification error: {e}")
            return False
    
    def _track_google_analytics(self, event: AnalyticsEvent) -> bool:
        """Track event with Google Analytics."""
        # In production, use GA4 Measurement Protocol
        print(f"GA Event: {event.event_name}", event.properties)
        return True
    
    def _track_mixpanel(self, event: AnalyticsEvent) -> bool:
        """Track event with Mixpanel."""
        # In production, use Mixpanel API
        print(f"Mixpanel Event: {event.event_name}", event.properties)
        return True
    
    def _track_custom(self, event: AnalyticsEvent) -> bool:
        """Track event with custom analytics."""
        # Custom implementation - could log to database, send to webhook, etc.
        print(f"Custom Event: {event.event_name}", event.properties)
        return True
    
    def _identify_google_analytics(self, user_properties: UserProperties) -> bool:
        """Identify user with Google Analytics."""
        print(f"GA Identify: {user_properties.user_id}", user_properties.properties)
        return True
    
    def _identify_mixpanel(self, user_properties: UserProperties) -> bool:
        """Identify user with Mixpanel."""
        print(f"Mixpanel Identify: {user_properties.user_id}", user_properties.properties)
        return True
    
    def get_tracking_script(self) -> str:
        """Get client-side tracking script."""
        if not self.enabled or not self._can_track():
            return ""
        
        if self.provider == AnalyticsProvider.GOOGLE_ANALYTICS:
            return f"""
            <!-- Google Analytics -->
            <script async src="https://www.googletagmanager.com/gtag/js?id={self.tracking_id}"></script>
            <script>
                window.dataLayer = window.dataLayer || [];
                function gtag(){{dataLayer.push(arguments);}}
                gtag('js', new Date());
                gtag('config', '{self.tracking_id}');
            </script>
            """
        else:
            return f"<!-- Analytics script for {self.provider} -->"
    
    def hash_user_id(self, user_id: str) -> str:
        """Hash user ID for privacy compliance."""
        return hashlib.sha256(user_id.encode()).hexdigest()


# Factory functions
def create_analytics_client(provider: AnalyticsProvider = AnalyticsProvider.GOOGLE_ANALYTICS) -> AnalyticsClient:
    """Create an analytics client instance."""
    return AnalyticsClient(provider)


def create_consent_manager(user_context: 'UserContext') -> ConsentManager:
    """Create a consent manager instance."""
    return ConsentManager(user_context)


# Convenience functions
def track_event(event_name: str, properties: Dict[str, Any], **kwargs) -> bool:
    """Convenience function to track an event."""
    event = AnalyticsEvent(
        event_name=event_name,
        properties=properties,
        **kwargs
    )
    client = AnalyticsClient()
    return client.track_event(event)


def identify_user(user_id: str, properties: Dict[str, Any], **kwargs) -> bool:
    """Convenience function to identify a user."""
    user_props = UserProperties(
        user_id=user_id,
        properties=properties,
        **kwargs
    )
    client = AnalyticsClient()
    return client.identify_user(user_props)


__all__ = [
    # Consent Manager
    'PrivacyRegime',
    'CookieCategory',
    'ConsentState',
    'ConsentManager',
    
    # Analytics Client
    'AnalyticsProvider',
    'AnalyticsEvent',
    'UserProperties',
    'AnalyticsClient',
    
    # Factory
    'create_analytics_client',
    'create_consent_manager',
    
    # Convenience
    'track_event',
    'identify_user',
]
