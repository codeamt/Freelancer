"""
Pydantic Models for Auth Service

Type-safe data models for authentication and authorization.
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    EDITOR = "editor"
    MEMBER = "member"
    USER = "user"
    INSTRUCTOR = "instructor"
    STUDENT = "student"


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class UserBase(BaseModel):
    """Base user model with common fields"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserCreate(UserBase):
    """Model for creating a new user"""
    password: str = Field(..., min_length=8)
    roles: List[UserRole] = Field(default_factory=lambda: [UserRole.USER])
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    """Model for updating user information"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = None
    roles: Optional[List[UserRole]] = None
    status: Optional[UserStatus] = None


class User(UserBase):
    """Complete user model (without password)"""
    id: str = Field(..., alias="_id")
    roles: List[UserRole] = Field(default_factory=list)
    status: UserStatus = UserStatus.ACTIVE
    email_verified: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        populate_by_name = True


class LoginRequest(BaseModel):
    """Login request model"""
    username: str  # Can be username or email
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: User


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # user_id
    exp: int  # expiration timestamp
    iat: int  # issued at timestamp
    roles: List[UserRole] = Field(default_factory=list)
    email: Optional[str] = None


class TokenRefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    """Token refresh response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8)


class PermissionCheck(BaseModel):
    """Permission check request"""
    user_id: str
    resource: str
    action: str
    context: dict = Field(default_factory=dict)


class PermissionCheckResponse(BaseModel):
    """Permission check response"""
    allowed: bool
    reason: Optional[str] = None


class RoleAssignment(BaseModel):
    """Role assignment request"""
    user_id: str
    roles: List[UserRole]


class SessionInfo(BaseModel):
    """User session information"""
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
