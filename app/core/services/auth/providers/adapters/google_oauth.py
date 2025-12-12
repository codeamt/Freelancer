from fasthtml.oauth import GoogleAppClient, OAuth
from fastapi import Request
from starlette.responses import RedirectResponse
import os
from core.utils.logger import get_logger

logger = get_logger(__name__)


class GoogleOAuthService(OAuth):
    """
    Google OAuth Service for authentication.
    
    Provides OAuth 2.0 authentication flow with Google.
    """
    
    def __init__(self, app):
        client = GoogleAppClient(
            os.getenv("GOOGLE_CLIENT_ID"),
            os.getenv("GOOGLE_CLIENT_SECRET"),
            redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
        )
        super().__init__(app, client)
    
    def get_auth(self, info, ident, session, state):
        """
        Handle successful OAuth authentication.
        
        Args:
            info: OAuth token information
            ident: User identity information
            session: Session object
            state: OAuth state parameter
        """
        session['google_token'] = info.get('access_token')
        session['user_info'] = info
        
        logger.info(f"User authenticated via Google OAuth: {ident}")
        
        return RedirectResponse('/', status_code=303)

    def get_error(self, err, session):
        """
        Handle OAuth errors.
        
        Args:
            err: Error information
            session: Session object
        """
        logger.error(f"OAuth error: {err}")
        session['oauth_error'] = str(err)
        return RedirectResponse('/auth/login', status_code=303)
