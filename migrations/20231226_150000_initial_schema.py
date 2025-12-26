"""
Initial Migration

Creates the base database schema for the application.
Created: 2023-12-26
Author: System
"""

from core.db.migrations import Migration


class Migration_20231226_150000(Migration):
    version = "20231226_150000"
    description = "Initial database schema"
    author = "System"
    dependencies = []
    
    async def up(self, connection):
        """Apply the initial schema"""
        # Users table
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'user',
                roles TEXT[] DEFAULT '{}',
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                avatar_url TEXT,
                bio TEXT,
                is_active BOOLEAN DEFAULT true,
                is_verified BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User sessions table
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                session_token VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Devices table
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
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
        """)
        
        # Refresh tokens table
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
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
        """)
        
        # Sites table
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS sites (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                domain VARCHAR(255) UNIQUE NOT NULL,
                description TEXT,
                owner_id INTEGER REFERENCES users(id),
                settings JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)")
        
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)")
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)")
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at)")
        
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_devices_user_id ON devices(user_id)")
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_devices_device_id ON devices(device_id)")
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices(last_seen_at)")
        
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id)")
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_id ON refresh_tokens(token_id)")
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_refresh_tokens_device_id ON refresh_tokens(device_id)")
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens(expires_at)")
        
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_sites_owner_id ON sites(owner_id)")
        await connection.execute("CREATE INDEX IF NOT EXISTS idx_sites_domain ON sites(domain)")
    
    async def down(self, connection):
        """Rollback the initial schema"""
        # Drop tables in reverse order
        await connection.execute("DROP TABLE IF EXISTS refresh_tokens CASCADE")
        await connection.execute("DROP TABLE IF EXISTS devices CASCADE")
        await connection.execute("DROP TABLE IF EXISTS user_sessions CASCADE")
        await connection.execute("DROP TABLE IF EXISTS sites CASCADE")
        await connection.execute("DROP TABLE IF EXISTS users CASCADE")
