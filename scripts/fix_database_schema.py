#!/usr/bin/env python3
"""
Fix database schema by adding missing columns.
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv('app.config.env')

from core.db.adapters import PostgresAdapter
from core.utils.logger import get_logger

logger = get_logger(__name__)


async def fix_schema():
    """Add missing columns to users table"""
    print("\n🔧 Fixing database schema...")
    
    # Connect to database
    postgres_url = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/app_db")
    postgres = PostgresAdapter(connection_string=postgres_url, min_size=10, max_size=20)
    
    try:
        # Check if updated_at column exists
        check_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'updated_at'
        """
        result = await postgres.fetch_one(check_query)
        
        if not result:
            print("   Adding 'updated_at' column...")
            add_column_query = """
                ALTER TABLE users 
                ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """
            await postgres.execute(add_column_query)
            print("   ✅ Added 'updated_at' column")
        else:
            print("   ✅ 'updated_at' column already exists")
        
        # Check if is_verified column exists
        check_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'is_verified'
        """
        result = await postgres.fetch_one(check_query)
        
        if not result:
            print("   Adding 'is_verified' column...")
            add_column_query = """
                ALTER TABLE users 
                ADD COLUMN is_verified BOOLEAN DEFAULT false
            """
            await postgres.execute(add_column_query)
            
            # Update existing users to be verified
            update_query = """
                UPDATE users SET is_verified = true WHERE email LIKE '%@test.com'
            """
            await postgres.execute(update_query)
            print("   ✅ Added 'is_verified' column and marked test users as verified")
        else:
            print("   ✅ 'is_verified' column already exists")
        
        print("\n✅ Database schema fixed!")
        
    except Exception as e:
        print(f"\n❌ Error fixing schema: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(fix_schema())
