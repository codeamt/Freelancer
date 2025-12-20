"""
Pydantic Models for Storage Service

Type-safe data models for file storage operations.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum


class StorageLevel(str, Enum):
    """Storage isolation levels"""
    APP = "app"    # Shared across all users in domain
    USER = "user"  # Isolated per user in domain


class FileMetadata(BaseModel):
    """File metadata model"""
    key: str
    filename: str
    size: int = Field(..., ge=0)
    content_type: str
    last_modified: datetime
    etag: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class UploadUrlRequest(BaseModel):
    """Request model for generating upload URL"""
    domain: str = Field(..., min_length=1)
    level: StorageLevel
    filename: str = Field(..., min_length=1)
    content_type: str
    user_id: Optional[str] = None
    expires_in: int = Field(default=3600, ge=60, le=86400)  # 1 min to 24 hours
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename doesn't contain path traversal"""
        if '..' in v or v.startswith('/'):
            raise ValueError('Invalid filename')
        return v


class UploadUrlResponse(BaseModel):
    """Response model for upload URL generation"""
    url: str
    fields: Dict[str, str]
    key: str
    expires_in: int


class DownloadUrlRequest(BaseModel):
    """Request model for generating download URL"""
    domain: str = Field(..., min_length=1)
    level: StorageLevel
    filename: str = Field(..., min_length=1)
    user_id: Optional[str] = None
    expires_in: int = Field(default=3600, ge=60, le=86400)


class DownloadUrlResponse(BaseModel):
    """Response model for download URL generation"""
    url: str
    expires_in: int


class FileUploadRequest(BaseModel):
    """Request model for direct file upload"""
    domain: str = Field(..., min_length=1)
    level: StorageLevel
    filename: str = Field(..., min_length=1)
    content_type: str = "application/octet-stream"
    user_id: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)
    compress: bool = False
    encrypt: bool = True


class FileUploadResponse(BaseModel):
    """Response model for file upload"""
    success: bool
    key: str
    size: int
    message: Optional[str] = None


class FileDownloadRequest(BaseModel):
    """Request model for file download"""
    domain: str = Field(..., min_length=1)
    level: StorageLevel
    filename: str = Field(..., min_length=1)
    user_id: Optional[str] = None


class FileDeleteRequest(BaseModel):
    """Request model for file deletion"""
    domain: str = Field(..., min_length=1)
    level: StorageLevel
    filename: str = Field(..., min_length=1)
    user_id: Optional[str] = None


class FileDeleteResponse(BaseModel):
    """Response model for file deletion"""
    success: bool
    message: Optional[str] = None


class FileListRequest(BaseModel):
    """Request model for listing files"""
    domain: str = Field(..., min_length=1)
    level: StorageLevel
    user_id: Optional[str] = None
    prefix: str = ""
    max_keys: int = Field(default=1000, ge=1, le=10000)


class FileListResponse(BaseModel):
    """Response model for file listing"""
    files: List[FileMetadata]
    total: int
    truncated: bool = False


class StoragePath(BaseModel):
    """Storage path model"""
    domain: str
    level: StorageLevel
    user_id: Optional[str] = None
    filename: str
    full_path: str
    
    @classmethod
    def build(cls, domain: str, level: StorageLevel, filename: str, user_id: Optional[str] = None):
        """Build storage path"""
        if level == StorageLevel.APP:
            full_path = f"{domain}/app/{filename}"
        else:  # USER level
            if not user_id:
                raise ValueError("user_id required for USER level storage")
            full_path = f"{domain}/user/{user_id}/{filename}"
        
        return cls(
            domain=domain,
            level=level,
            user_id=user_id,
            filename=filename,
            full_path=full_path
        )
