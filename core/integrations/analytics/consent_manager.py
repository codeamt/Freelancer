"""
Cookie Consent Manager - Handles GDPR/CCPA compliance.

Manages user consent for different cookie categories and privacy regimes.
"""
import json
from datetime import datetime
from enum import Enum
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from core.services.auth.context import UserContext


class PrivacyRegime(Enum):
    """Privacy regulation regimes."""
    GDPR = "gdpr"       # EU - strict opt-in
    CCPA = "ccpa"       # California - opt-out
    LGPD = "lgpd"       # Brazil - opt-in
    DEFAULT = "default"


class ConsentManager:
    """
    Manages cookie consent based on privacy regulations.
    
    Handles consent state, banner display, and category permissions.
    """
    
    def __init__(self, user_context: 'UserContext'):
        """
        Initialize consent manager.
        
        Args:
            user_context: Current user context with cookies
        """
        self.context = user_context
      
    def get_consent_state(self) -> Dict[str, bool]:
        """
        Get current consent state from cookies.
        
        Returns:
            Dictionary of consent categories and their status
        """
        consent_json = self.context.get_cookie('cookie_consent')
        if not consent_json:
            return {'necessary': True}
          
        try:
            return json.loads(consent_json)
        except json.JSONDecodeError:
            return {'necessary': True}
      
    def set_consent(self, categories: Dict[str, bool]):
        """
        Set user consent preferences.
        
        Args:
            categories: Dictionary of category names to consent status
        """
        consent = {
            'necessary': True,  # Always true - required for functionality
            'analytics': categories.get('analytics', False),
            'marketing': categories.get('marketing', False),
            'functional': categories.get('functional', False),
            'timestamp': datetime.utcnow().isoformat()
        }
          
        # Store consent in cookie
        self.context.set_cookie(
            'cookie_consent',
            json.dumps(consent),
            max_age=31536000,  # 1 year
            httponly=True,
            samesite='Lax'
        )
      
    def requires_consent_banner(self) -> bool:
        """
        Check if consent banner should be displayed.
        
        Returns:
            True if user hasn't set consent preferences yet
        """
        return 'cookie_consent' not in self.context.request_cookies
      
    def has_analytics_consent(self) -> bool:
        """
        Check if user has consented to analytics cookies.
        
        Returns:
            True if analytics consent granted
        """
        consent_state = self.get_consent_state()
        return consent_state.get('analytics', False)
    
    def has_marketing_consent(self) -> bool:
        """
        Check if user has consented to marketing cookies.
        
        Returns:
            True if marketing consent granted
        """
        consent_state = self.get_consent_state()
        return consent_state.get('marketing', False)