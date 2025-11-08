import os
from app.core.app import app
from app.core.services.oauth import GoogleOAuthService

# Set dummy environment variables for testing
os.environ['GOOGLE_CLIENT_ID'] = 'dummy_client_id'
os.environ['GOOGLE_CLIENT_SECRET'] = 'dummy_client_secret'

# Reinitialize the app with OAuth
def test_oauth_routes():
    # Initialize OAuth service
    oauth_service = GoogleOAuthService(app)
    
    # Check if OAuth routes are registered
    oauth_routes = [route.path for route in app.routes if 'auth' in route.path and ('google' in route.path or 'redirect' in route.path or 'logout' in route.path)]
    print("OAuth routes:", oauth_routes)
    
    return oauth_routes

if __name__ == "__main__":
    routes = test_oauth_routes()
    print(f"Found {len(routes)} OAuth-related routes")
