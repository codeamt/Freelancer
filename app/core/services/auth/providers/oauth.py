# app/core/services/auth/providers/oauth.py
from typing import Dict, Optional
from fasthtml.common import Request

class OAuthProvider:
    def __init__(self):
        self.adapters = {}

    def register(self, name: str, adapter):
        """Register OAuth adapter"""
        self.adapters[name] = adapter

    async def authenticate(self, request: Request, provider: str) -> Optional[Dict]:
        """Main authentication interface"""
        if provider not in self.adapters:
            raise ValueError(f"Unsupported provider: {provider}")
        return await self.adapters[provider].validate(request)