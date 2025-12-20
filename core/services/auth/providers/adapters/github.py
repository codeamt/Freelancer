# app/core/services/auth/providers/adapters/github.py
import httpx
from typing import Dict, Optional
from fasthtml.common import Request
from core.utils.logger import get_logger

logger = get_logger(__name__)

class GitHubOAuth:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    async def validate(self, request: Request) -> Optional[Dict]:
        """Handle FastHTML request object"""
        try:
            code = request.params.get("code")
            if not code:
                return None
                
            token = await self._exchange_code(code)
            return await self._get_user_info(token)
        except Exception as e:
            logger.error(f"GitHub OAuth error: {e}")
            return None

    async def _exchange_code(self, code: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code
                },
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            return response.json().get("access_token")

    async def _get_user_info(self, token: str) -> Dict:
        """Get standardized user info from GitHub"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Get email (may need separate call if email is private)
            email = data.get("email")
            if not email:
                email_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                if email_response.status_code == 200:
                    emails = email_response.json()
                    primary = next((e for e in emails if e.get("primary")), None)
                    email = primary["email"] if primary else (emails[0]["email"] if emails else None)
            
            return {
                "id": str(data["id"]),
                "email": email,
                "name": data.get("name") or data.get("login", ""),
                "picture": data.get("avatar_url", ""),
                "token": token
            }