"""
User Repository - Extends PostgresRepository

Demonstrates proper use of BaseRepository for a Postgres-primary entity
with MongoDB profile extension and Redis caching.
"""
from typing import Optional, Dict, List, Any
from datetime import datetime
from dataclasses import dataclass
from core.db.repositories.base_repository import PostgresRepository
from core.db.transaction_manager import TransactionManager, transactional
from core.db.adapters.postgres_adapter import PostgresAdapter
from core.db.adapters.mongodb_adapter import MongoDBAdapter
from core.db.adapters.redis_adapter import RedisAdapter
from core.utils.logger import get_logger

# Import security directly to avoid circular import with auth_service
import bcrypt

logger = get_logger(__name__)


@dataclass
class User:
    """User entity."""
    id: int
    email: str
    role: str
    created_at: datetime
    updated_at: datetime
    profile: Optional[Dict] = None


class UserRepository(PostgresRepository[User]):
    """
    User repository - Postgres primary with MongoDB profile extension.
    
    Inherits common patterns from PostgresRepository:
    - Caching (Redis)
    - CRUD operations
    - Transaction support
    - Logging
    """
    
    def __init__(
        self,
        postgres: PostgresAdapter,
        mongodb: Optional[MongoDBAdapter] = None,
        redis: Optional[RedisAdapter] = None
    ):
        super().__init__(postgres, mongodb, redis)
    
    # ========================================================================
    # BaseRepository Implementation (Required)
    # ========================================================================
    
    def get_entity_name(self) -> str:
        """Entity name for logging/caching."""
        return "user"
    
    def get_table_name(self) -> str:
        """Postgres table name."""
        return "users"
    
    def get_primary_key_field(self) -> str:
        """Primary key field."""
        return "id"
    
    def to_dict(self, entity: User) -> Dict[str, Any]:
        """Convert User to dict."""
        data = {
            'id': entity.id,
            'email': entity.email,
            'role': entity.role,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at
        }
        if entity.profile:
            data['profile'] = entity.profile
        return data
    
    def from_dict(self, data: Dict[str, Any]) -> User:
        """Convert dict to User."""
        return User(
            id=data['id'],
            email=data['email'],
            role=data['role'],
            created_at=data['created_at'],
            updated_at=data['updated_at'],
            profile=data.get('profile')
        )
    
    # ========================================================================
    # Custom User Operations
    # ========================================================================
    
    @transactional
    async def create_user(
        self,
        email: str,
        password: str,
        role: str = "user",
        profile_data: Optional[Dict] = None,
        transaction_manager: Optional[TransactionManager] = None
    ) -> int:
        """
        Create user with optional profile.
        
        Uses inherited transaction support from BaseRepository.
        """
        tm = transaction_manager
        
        # Validate required fields
        self._validate_required_fields(
            {'email': email, 'password': password},
            ['email', 'password']
        )
        
        # Hash password
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(password.encode(), salt).decode()
        
        # Prepare data with timestamps
        user_data = self._add_timestamps({
            'email': email,
            'password_hash': password_hash,
            'role': role
        })
        
        # Insert into Postgres
        user_id = await self.execute_in_transaction(
            tm,
            self.postgres,
            'insert',
            self.get_table_name(),
            user_data
        )
        
        # Insert profile into MongoDB if provided
        if self.mongodb and profile_data:
            profile_doc = {
                'user_id': user_id,
                'email': email,
                **profile_data,
                'created_at': datetime.utcnow()
            }
            
            await self.execute_in_transaction(
                tm,
                self.mongodb,
                'insert_one',
                'user_profiles',
                profile_doc
            )
        
        # Invalidate caches
        await self._invalidate_cache(
            self._get_cache_key(user_id),
            self._get_cache_key(email, prefix='email')
        )
        
        self._log_operation('create', user_id, f"email={email}")
        return user_id
    
    async def get_user_by_id(
        self,
        user_id: int,
        include_profile: bool = False
    ) -> Optional[User]:
        """
        Get user by ID.
        
        Uses inherited get_by_id with profile extension.
        """
        # Use base implementation for core data
        user = await self.get_by_id(user_id, use_cache=True)
        
        if not user:
            return None
        
        # Fetch profile if requested
        if include_profile and self.mongodb:
            profile = await self.mongodb.find_one(
                'user_profiles',
                {'user_id': user_id}
            )
            if profile:
                # Remove duplicate fields
                profile.pop('user_id', None)
                profile.pop('email', None)
                profile.pop('_id', None)
                user.profile = profile
        
        return user
    
    async def get_user_by_email(
        self,
        email: str,
        include_password: bool = False
    ) -> Optional[Dict]:
        """
        Get user by email.
        
        Custom method since email is not primary key.
        """
        # Check cache (only if not including password)
        if not include_password:
            cache_key = self._get_cache_key(email, prefix='email')
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached
        
        # Query Postgres
        if include_password:
            query = """
                SELECT id, email, password_hash, role, created_at, updated_at 
                FROM users WHERE email = $1
            """
        else:
            query = """
                SELECT id, email, role, created_at, updated_at 
                FROM users WHERE email = $1
            """
        
        user_data = await self.postgres.fetch_one(query, email)
        
        # Cache result (never cache with password)
        if user_data and not include_password:
            cache_key = self._get_cache_key(email, prefix='email')
            await self._set_cache(cache_key, user_data)
        
        return user_data
    
    async def verify_password(
        self,
        email: str,
        password: str
    ) -> Optional[User]:
        """Verify password and return user."""
        user_data = await self.get_user_by_email(email, include_password=True)
        
        if not user_data:
            return None
        
        try:
            password_valid = bcrypt.checkpw(password.encode(), user_data['password_hash'].encode())
        except Exception:
            password_valid = False
        
        if not password_valid:
            self._log_operation('auth_failed', user_data['id'], f"email={email}")
            return None
        
        # Remove password before converting to entity
        user_data.pop('password_hash', None)
        
        self._log_operation('auth_success', user_data['id'], f"email={email}")
        return self.from_dict(user_data)
    
    @transactional
    async def update_user(
        self,
        user_id: int,
        updates: Dict[str, Any],
        transaction_manager: Optional[TransactionManager] = None
    ) -> bool:
        """
        Update user data.
        
        Uses inherited transaction support.
        """
        tm = transaction_manager
        
        # Separate Postgres and MongoDB updates
        pg_updates = {}
        mongo_updates = {}
        
        pg_fields = {'email', 'role'}
        for key, value in updates.items():
            if key in pg_fields:
                pg_updates[key] = value
            else:
                mongo_updates[key] = value
        
        # Update Postgres if needed
        if pg_updates:
            # Add timestamp
            pg_updates = self._update_timestamp(pg_updates)
            
            affected = await self.execute_in_transaction(
                tm,
                self.postgres,
                'update',
                self.get_table_name(),
                pg_updates,
                {'id': user_id}
            )
            
            if affected == 0:
                logger.warning(f"User {user_id} not found for update")
                return False
        
        # Update MongoDB profile if needed
        if mongo_updates and self.mongodb:
            mongo_updates['updated_at'] = datetime.utcnow()
            
            await self.execute_in_transaction(
                tm,
                self.mongodb,
                'update_one',
                'user_profiles',
                {'user_id': user_id},
                mongo_updates
            )
        
        # Invalidate caches
        user = await self.get_user_by_id(user_id)
        if user:
            await self._invalidate_cache(
                self._get_cache_key(user_id),
                self._get_cache_key(user.email, prefix='email')
            )
        
        self._log_operation('update', user_id)
        return True
    
    @transactional
    async def update_password(
        self,
        user_id: int,
        new_password: str,
        transaction_manager: Optional[TransactionManager] = None
    ) -> bool:
        """Update password (separate for security)."""
        tm = transaction_manager
        
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(new_password.encode(), salt).decode()
        
        affected = await self.execute_in_transaction(
            tm,
            self.postgres,
            'update',
            self.get_table_name(),
            {'password_hash': password_hash, 'updated_at': datetime.utcnow()},
            {'id': user_id}
        )
        
        if affected > 0:
            self._log_operation('password_change', user_id)
            return True
        
        return False
    
    @transactional
    async def delete_user(
        self,
        user_id: int,
        transaction_manager: Optional[TransactionManager] = None
    ) -> bool:
        """
        Delete user from all databases.
        
        Uses inherited transaction support.
        """
        tm = transaction_manager
        
        # Get user for cache invalidation
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Delete from Postgres
        await self.execute_in_transaction(
            tm,
            self.postgres,
            'delete',
            self.get_table_name(),
            {'id': user_id}
        )
        
        # Delete profile from MongoDB
        if self.mongodb:
            await self.execute_in_transaction(
                tm,
                self.mongodb,
                'delete_one',
                'user_profiles',
                {'user_id': user_id}
            )
        
        # Invalidate caches
        await self._invalidate_cache(
            self._get_cache_key(user_id),
            self._get_cache_key(user.email, prefix='email')
        )
        
        self._log_operation('delete', user_id, f"email={user.email}")
        return True
    
    # ========================================================================
    # Query Methods (use inherited list_all and count)
    # ========================================================================
    
    async def list_users(
        self,
        role: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[User]:
        """
        List users with optional role filter.
        
        Uses inherited list_all method.
        """
        filters = {'role': role} if role else None
        return await self.list_all(
            limit=limit,
            offset=offset,
            filters=filters,
            sort_by='created_at',
            sort_desc=True
        )
    
    async def count_users(self, role: Optional[str] = None) -> int:
        """
        Count users.
        
        Uses inherited count method.
        """
        filters = {'role': role} if role else None
        return await self.count(filters)
    
    async def user_exists(self, email: str) -> bool:
        """Check if user exists by email."""
        user = await self.get_user_by_email(email)
        return user is not None
    
    # ========================================================================
    # Session Management (Redis)
    # ========================================================================
    
    async def create_session(
        self,
        user_id: int,
        session_token: str,
        ttl_seconds: int = 86400
    ):
        """Create session in Redis."""
        if not self.redis:
            return
        
        session_key = f"session:{session_token}"
        await self.redis.setex(
            session_key,
            ttl_seconds,
            {'user_id': user_id, 'created_at': datetime.utcnow().isoformat()}
        )
        
        # Track user's sessions
        await self.redis.sadd(f"user_sessions:{user_id}", session_token)
        await self.redis.expire(f"user_sessions:{user_id}", ttl_seconds)
    
    async def get_session(self, session_token: str) -> Optional[Dict]:
        """Get session from Redis."""
        if not self.redis:
            return None
        
        return await self.redis.get(f"session:{session_token}")
    
    async def revoke_session(self, session_token: str):
        """Revoke session."""
        if not self.redis:
            return
        
        session = await self.get_session(session_token)
        if session:
            user_id = session.get('user_id')
            await self.redis.delete(f"session:{session_token}")
            if user_id:
                await self.redis.srem(f"user_sessions:{user_id}", session_token)
    
    async def revoke_all_sessions(self, user_id: int):
        """Revoke all user sessions."""
        if not self.redis:
            return
        
        sessions = await self.redis.smembers(f"user_sessions:{user_id}")
        for token in sessions:
            await self.redis.delete(f"session:{token}")
        await self.redis.delete(f"user_sessions:{user_id}")