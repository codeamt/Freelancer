# app/core/services/auth/providers/adapters/google.py
import httpx
from typing import Dict, Optional
from fasthtml.common import Request
from core.utils.logger import get_logger

logger = get_logger(__name__)

class GoogleOAuth:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    async def validate(self, request: Request) -> Optional[Dict]:
        """Handle FastHTML request object"""
        try:
            code = request.params.get("code")
            if not code:
                return None
                
            token = await self._exchange_code(code)
            return await self._get_user_info(token)
        except Exception as e:
            logger.error(f"Google OAuth error: {e}")
            return None

    async def _exchange_code(self, code: str) -> str:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            response.raise_for_status()
            return response.json().get("access_token")

    async def _get_user_info(self, token: str) -> Dict:
        """Get standardized user info from Google"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            data = response.json()
            return {
                "id": data["id"],
                "email": data["email"],
                "name": data.get("name", ""),
                "picture": data.get("picture", ""),
                "token": token
            }