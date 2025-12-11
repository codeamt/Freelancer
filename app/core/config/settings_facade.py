from app.settings import Settings
from app.core.auth.context import UserContext
  
class SettingsFacade:
    def __init__(self, user_context: UserContext, global_settings: Settings):
        self._user = user_context
        self._global = global_settings
      
    @property
    def analytics_tracking_enabled(self) -> bool:
        """Check if analytics tracking is allowed for this user"""
        tracking_opt_out = self._user.cookies.get('tracking_opt_out')
          
        # SuperAdmins might be tracked for security auditing
        if tracking_opt_out == 'true' and self._user.role != 'admin':
            return False
          
        return self._global.google_analytics_id is not None
      
    @property
    def can_modify_commerce_settings(self) -> bool:
        """Only admins can modify commerce settings"""
        return self._user.role == 'admin'
      
    @property
    def available_payment_methods(self) -> list:
        """Return payment methods available to this user"""
        methods = []
        if self._global.stripe_api_key:
            methods.append('stripe')
        if self._global.paypal_client_id:
            methods.append('paypal')
        return methods
      
    def get_feature_flag(self, flag_name: str) -> bool:
        """Get feature flag value based on role"""
        # Example: admins might see beta features
        if flag_name == 'beta_editor' and self._user.role == 'admin':
            return True
        return getattr(self._global, flag_name, False)