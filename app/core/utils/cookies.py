from dataclasses import dataclass
from typing import Optional
from app.settings import Settings

@dataclass
class CookieConfig:
      max_age: Optional[int] = None
      httponly: bool = True
      secure: bool = True
      samesite: str = 'Lax'
      path: str = '/'


class SecureCookieManager:
    def __init__(self, user_context, settings: Settings):
        self.context = user_context
        self.settings = settings

    def set_session_cookie(self, key: str, value: str, max_age: int = 86400):
        """Set a session cookie with security best practices"""
        self.context.set_cookie(
            key, value,
            max_age=max_age,
            httponly=True,
            secure=self.settings.is_production(),
            samesite='Lax',
            path='/'
        )

    def set_tracking_cookie(self, key: str, value: str):
        """Set a tracking cookie (can be accessed by JS)"""
        self.context.set_cookie(
            key, value,
            max_age=31536000,  # 1 year
            httponly=False,
              secure=self.settings.is_production(),
              samesite='Lax'
          )
      
    def set_cart_cookie(self, key: str, value: str, persistent: bool = False):
        """Set cart cookie - session or persistent based on consent"""
        self.context.set_cookie(
            key, value,
            max_age=86400 if persistent else None,  # 24hr or session
            httponly=True,
            secure=self.settings.is_production(),
            samesite='Strict',  # Strict for sensitive data
            path='/'
        )