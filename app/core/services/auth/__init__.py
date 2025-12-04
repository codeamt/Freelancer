"""Core Auth Service - Shared authentication functionality"""
from .auth_service import AuthService
from .user_service import UserService
from .utils import get_current_user


from .providers.jwt import JWTProvider
from .providers.oauth import OAuthProvider
from typing import Optional

class AuthService:
    def __init__(self):
        self.jwt = JWTProvider()
        self.oauth = OAuthProvider()
    
    async def authenticate(self, token: str) -> Optional[dict]:
        """Core authentication logic"""
        return await self.jwt.verify(token)
    
    # Shared utilities
    async def has_permission(self, user: dict, permission: str) -> bool:
        return permission in user.get('permissions', [])

__all__ = ['AuthService', 'UserService', 'JWTProvider', 'security','get_current_user']
