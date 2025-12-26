#!/usr/bin/env python3
"""
Create device tracking schema for JWT refresh tokens.
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


async def create_device_schema():
    """Create device tracking tables"""
    print("\n🔧 Creating device tracking schema...")
    
    # Connect to database
    postgres_url = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/app_db")
    postgres = PostgresAdapter(connection_string=postgres_url, min_size=10, max_size=20)
    
    try:
        # Create refresh_tokens table
        print("   Creating refresh_tokens table...")
        create_refresh_tokens = """
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token_id VARCHAR(255) UNIQUE NOT NULL,
                device_id VARCHAR(255) NOT NULL,
                device_name VARCHAR(255),
                device_type VARCHAR(50),
                platform VARCHAR(50),
                browser VARCHAR(50),
                ip_address INET,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT true
            )
        """
        await postgres.execute(create_refresh_tokens)
        
        # Create devices table for tracking user devices
        print("   Creating devices table...")
        create_devices = """
            CREATE TABLE IF NOT EXISTS devices (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                device_id VARCHAR(255) UNIQUE NOT NULL,
                device_name VARCHAR(255),
                device_type VARCHAR(50),
                platform VARCHAR(50),
                browser VARCHAR(50),
                ip_address INET,
                first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT true,
                is_trusted BOOLEAN DEFAULT false
            )
        """
        await postgres.execute(create_devices)
        
        # Create indexes for performance
        print("   Creating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_id ON refresh_tokens(token_id)",
            "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_device_id ON refresh_tokens(device_id)",
            "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens(expires_at)",
            "CREATE INDEX IF NOT EXISTS idx_devices_user_id ON devices(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_devices_device_id ON devices(device_id)"
        ]
        
        for index in indexes:
            await postgres.execute(index)
        
        print("\n✅ Device tracking schema created successfully!")
        
    except Exception as e:
        print(f"\n❌ Error creating schema: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(create_device_schema())
