import json
from datetime import datetime
from enum import Enum

class PrivacyRegime(Enum):
    GDPR = "gdpr"       # EU - strict opt-in
    CCPA = "ccpa"       # California - opt-out
    LGPD = "lgpd"       # Brazil - opt-in
    DEFAULT = "default"

class ConsentManager:
    def __init__(self, user_context):
        self.context = user_context
      
    def get_consent_state(self) -> dict:
        consent_json = self.context.get_cookie('cookie_consent')
        if not consent_json:
            return {'necessary': True}
          
        return json.loads(consent_json)
      
    def set_consent(self, categories: dict):
        consent = {
            'necessary': True,
            'analytics': categories.get('analytics', False),
            'marketing': categories.get('marketing', False),
            'functional': categories.get('functional', False),
            'timestamp': datetime.utcnow().isoformat()
        }
          
        cookie_mgr = SecureCookieManager(self.context, settings)
        cookie_mgr.set_session_cookie(
            'cookie_consent',
            json.dumps(consent),
            max_age=31536000  # 1 year
        )
      
    def requires_consent_banner(self) -> bool:
        return 'cookie_consent' not in self.context.cookies
      
    def has_analytics_consent(self) -> bool:
        consent_state = self.get_consent_state()
        return consent_state.get('analytics', False)