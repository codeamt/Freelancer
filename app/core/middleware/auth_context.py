from fasthtml.common import *

from starlette.middleware.base import BaseHTTPMiddleware

from core.services.auth.auth_service import AnonymousUser
from core.services.auth.context import (
    create_anonymous_context,
    create_user_context,
    current_user_context,
)
from core.services.auth.helpers import get_current_user_from_request


def set_response_cookies(request, response):
    user_context = current_user_context.get(None)
    if not user_context:
        return response

    for key, (value, kwargs) in user_context._outgoing_cookies.items():
        response.set_cookie(key, value, **kwargs)

    return response


class AuthContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = None
        user_context = None

        try:
            auth_service = getattr(request.app.state, "auth_service", None)
            if auth_service is None:
                user = AnonymousUser()
            else:
                user = await get_current_user_from_request(request, auth_service)

            if isinstance(user, AnonymousUser) or not user:
                user_context = create_anonymous_context(request)
            else:
                user_context = create_user_context(user, request)

            token = current_user_context.set(user_context)

            response = await call_next(request)
            return set_response_cookies(request, response)
        finally:
            if token is not None:
                current_user_context.reset(token)


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