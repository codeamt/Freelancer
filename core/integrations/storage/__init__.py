"""
Storage Integration Package

Exports storage service and Pydantic models for type safety.
"""
from core.integrations.storage.s3_client import StorageService

# Import Pydantic models
from core.integrations.storage.models import (
    StorageLevel,
    FileMetadata,
    UploadUrlRequest,
    UploadUrlResponse,
    DownloadUrlRequest,
    DownloadUrlResponse,
    FileUploadRequest,
    FileUploadResponse,
    FileDownloadRequest,
    FileDeleteRequest,
    FileDeleteResponse,
    FileListRequest,
    FileListResponse,
    StoragePath,
)

__all__ = [
    # Service
    'StorageService',
    
    # Models
    'StorageLevel',
    'FileMetadata',
    'UploadUrlRequest',
    'UploadUrlResponse',
    'DownloadUrlRequest',
    'DownloadUrlResponse',
    'FileUploadRequest',
    'FileUploadResponse',
    'FileDownloadRequest',
    'FileDeleteRequest',
    'FileDeleteResponse',
    'FileListRequest',
    'FileListResponse',
    'StoragePath',
]
