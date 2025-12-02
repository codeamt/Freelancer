"""Base Authentication Service - Abstract Base Class"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import jwt
import os

JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRATION_HOURS = 12


class BaseAuthService(ABC):
    """
    Abstract base class for authentication services.
    Add-ons can extend this to implement custom authentication logic,
    role definitions, and permission scopes.
    """

    @abstractmethod
    def get_user_roles(self, user_id: str) -> List[str]:
        """
        Get all roles for a user.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            List of role names
        """
        pass

    @abstractmethod
    def get_user_permissions(self, user_id: str) -> List[str]:
        """
        Get all permissions/scopes for a user.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            List of permission/scope names
        """
        pass

    @abstractmethod
    def has_permission(self, user_id: str, permission: str) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            user_id: The user's unique identifier
            permission: The permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        pass

    @abstractmethod
    def has_role(self, user_id: str, role: str) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            user_id: The user's unique identifier
            role: The role to check
            
        Returns:
            True if user has role, False otherwise
        """
        pass

    # Common token methods (can be overridden if needed)
    def create_token(self, data: dict, expires_hours: Optional[int] = None) -> str:
        """
        Create a JWT token with the given data.
        
        Args:
            data: Dictionary of claims to include in token
            expires_hours: Optional custom expiration time in hours
            
        Returns:
            Encoded JWT token string
        """
        expires = expires_hours or TOKEN_EXPIRATION_HOURS
        payload = {
            **data,
            "exp": datetime.utcnow() + timedelta(hours=expires)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: The JWT token to verify
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

    @abstractmethod
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: The username
            password: The password
            
        Returns:
            User data dict if authenticated, None otherwise
        """
        pass

    @abstractmethod
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """
        Get user data by ID.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            User data dict or None if not found
        """
        pass
