from fasthtml.common import *
from app.core.auth.context import UserContext, current_user_context

from app.core.config.settings_facade import SettingsFacade
from app.settings import settings

async def inject_settings_facade(request):
    user_context = current_user_context.get()
    settings_facade = SettingsFacade(user_context, settings)
    # Store in context or request state
    pass



async def inject_user_context(request):
    """Create UserContext from request and store in context var"""
    cookies = dict(request.cookies)


    # Authenticate user
    auth_token = cookies.get('auth_token') or request.headers.get('Authorization')
    user_data = await authenticate_token(auth_token)

    # Load permissions based on role
    permissions = await get_user_permissions(user_data['user_id'], user_data['role'])

    # Create and store context
    user_context = UserContext(
        user_id=user_data['user_id'],
        role=user_data['role'],
        permissions=permissions,
        request_cookies=cookies,
        ip_address=request.client.host
    )

    current_user_context.set(user_context)

async def set_response_cookies(request, response):
      """Apply outgoing cookies from UserContext to response"""
      user_context = current_user_context.get(None)
      if not user_context:
          return response
      
      for key, (value, kwargs) in user_context._outgoing_cookies.items():
          response.set_cookie(key, value, **kwargs)
      
      return response


'''
Use Facade in Services

class AnalyticsClient:
      def __init__(self, settings_facade: SettingsFacade):
          self.settings = settings_facade
      
      async def track_event(self, event):
          if not self.settings.analytics_tracking_enabled:
              return
          # Track event
'''