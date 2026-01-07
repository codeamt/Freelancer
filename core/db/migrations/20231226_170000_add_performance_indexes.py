"""
Add Performance Indexes

Adds optimized indexes for improved query performance.
Created: 2023-12-26
Author: System
"""

from core.db.migrations import Migration


class Migration_20231226_170000(Migration):
    version = "20231226_170000"
    description = "Add performance indexes"
    author = "System"
    dependencies = ["20231226_150000", "20231226_160000"]
    
    async def up(self, connection):
        """Create performance indexes"""
        # CREATE INDEX CONCURRENTLY cannot run in a transaction
        # So we need to run each index creation separately
        
        # Users table indexes
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_active 
            ON users(email, is_active)
        """)
        
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role_created 
            ON users(role, created_at DESC)
        """)
        
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_verified_created 
            ON users(is_verified, created_at DESC) WHERE is_verified = true
        """)
        
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_name_search 
            ON users(LOWER(first_name), LOWER(last_name))
        """)
        
        # Devices table indexes
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_user_last_seen 
            ON devices(user_id, last_seen_at DESC)
        """)
        
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_active_trusted 
            ON devices(is_active, is_trusted) WHERE is_active = true
        """)
        
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_ip_user 
            ON devices(ip_address, user_id)
        """)
        
        # Refresh tokens table indexes
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_refresh_tokens_user_expires 
            ON refresh_tokens(user_id, expires_at DESC)
        """)
        
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_refresh_tokens_expired_cleanup 
            ON refresh_tokens(expires_at, is_active) 
            WHERE expires_at < NOW() OR is_active = false
        """)
        
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_refresh_tokens_device_active 
            ON refresh_tokens(device_id, is_active) WHERE is_active = true
        """)
        
        # User sessions table indexes
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_user_expires 
            ON user_sessions(user_id, expires_at DESC)
        """)
        
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_expired 
            ON user_sessions(expires_at) WHERE expires_at < NOW()
        """)
        
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_last_accessed 
            ON user_sessions(last_accessed DESC)
        """)
        
        # Sites table indexes
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sites_owner_created 
            ON sites(owner_id, created_at DESC)
        """)
        
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sites_settings_gin 
            ON sites USING GIN(settings)
        """)
        
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sites_domain_active 
            ON sites(domain) WHERE owner_id IS NOT NULL
        """)
        
        # Composite indexes for common queries
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active_verified 
            ON users(is_active, is_verified, created_at DESC)
        """)
        
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_devices_user_active_type 
            ON devices(user_id, is_active, device_type)
        """)
        
        # Partial indexes for better performance
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active_only 
            ON users(id, email) WHERE is_active = true
        """)
        
        await connection.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tokens_active_only 
            ON refresh_tokens(user_id, token_id) WHERE is_active = true AND expires_at > NOW()
        """)
    
    async def down(self, connection):
        """Drop performance indexes"""
        # Users table
        await connection.execute("DROP INDEX IF EXISTS idx_users_email_active")
        await connection.execute("DROP INDEX IF EXISTS idx_users_role_created")
        await connection.execute("DROP INDEX IF EXISTS idx_users_verified_created")
        await connection.execute("DROP INDEX IF EXISTS idx_users_name_search")
        await connection.execute("DROP INDEX IF EXISTS idx_users_active_verified")
        await connection.execute("DROP INDEX IF EXISTS idx_users_active_only")
        
        # Devices table
        await connection.execute("DROP INDEX IF EXISTS idx_devices_user_last_seen")
        await connection.execute("DROP INDEX IF EXISTS idx_devices_active_trusted")
        await connection.execute("DROP INDEX IF EXISTS idx_devices_ip_user")
        await connection.execute("DROP INDEX IF EXISTS idx_devices_user_active_type")
        
        # Refresh tokens table
        await connection.execute("DROP INDEX IF EXISTS idx_refresh_tokens_user_expires")
        await connection.execute("DROP INDEX IF EXISTS idx_refresh_tokens_expired_cleanup")
        await connection.execute("DROP INDEX IF EXISTS idx_refresh_tokens_device_active")
        await connection.execute("DROP INDEX IF EXISTS idx_tokens_active_only")
        
        # User sessions table
        await connection.execute("DROP INDEX IF EXISTS idx_sessions_user_expires")
        await connection.execute("DROP INDEX IF EXISTS idx_sessions_expired")
        await connection.execute("DROP INDEX IF EXISTS idx_sessions_last_accessed")
        
        # Sites table
        await connection.execute("DROP INDEX IF EXISTS idx_sites_owner_created")
        await connection.execute("DROP INDEX IF EXISTS idx_sites_settings_gin")
        await connection.execute("DROP INDEX IF EXISTS idx_sites_domain_active")
