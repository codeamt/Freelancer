# app/core/services/auth/providers/adapters/github.py
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