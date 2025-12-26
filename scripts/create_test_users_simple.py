#!/usr/bin/env python3
"""
Create test users for all roles in the system (simplified version).

This script creates test users with different role combinations
for development and testing purposes.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.db.adapters import PostgresAdapter
from core.utils.logger import get_logger
from core.utils.security import hash_password

logger = get_logger(__name__)

# Test user credentials
TEST_USERS = [
    {
        "email": "superadmin@test.com",
        "password": "SuperAdmin123!",
        "role": "super_admin",
        "description": "Super Admin - Full system access"
    },
    {
        "email": "admin@test.com",
        "password": "Admin123!",
        "role": "admin",
        "description": "Admin - Administrative access"
    },
    {
        "email": "instructor@test.com",
        "password": "Instructor123!",
        "role": "instructor",
        "description": "Instructor - Course creation and management"
    },
    {
        "email": "editor@test.com",
        "password": "Editor123!",
        "role": "editor",
        "description": "Editor - Content editing access"
    },
    {
        "email": "student@test.com",
        "password": "Student123!",
        "role": "student",
        "description": "Student - Course enrollment"
    },
    {
        "email": "user@test.com",
        "password": "User123!",
        "role": "user",
        "description": "User - Basic access"
    },
    {
        "email": "guest@test.com",
        "password": "Guest123!",
        "role": "guest",
        "description": "Guest - Limited access"
    },
    # Multi-role users (using primary role for now)
    {
        "email": "admin-instructor@test.com",
        "password": "MultiRole1!",
        "role": "admin",  # Primary role
        "description": "Admin + Instructor - Multiple roles"
    },
    {
        "email": "instructor-student@test.com",
        "password": "MultiRole2!",
        "role": "instructor",  # Primary role
        "description": "Instructor + Student - Can teach and learn"
    },
    {
        "email": "editor-instructor@test.com",
        "password": "MultiRole3!",
        "role": "instructor",  # Primary role
        "description": "Editor + Instructor - Content creation"
    },
    # Add-on specific roles
    {
        "email": "blog-admin@test.com",
        "password": "BlogAdmin123!",
        "role": "blog_admin",
        "description": "Blog Admin - Blog management"
    },
    {
        "email": "blog-author@test.com",
        "password": "BlogAuthor123!",
        "role": "blog_author",
        "description": "Blog Author - Can write posts"
    },
    {
        "email": "lms-admin@test.com",
        "password": "LMSAdmin123!",
        "role": "lms_admin",
        "description": "LMS Admin - Learning system management"
    }
]


async def create_test_users():
    """Create all test users"""
    print("\n🔧 Creating test users for development...\n")
    
    # Initialize database connection
    postgres_url = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/app_db")
    postgres = PostgresAdapter(connection_string=postgres_url, min_size=10, max_size=20)
    
    created_users = []
    failed_users = []
    
    for user_data in TEST_USERS:
        email = user_data["email"]
        password = user_data["password"]
        role = user_data["role"]
        description = user_data["description"]
        
        try:
            # Check if user already exists
            query = "SELECT id FROM users WHERE email = $1"
            result = await postgres.fetch_one(query, email)
            
            if result:
                print(f"⚠️  User already exists: {email}")
                # Update role if needed
                update_query = "UPDATE users SET role = $1 WHERE email = $2"
                await postgres.execute_query(update_query, role, email)
                print(f"   ✓ Updated role for {email}")
                created_users.append(user_data)
                continue
            
            # Create new user
            hashed_pw = hash_password(password)
            insert_query = """
                INSERT INTO users (email, password_hash, role, roles, created_at)
                VALUES ($1, $2, $3, $4, NOW())
                RETURNING id
            """
            
            user_id = await postgres.fetch_one(
                insert_query,
                email, hashed_pw, role, [role]
            )
            
            if user_id:
                print(f"✅ Created: {email}")
                print(f"   Role: {role}")
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
            print(f"   Role: {user['role']}")
    
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
    
    postgres_url = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/app_db")
    postgres = PostgresAdapter(connection_string=postgres_url, min_size=10, max_size=20)
    
    deleted_count = 0
    
    for user_data in TEST_USERS:
        email = user_data["email"]
        try:
            delete_query = "DELETE FROM users WHERE email = $1"
            result = await postgres.execute_query(delete_query, email)
            if result:
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
            print(f"   Role: {user['role']}")


if __name__ == "__main__":
    # Set environment for development
    os.environ["PYTHONPATH"] = str(Path(__file__).parent.parent)
    
    # Run the script
    asyncio.run(main())
