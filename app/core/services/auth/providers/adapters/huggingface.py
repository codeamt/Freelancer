# app/core/services/auth/providers/adapters/huggingface.py
from typing import Dict, Optional
from huggingface_hub import HfOAuthClient
from core.utils.logger import get_logger

logger = get_logger(__name__)

class HuggingFaceOAuth:
    def __init__(self, client_id: str, client_secret: str):
        self.oauth = HfOAuthClient(
            client_id=client_id,
            client_secret=client_secret
        )

    async def validate(self, request) -> Optional[Dict]:
        """Extract and validate OAuth info from FastHTML request"""
        try:
            # Parse OAuth data from request
            oauth_info = self.oauth.parse_request(request)
            if not oauth_info:
                return None
                
            return {
                "id": oauth_info.user_info.sub,
                "email": oauth_info.user_info.email,
                "name": oauth_info.user_info.preferred_username,
                "token": oauth_info.access_token,
                "expires_at": oauth_info.expires_at
            }
        except Exception as e:
            logger.error(f"HuggingFace OAuth error: {e}")
            return None