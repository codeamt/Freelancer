"""
Enhanced User Repository with Encryption Support

Extends the base user repository to handle encrypted fields.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from core.db.repositories.user_repository import UserRepository
from core.services.auth.models_encrypted import (
    EncryptedUserModel, 
    EncryptedUserCreate, 
    EncryptedUserUpdate,
    SENSITIVE_USER_FIELDS
)
from core.services.encryption import get_encryption_service
from core.utils.logger import get_logger

logger = get_logger(__name__)


class EncryptedUserRepository(UserRepository):
    """User repository with encryption support"""
    
    def __init__(self, postgres=None):
        super().__init__(postgres)
        self.encryption_service = get_encryption_service()
    
    async def create_user(self, user_data: EncryptedUserCreate) -> EncryptedUserModel:
        """
        Create a new user with encrypted sensitive fields
        """
        # Encrypt sensitive fields
        encrypted_data = user_data.encrypt_sensitive_fields()
        
        # Build query with encrypted fields
        fields = ['email', 'password_hash', 'role', 'roles']
        values = [user_data.email, user_data.password, user_data.role, user_data.roles]
        
        # Add encrypted fields if provided
        for field in SENSITIVE_USER_FIELDS:
            if field in encrypted_data:
                fields.append(field)
                values.append(encrypted_data[field])
        
        # Add optional fields
        if user_data.first_name:
            fields.append('first_name')
            values.append(user_data.first_name)
        
        if user_data.last_name:
            fields.append('last_name')
            values.append(user_data.last_name)
        
        # Add timestamps
        fields.extend(['created_at', 'updated_at'])
        now = datetime.utcnow().isoformat()
        values.extend([now, now])
        
        # Build and execute query
        placeholders = ', '.join(['$' + str(i + 1) for i in range(len(values))])
        query = f"""
            INSERT INTO users ({', '.join(fields)})
            VALUES ({placeholders})
            RETURNING id, created_at, updated_at
        """
        
        result = await self.postgres.fetch_one(query, *values)
        
        # Create user model
        user = EncryptedUserModel(
            id=result['id'],
            email=user_data.email,
            role=user_data.role,
            roles=user_data.roles,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            created_at=result['created_at'],
            updated_at=result['updated_at']
        )
        
        # Set encrypted fields
        user.set_encrypted_fields(encrypted_data)
        
        logger.info(f"Created encrypted user: {user.email}")
        return user
    
    async def get_user_by_id(self, user_id: int) -> Optional[EncryptedUserModel]:
        """
        Get user by ID with encrypted fields
        """
        query = """
            SELECT id, email, password_hash, role, roles, first_name, last_name,
                   avatar_url, bio, is_active, is_verified, created_at, updated_at,
                   phone, address, ssn, credit_card, bank_account, personal_info
            FROM users
            WHERE id = $1
        """
        
        result = await self.postgres.fetch_one(query, user_id)
        
        if not result:
            return None
        
        # Create user model
        user = EncryptedUserModel(
            id=result['id'],
            email=result['email'],
            role=result['role'],
            roles=result['roles'],
            first_name=result['first_name'],
            last_name=result['last_name'],
            avatar_url=result['avatar_url'],
            bio=result['bio'],
            is_active=result['is_active'],
            is_verified=result['is_verified'],
            created_at=result['created_at'],
            updated_at=result['updated_at']
        )
        
        # Set encrypted fields
        encrypted_data = {
            'phone': result['phone'],
            'address': result['address'],
            'ssn': result['ssn'],
            'credit_card': result['credit_card'],
            'bank_account': result['bank_account'],
            'personal_info': result['personal_info']
        }
        user.set_encrypted_fields(encrypted_data)
        
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[EncryptedUserModel]:
        """
        Get user by email with encrypted fields
        """
        query = """
            SELECT id, email, password_hash, role, roles, first_name, last_name,
                   avatar_url, bio, is_active, is_verified, created_at, updated_at,
                   phone, address, ssn, credit_card, bank_account, personal_info
            FROM users
            WHERE email = $1
        """
        
        result = await self.postgres.fetch_one(query, email)
        
        if not result:
            return None
        
        # Create user model
        user = EncryptedUserModel(
            id=result['id'],
            email=result['email'],
            role=result['role'],
            roles=result['roles'],
            first_name=result['first_name'],
            last_name=result['last_name'],
            avatar_url=result['avatar_url'],
            bio=result['bio'],
            is_active=result['is_active'],
            is_verified=result['is_verified'],
            created_at=result['created_at'],
            updated_at=result['updated_at']
        )
        
        # Set encrypted fields
        encrypted_data = {
            'phone': result['phone'],
            'address': result['address'],
            'ssn': result['ssn'],
            'credit_card': result['credit_card'],
            'bank_account': result['bank_account'],
            'personal_info': result['personal_info']
        }
        user.set_encrypted_fields(encrypted_data)
        
        return user
    
    async def update_user(self, user_id: int, user_data: EncryptedUserUpdate) -> Optional[EncryptedUserModel]:
        """
        Update user with encrypted fields
        """
        # Encrypt sensitive fields
        encrypted_data = user_data.encrypt_sensitive_fields()
        
        # Build update query
        updates = []
        values = []
        param_count = 1
        
        # Add regular fields
        update_fields = ['role', 'roles', 'first_name', 'last_name', 'avatar_url', 
                        'bio', 'is_active', 'is_verified']
        
        for field in update_fields:
            if hasattr(user_data, field) and getattr(user_data, field) is not None:
                updates.append(f"{field} = ${param_count}")
                values.append(getattr(user_data, field))
                param_count += 1
        
        # Add encrypted fields
        for field in SENSITIVE_USER_FIELDS:
            if field in encrypted_data:
                updates.append(f"{field} = ${param_count}")
                values.append(encrypted_data[field])
                param_count += 1
        
        if not updates:
            return await self.get_user_by_id(user_id)
        
        # Add updated_at
        updates.append(f"updated_at = ${param_count}")
        values.append(datetime.utcnow().isoformat())
        param_count += 1
        
        # Add user_id
        values.append(user_id)
        
        # Execute update
        query = f"""
            UPDATE users 
            SET {', '.join(updates)}
            WHERE id = ${param_count}
        """
        
        await self.postgres.execute(query, *values)
        
        # Return updated user
        return await self.get_user_by_id(user_id)
    
    async def update_sensitive_field(self, user_id: int, field: str, value: Any) -> bool:
        """
        Update a single sensitive field
        """
        if field not in SENSITIVE_USER_FIELDS:
            logger.error(f"Field {field} is not in sensitive fields list")
            return False
        
        # Encrypt the value
        encrypted_value = self.encryption_service.encrypt_field(value, field)
        
        # Update the field
        query = f"""
            UPDATE users 
            SET {field} = $1, updated_at = $2
            WHERE id = $3
        """
        
        await self.postgres.execute(query, encrypted_value, datetime.utcnow().isoformat(), user_id)
        
        logger.info(f"Updated encrypted field {field} for user {user_id}")
        return True
    
    async def search_users_encrypted(self, filters: Dict[str, Any]) -> List[EncryptedUserModel]:
        """
        Search users with encrypted fields (note: encrypted fields cannot be searched by content)
        """
        # Build WHERE clause
        conditions = []
        values = []
        param_count = 1
        
        # Only non-encrypted fields can be searched
        searchable_fields = ['email', 'role', 'is_active', 'is_verified', 'first_name', 'last_name']
        
        for field, value in filters.items():
            if field in searchable_fields:
                conditions.append(f"{field} = ${param_count}")
                values.append(value)
                param_count += 1
            elif field in SENSITIVE_USER_FIELDS:
                logger.warning(f"Cannot search encrypted field {field} by content")
        
        # Build query
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT id, email, password_hash, role, roles, first_name, last_name,
                   avatar_url, bio, is_active, is_verified, created_at, updated_at,
                   phone, address, ssn, credit_card, bank_account, personal_info
            FROM users
            WHERE {where_clause}
            ORDER BY created_at DESC
        """
        
        results = await self.postgres.fetch_all(query, *values)
        
        users = []
        for result in results:
            user = EncryptedUserModel(
                id=result['id'],
                email=result['email'],
                role=result['role'],
                roles=result['roles'],
                first_name=result['first_name'],
                last_name=result['last_name'],
                avatar_url=result['avatar_url'],
                bio=result['bio'],
                is_active=result['is_active'],
                is_verified=result['is_verified'],
                created_at=result['created_at'],
                updated_at=result['updated_at']
            )
            
            # Set encrypted fields
            encrypted_data = {
                'phone': result['phone'],
                'address': result['address'],
                'ssn': result['ssn'],
                'credit_card': result['credit_card'],
                'bank_account': result['bank_account'],
                'personal_info': result['personal_info']
            }
            user.set_encrypted_fields(encrypted_data)
            
            users.append(user)
        
        return users
    
    async def rotate_encryption(self, user_id: int) -> bool:
        """
        Rotate encryption for a user's sensitive fields
        """
        # Get user with encrypted fields
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Get all encrypted fields
        encrypted_fields = user.get_encrypted_fields()
        
        # Re-encrypt each field with current key
        updates = []
        values = []
        param_count = 1
        
        for field, encrypted_value in encrypted_fields.items():
            if encrypted_value:
                try:
                    # Decrypt with old key
                    decrypted = self.encryption_service.decrypt(encrypted_value)
                    # Re-encrypt with current key
                    re_encrypted = self.encryption_service.encrypt(decrypted)
                    
                    updates.append(f"{field} = ${param_count}")
                    values.append(re_encrypted)
                    param_count += 1
                except Exception as e:
                    logger.error(f"Failed to rotate encryption for field {field}: {e}")
        
        if updates:
            # Add updated_at
            updates.append(f"updated_at = ${param_count}")
            values.append(datetime.utcnow().isoformat())
            param_count += 1
            
            # Add user_id
            values.append(user_id)
            
            # Update
            query = f"""
                UPDATE users 
                SET {', '.join(updates)}
                WHERE id = ${param_count}
            """
            
            await self.postgres.execute(query, *values)
            logger.info(f"Rotated encryption for user {user_id}")
        
        return True
