#!/usr/bin/env python3
"""
Test authentication endpoints to troubleshoot login issues.
"""

import asyncio
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv('app.config.env')

import httpx
from core.utils.logger import get_logger

logger = get_logger(__name__)

# Test credentials
TEST_CREDENTIALS = {
    "email": "admin@test.com",
    "password": "Admin123!"
}

BASE_URL = "http://localhost:5001"


async def test_login_endpoint():
    """Test the login endpoint directly"""
    print("\n🔍 Testing Login Endpoint")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Test login
        login_data = {
            "email": TEST_CREDENTIALS["email"],
            "password": TEST_CREDENTIALS["password"]
        }
        
        print(f"\n📤 Sending login request:")
        print(f"   URL: {BASE_URL}/auth/login")
        print(f"   Email: {TEST_CREDENTIALS['email']}")
        print(f"   Password: {TEST_CREDENTIALS['password']}")
        
        try:
            response = await client.post(
                f"{BASE_URL}/auth/login",
                data=login_data,  # Using form data
                follow_redirects=False
            )
            
            print(f"\n📥 Response received:")
            print(f"   Status Code: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            
            if response.headers.get("content-type", "").startswith("text/html"):
                print(f"   Response is HTML (length: {len(response.text)} bytes)")
                # Check if it's a redirect to dashboard
                if response.status_code == 302:
                    location = response.headers.get("location", "")
                    print(f"   Redirect Location: {location}")
                    if "dashboard" in location:
                        print("   ✅ Login successful - redirecting to dashboard")
                    else:
                        print(f"   ⚠️ Unexpected redirect to: {location}")
            else:
                try:
                    json_response = response.json()
                    print(f"   JSON Response: {json.dumps(json_response, indent=2)}")
                except:
                    print(f"   Text Response: {response.text[:500]}...")
            
            # Check for auth token in cookies
            cookies = response.cookies
            if "auth_token" in cookies:
                print(f"\n✅ Auth token found in cookie")
                token = cookies["auth_token"]
                print(f"   Token (first 50 chars): {token[:50]}...")
            else:
                print(f"\n❌ No auth token in cookies")
                print(f"   Available cookies: {list(cookies.keys())}")
            
        except httpx.ConnectError:
            print(f"\n❌ Connection Error: Could not connect to {BASE_URL}")
            print("   Make sure the app is running on http://localhost:5001")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


async def test_register_endpoint():
    """Test the register endpoint"""
    print("\n🔍 Testing Register Endpoint")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Test registration with new user
        register_data = {
            "email": "testuser@example.com",
            "password": "TestUser123!",
            "confirm_password": "TestUser123!"
        }
        
        print(f"\n📤 Sending register request:")
        print(f"   URL: {BASE_URL}/auth/register")
        print(f"   Email: {register_data['email']}")
        
        try:
            response = await client.post(
                f"{BASE_URL}/auth/register",
                data=register_data,
                follow_redirects=False
            )
            
            print(f"\n📥 Response received:")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 302:
                location = response.headers.get("location", "")
                print(f"   Redirect Location: {location}")
                if "login" in location:
                    print("   ✅ Registration successful - redirecting to login")
            else:
                print(f"   Response: {response.text[:500]}...")
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


async def test_user_verification():
    """Check if test user exists in database"""
    print("\n🔍 Verifying User in Database")
    print("=" * 60)
    
    try:
        from core.db.adapters import PostgresAdapter
        import os
        
        # Connect to database
        postgres_url = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/app_db")
        postgres = PostgresAdapter(connection_string=postgres_url, min_size=10, max_size=20)
        
        # Check user exists
        query = "SELECT email, role, roles, created_at FROM users WHERE email = $1"
        result = await postgres.fetch_one(query, TEST_CREDENTIALS["email"])
        
        if result:
            print(f"\n✅ User found in database:")
            print(f"   Email: {result['email']}")
            print(f"   Role: {result['role']}")
            print(f"   Roles: {result['roles']}")
            print(f"   Created At: {result['created_at']}")
            
            # Check password hash
            query = "SELECT password_hash FROM users WHERE email = $1"
            pw_result = await postgres.fetch_one(query, TEST_CREDENTIALS["email"])
            if pw_result:
                print(f"   Password Hash: {pw_result['password_hash'][:50]}...")
                
                # Verify password
                from core.utils.security import verify_password
                if verify_password(TEST_CREDENTIALS["password"], pw_result['password_hash']):
                    print(f"   ✅ Password verification successful")
                else:
                    print(f"   ❌ Password verification failed")
        else:
            print(f"\n❌ User not found in database: {TEST_CREDENTIALS['email']}")
            
    except Exception as e:
        print(f"\n❌ Database error: {str(e)}")


async def test_auth_service_directly():
    """Test auth service directly"""
    print("\n🔍 Testing Auth Service Directly")
    print("=" * 60)
    
    try:
        from core.services.auth.auth_service import AuthService
        from core.db.repositories.user_repository import UserRepository
        from core.db.adapters import PostgresAdapter
        import os
        
        # Initialize services
        postgres_url = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/app_db")
        postgres = PostgresAdapter(connection_string=postgres_url, min_size=10, max_size=20)
        user_repo = UserRepository(postgres)
        auth_service = AuthService(user_repository=user_repo)
        
        # Test login
        print(f"\n🔐 Testing login with auth service...")
        from core.services.auth.auth_service import LoginRequest
        login_request = LoginRequest(
            username=TEST_CREDENTIALS["email"],
            password=TEST_CREDENTIALS["password"]
        )
        login_result = await auth_service.login(login_request)
        
        if login_result and login_result.access_token:
            print(f"   ✅ Login successful via auth service")
            print(f"   Token (first 50 chars): {login_result.access_token[:50]}...")
            
            # Verify token
            payload = await auth_service.jwt.verify(login_result.access_token)
            if payload:
                print(f"   ✅ Token verification successful")
                print(f"   User ID: {payload.get('user_id')}")
                print(f"   Role: {payload.get('role')}")
                print(f"   Roles: {payload.get('roles')}")
            else:
                print(f"   ❌ Token verification failed")
        else:
            print(f"   ❌ Login failed via auth service")
            print(f"   Error: {login_result.error if hasattr(login_result, 'error') else 'Unknown'}")
            
    except Exception as e:
        print(f"\n❌ Auth service error: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests"""
    print("\n🚀 Authentication Troubleshooting")
    print("=" * 60)
    print(f"Testing with credentials:")
    print(f"   Email: {TEST_CREDENTIALS['email']}")
    print(f"   Password: {TEST_CREDENTIALS['password']}")
    
    # Test 1: Check user in database
    await test_user_verification()
    
    # Test 2: Test auth service directly
    await test_auth_service_directly()
    
    # Test 3: Test login endpoint
    await test_login_endpoint()
    
    # Test 4: Test register endpoint
    await test_register_endpoint()
    
    print("\n✨ Troubleshooting complete!")


if __name__ == "__main__":
    asyncio.run(main())
