#!/usr/bin/env python3
"""
Create test users for all roles in the system.

This script creates test users with different role combinations
for development and testing purposes.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.services.auth.user_service import UserService
from core.services.auth.models import UserRole
from core.utils.logger import get_logger

logger = get_logger(__name__)

# Test user credentials
TEST_USERS = [
    {
        "email": "superadmin@test.com",
        "password": "SuperAdmin123!",
        "roles": [UserRole.SUPER_ADMIN],
        "description": "Super Admin - Full system access"
    },
    {
        "email": "admin@test.com",
        "password": "Admin123!",
        "roles": [UserRole.ADMIN],
        "description": "Admin - Administrative access"
    },
    {
        "email": "instructor@test.com",
        "password": "Instructor123!",
        "roles": [UserRole.INSTRUCTOR],
        "description": "Instructor - Course creation and management"
    },
    {
        "email": "editor@test.com",
        "password": "Editor123!",
        "roles": [UserRole.EDITOR],
        "description": "Editor - Content editing access"
    },
    {
        "email": "student@test.com",
        "password": "Student123!",
        "roles": [UserRole.STUDENT],
        "description": "Student - Course enrollment"
    },
    {
        "email": "user@test.com",
        "password": "User123!",
        "roles": [UserRole.USER],
        "description": "User - Basic access"
    },
    {
        "email": "guest@test.com",
        "password": "Guest123!",
        "roles": [UserRole.GUEST],
        "description": "Guest - Limited access"
    },
    # Multi-role users
    {
        "email": "admin-instructor@test.com",
        "password": "MultiRole1!",
        "roles": [UserRole.ADMIN, UserRole.INSTRUCTOR],
        "description": "Admin + Instructor - Multiple roles"
    },
    {
        "email": "instructor-student@test.com",
        "password": "MultiRole2!",
        "roles": [UserRole.INSTRUCTOR, UserRole.STUDENT],
        "description": "Instructor + Student - Can teach and learn"
    },
    {
        "email": "editor-instructor@test.com",
        "password": "MultiRole3!",
        "roles": [UserRole.EDITOR, UserRole.INSTRUCTOR],
        "description": "Editor + Instructor - Content creation"
    },
    {
        "email": "all-roles@test.com",
        "password": "AllRoles123!",
        "roles": [
            UserRole.SUPER_ADMIN,
            UserRole.ADMIN,
            UserRole.INSTRUCTOR,
            UserRole.EDITOR,
            UserRole.STUDENT,
            UserRole.USER,
            UserRole.GUEST
        ],
        "description": "All Roles - Full access testing"
    },
    # Add-on specific roles
    {
        "email": "blog-admin@test.com",
        "password": "BlogAdmin123!",
        "roles": [UserRole.USER, UserRole.BLOG_ADMIN],
        "description": "Blog Admin - Blog management"
    },
    {
        "email": "blog-author@test.com",
        "password": "BlogAuthor123!",
        "roles": [UserRole.USER, UserRole.BLOG_AUTHOR],
        "description": "Blog Author - Can write posts"
    },
    {
        "email": "lms-admin@test.com",
        "password": "LMSAdmin123!",
        "roles": [UserRole.USER, UserRole.LMS_ADMIN],
        "description": "LMS Admin - Learning system management"
    },
    # Legacy roles (for backward compatibility testing)
    {
        "email": "member@test.com",
        "password": "Member123!",
        "roles": [UserRole.MEMBER],
        "description": "Member - Legacy role (maps to USER)"
    },
    {
        "email": "site-owner@test.com",
        "password": "SiteOwner123!",
        "roles": [UserRole.SITE_OWNER],
        "description": "Site Owner - Legacy role (maps to ADMIN)"
    },
    {
        "email": "support@test.com",
        "password": "Support123!",
        "roles": [UserRole.SUPPORT_STAFF],
        "description": "Support Staff - Legacy role (maps to SUPER_ADMIN)"
    }
]


async def create_test_users():
    """Create all test users"""
    print("\n🔧 Creating test users for development...\n")
    
    # Initialize repositories and services
    from core.db.repositories.user_repository import UserRepository
    from core.db.adapters import PostgresAdapter
    import os
    
    # Get database connection
    postgres_url = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/app_db")
    postgres = PostgresAdapter(connection_string=postgres_url, min_size=10, max_size=20)
    
    # Initialize user repository
    user_repo = UserRepository(postgres)
    
    # Initialize user service
    user_service = UserService(user_repository=user_repo)
    
    created_users = []
    failed_users = []
    
    for user_data in TEST_USERS:
        email = user_data["email"]
        password = user_data["password"]
        roles = user_data["roles"]
        description = user_data["description"]
        
        try:
            # Check if user already exists
            existing_user = await user_service.get_user_by_email(email)
            
            if existing_user:
                print(f"⚠️  User already exists: {email}")
                # Update roles if needed
                if set(existing_user.roles) != set(roles):
                    await user_service.update_user_roles(existing_user.id, roles)
                    print(f"   ✓ Updated roles for {email}")
                created_users.append(user_data)
                continue
            
            # Create new user
            user = await user_service.create_user(
                email=email,
                password=password,
                roles=roles,
                is_verified=True  # Auto-verify for testing
            )
            
            if user:
                print(f"✅ Created: {email}")
                print(f"   Roles: {', '.join([r.value for r in roles])}")
                print(f"   {description}")
                created_users.append(user_data)
            else:
                print(f"❌ Failed to create: {email}")
                failed_users.append(user_data)
                
        except Exception as e:
            print(f"❌ Error creating {email}: {str(e)}")
            failed_users.append(user_data)
        
        print()
    
    # Summary
    print("=" * 60)
    print(f"📊 SUMMARY:")
    print(f"   ✅ Created/Updated: {len(created_users)} users")
    print(f"   ❌ Failed: {len(failed_users)} users")
    print("=" * 60)
    
    if created_users:
        print("\n📋 TEST CREDENTIALS:")
        print("-" * 60)
        for user in created_users:
            print(f"\n👤 {user['description']}")
            print(f"   Email: {user['email']}")
            print(f"   Password: {user['password']}")
            print(f"   Roles: {', '.join([r.value for r in user['roles']])}")
    
    if failed_users:
        print("\n❌ Failed Users:")
        for user in failed_users:
            print(f"   - {user['email']}: {user.get('error', 'Unknown error')}")
    
    print("\n✨ Test users ready for development!")
    print("\n📌 Quick Access URLs:")
    print("   - Login: http://localhost:5001/auth/login")
    print("   - Register: http://localhost:5001/auth/register")
    print("   - Dashboard: http://localhost:5001/dashboard")
    print("   - Role Demo: http://localhost:5001/demo/roles")
    print("   - Admin Panel: http://localhost:5001/admin")


async def reset_test_users():
    """Delete all test users"""
    print("\n🗑️  Resetting test users...")
    
    # Initialize repositories and services
    from core.db.repositories.user_repository import UserRepository
    from core.db.adapters import PostgresAdapter
    import os
    
    # Get database connection
    postgres_url = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/app_db")
    postgres = PostgresAdapter(connection_string=postgres_url, min_size=10, max_size=20)
    
    # Initialize user repository
    user_repo = UserRepository(postgres)
    
    # Initialize user service
    user_service = UserService(user_repository=user_repo)
    
    deleted_count = 0
    
    for user_data in TEST_USERS:
        email = user_data["email"]
        try:
            user = await user_service.get_user_by_email(email)
            if user:
                await user_service.delete_user(user.id)
                print(f"✅ Deleted: {email}")
                deleted_count += 1
        except Exception as e:
            print(f"❌ Failed to delete {email}: {str(e)}")
    
    print(f"\n📊 Deleted {deleted_count} test users")


async def main():
    """Main script function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage test users for development")
    parser.add_argument(
        "action",
        choices=["create", "reset", "list"],
        help="Action to perform"
    )
    
    args = parser.parse_args()
    
    if args.action == "create":
        await create_test_users()
    elif args.action == "reset":
        await reset_test_users()
        await create_test_users()
    elif args.action == "list":
        print("\n📋 Available Test Users:")
        print("-" * 60)
        for user in TEST_USERS:
            print(f"\n👤 {user['description']}")
            print(f"   Email: {user['email']}")
            print(f"   Roles: {', '.join([r.value for r in user['roles']])}")


if __name__ == "__main__":
    # Set environment for development
    os.environ["PYTHONPATH"] = str(Path(__file__).parent.parent)
    
    # Run the script
    asyncio.run(main())
