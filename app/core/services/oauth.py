from fasthtml.oauth import GoogleAppClient, OAuth
from fastapi import Request
from starlette.responses import RedirectResponse
import os


class GoogleOAuthService(OAuth):
    def __init__(self, app):
        # Initialize Google OAuth client
        client = GoogleAppClient(
            os.getenv("GOOGLE_CLIENT_ID"),
            os.getenv("GOOGLE_CLIENT_SECRET"),
            redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
        )
        super().__init__(app, client)
    
    def get_auth(self, info, ident, session, state):
        # Store user info and token in session
        session['google_token'] = info.get('access_token')
        session['user_info'] = info
        
        # You can add additional logic here such as:
        # - Saving user to database
        # - Checking user permissions
        # - Setting up user preferences
        
        # Redirect to home page after successful authentication
        return RedirectResponse('/', status_code=303)

    def get_error(self, err, session):
        # Handle OAuth errors
        print(f"OAuth error: {err}")
        session['oauth_error'] = str(err)
        return RedirectResponse('/auth/login', status_code=303)
