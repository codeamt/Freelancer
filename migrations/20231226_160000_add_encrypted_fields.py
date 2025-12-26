"""
Add Encrypted Fields to Users Table

Adds columns for storing encrypted sensitive user data.
Created: 2023-12-26
Author: System
"""

from core.db.migrations import Migration


class Migration_20231226_160000(Migration):
    version = "20231226_160000"
    description = "Add encrypted fields to users table"
    author = "System"
    dependencies = ["20231226_150000"]
    
    async def up(self, connection):
        """Add encrypted columns to users table"""
        # Add encrypted phone number
        await connection.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS phone TEXT
        """)
        
        # Add encrypted address
        await connection.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS address TEXT
        """)
        
        # Add encrypted SSN
        await connection.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS ssn TEXT
        """)
        
        # Add encrypted credit card
        await connection.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS credit_card TEXT
        """)
        
        # Add encrypted bank account
        await connection.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS bank_account TEXT
        """)
        
        # Add encrypted personal info (JSON)
        await connection.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS personal_info TEXT
        """)
        
        # Add comment to indicate these are encrypted fields
        await connection.execute("""
            COMMENT ON COLUMN users.phone IS 'Encrypted phone number'
        """)
        
        await connection.execute("""
            COMMENT ON COLUMN users.address IS 'Encrypted address'
        """)
        
        await connection.execute("""
            COMMENT ON COLUMN users.ssn IS 'Encrypted social security number'
        """)
        
        await connection.execute("""
            COMMENT ON COLUMN users.credit_card IS 'Encrypted credit card number'
        """)
        
        await connection.execute("""
            COMMENT ON COLUMN users.bank_account IS 'Encrypted bank account number'
        """)
        
        await connection.execute("""
            COMMENT ON COLUMN users.personal_info IS 'Encrypted personal information (JSON)'
        """)
        
        # Create index on encrypted fields for faster searches (if needed)
        # Note: Encrypted fields cannot be indexed for content searches
        # Only index if you need to check for NULL/NOT NULL
        
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_phone_not_null 
            ON users(id) WHERE phone IS NOT NULL
        """)
        
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_address_not_null 
            ON users(id) WHERE address IS NOT NULL
        """)
        
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_ssn_not_null 
            ON users(id) WHERE ssn IS NOT NULL
        """)
    
    async def down(self, connection):
        """Remove encrypted columns from users table"""
        # Drop indexes first
        await connection.execute("DROP INDEX IF EXISTS idx_users_phone_not_null")
        await connection.execute("DROP INDEX IF EXISTS idx_users_address_not_null")
        await connection.execute("DROP INDEX IF EXISTS idx_users_ssn_not_null")
        
        # Remove columns
        await connection.execute("ALTER TABLE users DROP COLUMN IF EXISTS phone")
        await connection.execute("ALTER TABLE users DROP COLUMN IF EXISTS address")
        await connection.execute("ALTER TABLE users DROP COLUMN IF EXISTS ssn")
        await connection.execute("ALTER TABLE users DROP COLUMN IF EXISTS credit_card")
        await connection.execute("ALTER TABLE users DROP COLUMN IF EXISTS bank_account")
        await connection.execute("ALTER TABLE users DROP COLUMN IF EXISTS personal_info")
