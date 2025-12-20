"""
Database Schema Initialization Script

Creates core tables if they don't exist.
Run this once to initialize the database.
"""
import asyncio
import os
from core.db.adapters import PostgresAdapter
from core.utils.logger import get_logger

logger = get_logger(__name__)

# SQL for creating core tables
CORE_SCHEMA_SQL = """
-- Users table (core authentication)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User profiles table (extended user data)
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    bio TEXT,
    avatar_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Sessions table (for session management)
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(255) PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    data JSONB,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
"""

# SQL for LMS addon tables
LMS_SCHEMA_SQL = """
-- Enrollments table (LMS addon)
CREATE TABLE IF NOT EXISTS enrollments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    progress INTEGER DEFAULT 0,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    UNIQUE(user_id, course_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_enrollments_user_id ON enrollments(user_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_course_id ON enrollments(course_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_status ON enrollments(status);
"""

# SQL for Commerce addon tables
COMMERCE_SCHEMA_SQL = """
-- Orders table (Commerce addon)
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',
    total DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
"""


async def init_database():
    """Initialize database with core schema."""
    logger.info("Initializing database schema...")
    
    # Get database connection string from environment
    postgres_url = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/app_db")
    
    # Create adapter
    postgres = PostgresAdapter(
        connection_string=postgres_url,
        min_size=1,
        max_size=2
    )
    
    try:
        # Connect to database
        await postgres.connect()
        logger.info("✓ Connected to PostgreSQL")
        
        # Execute core schema
        logger.info("Creating core tables...")
        await postgres.execute(CORE_SCHEMA_SQL)
        logger.info("✓ Core tables created")
        
        # Execute LMS schema
        logger.info("Creating LMS tables...")
        await postgres.execute(LMS_SCHEMA_SQL)
        logger.info("✓ LMS tables created")
        
        # Execute Commerce schema
        logger.info("Creating Commerce tables...")
        await postgres.execute(COMMERCE_SCHEMA_SQL)
        logger.info("✓ Commerce tables created")
        
        logger.info("=" * 60)
        logger.info("Database initialization complete!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    finally:
        await postgres.disconnect()


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv("../../../app.config.env")
    
    # Run initialization
    asyncio.run(init_database())
