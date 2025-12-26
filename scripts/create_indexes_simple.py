#!/usr/bin/env python3
"""
Create Performance Indexes - Simple Version

Creates database performance indexes.
"""

import asyncio
import asyncpg
import os
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv('app.config.env')


async def create_indexes():
    """Create all performance indexes"""
    # Database connection
    db_url = os.getenv("POSTGRES_URL") or f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    
    conn = await asyncpg.connect(db_url)
    
    # Index definitions
    indexes = [
        # Users table
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_active ON users(email, is_active)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role_created ON users(role, created_at DESC)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_verified_created ON users(is_verified, created_at DESC) WHERE is_verified = true",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_name_search ON users(LOWER(first_name), LOWER(last_name))",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active_verified ON users(is_active, is_verified, created_at DESC)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active_only ON users(id, email) WHERE is_active = true",
        
        # Devices table
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_user_last_seen ON devices(user_id, last_seen_at DESC)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_active_trusted ON devices(is_active, is_trusted) WHERE is_active = true",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_ip_user ON devices(ip_address, user_id)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_user_active_type ON devices(user_id, is_active, device_type)",
        
        # Refresh tokens table
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_refresh_tokens_user_expires ON refresh_tokens(user_id, expires_at DESC)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_refresh_tokens_expired_cleanup ON refresh_tokens(expires_at, is_active) WHERE expires_at < NOW() OR is_active = false",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_refresh_tokens_device_active ON refresh_tokens(device_id, is_active) WHERE is_active = true",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tokens_active_only ON refresh_tokens(user_id, token_id) WHERE is_active = true AND expires_at > NOW()",
        
        # User sessions table
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_user_expires ON user_sessions(user_id, expires_at DESC)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_expired ON user_sessions(expires_at) WHERE expires_at < NOW()",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_last_accessed ON user_sessions(last_accessed DESC)",
        
        # Sites table
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sites_owner_created ON sites(owner_id, created_at DESC)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sites_settings_gin ON sites USING GIN(settings)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sites_domain_active ON sites(domain) WHERE owner_id IS NOT NULL",
    ]
    
    print(f"Creating {len(indexes)} performance indexes...")
    
    success_count = 0
    for i, sql in enumerate(indexes, 1):
        try:
            await conn.execute(sql)
            print(f"✓ ({i}/{len(indexes)}) Created index")
            success_count += 1
        except Exception as e:
            print(f"✗ ({i}/{len(indexes)}) Failed: {e}")
    
    # Update statistics
    print("\nUpdating table statistics...")
    tables = ['users', 'devices', 'refresh_tokens', 'user_sessions', 'sites']
    for table in tables:
        try:
            await conn.execute(f"ANALYZE {table}")
            print(f"✓ Analyzed {table}")
        except Exception as e:
            print(f"✗ Failed to analyze {table}: {e}")
    
    await conn.close()
    
    print(f"\n✅ Completed: {success_count}/{len(indexes)} indexes created")


if __name__ == "__main__":
    asyncio.run(create_indexes())
