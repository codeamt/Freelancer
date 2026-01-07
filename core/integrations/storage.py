"""
Storage Integration

Flattened module containing S3 client and models for file storage operations.
"""

import os
import boto3
import gzip
import io
import logging
import time
import hashlib
from enum import Enum
from botocore.client import Config
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Union, List
from cryptography.fernet import Fernet
from pydantic import BaseModel, Field, validator

from core.services.base.storage import BaseStorageService
from core.utils.logger import get_logger
from core.exceptions import (
    FileNotFoundError as AppFileNotFoundError,
    FileUploadError,
    FileDownloadError,
    StorageError
)

logger = get_logger(__name__)
logger.setLevel(logging.INFO)


# ===== MODELS =====

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


# ===== S3 CLIENT =====

class StorageService(BaseStorageService):
    """Enhanced domain-aware storage service with isolation levels"""

    def __init__(self):
        self.bucket = os.getenv("APP_BUCKET", "fastapp-dev-assets")
        self.endpoint = os.getenv("S3_URL", "http://localhost:9000")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
        self.encryption_key = os.getenv("STORAGE_ENCRYPTION_KEY", Fernet.generate_key().decode())
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
            config=Config(
                signature_version='s3v4',
                connect_timeout=30,
                read_timeout=60,
                retries={'max_attempts': 3}
            )
        )
        
        self.fernet = Fernet(self.encryption_key.encode())
        logger.info(f"StorageService initialized for bucket: {self.bucket}")
    
    def get_module_prefix(self) -> str:
        """Get the storage prefix for this module"""
        return "storage"
    
    def get_storage_path(self) -> str:
        """Get the storage path for this module"""
        return f"{self.get_module_prefix()}/"

    def _build_storage_path(self, domain: str, level: StorageLevel, filename: str, user_id: Optional[str] = None) -> str:
        """Build storage path based on isolation level"""
        if level == StorageLevel.APP:
            return f"{domain}/app/{filename}"
        else:  # USER level
            if not user_id:
                raise ValueError("user_id required for USER level storage")
            return f"{domain}/user/{user_id}/{filename}"

    def _compress_data(self, data: bytes) -> bytes:
        """Compress data using gzip"""
        return gzip.compress(data)

    def _decompress_data(self, compressed_data: bytes) -> bytes:
        """Decompress gzip data"""
        return gzip.decompress(compressed_data)

    def _encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data"""
        return self.fernet.encrypt(data)

    def _decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt data"""
        return self.fernet.decrypt(encrypted_data)

    def generate_upload_url(self, request: UploadUrlRequest) -> UploadUrlResponse:
        """Generate presigned upload URL"""
        try:
            key = self._build_storage_path(request.domain, request.level, request.filename, request.user_id)
            
            # Generate presigned URL for upload
            url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': key,
                    'ContentType': request.content_type
                },
                ExpiresIn=request.expires_in
            )
            
            logger.info(f"Generated upload URL for key: {key}")
            
            return UploadUrlResponse(
                url=url,
                fields={},  # Not used with put_object
                key=key,
                expires_in=request.expires_in
            )
        except Exception as e:
            logger.error(f"Failed to generate upload URL: {e}")
            raise StorageError(f"Failed to generate upload URL: {str(e)}")

    def generate_download_url(self, request: DownloadUrlRequest) -> DownloadUrlResponse:
        """Generate presigned download URL"""
        try:
            key = self._build_storage_path(request.domain, request.level, request.filename, request.user_id)
            
            # Check if file exists
            try:
                self.s3_client.head_object(Bucket=self.bucket, Key=key)
            except self.s3_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] == '404':
                    raise AppFileNotFoundError(f"File not found: {key}")
                raise
            
            # Generate presigned URL for download
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': key
                },
                ExpiresIn=request.expires_in
            )
            
            logger.info(f"Generated download URL for key: {key}")
            
            return DownloadUrlResponse(
                url=url,
                expires_in=request.expires_in
            )
        except AppFileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate download URL: {e}")
            raise StorageError(f"Failed to generate download URL: {str(e)}")

    def upload_file(self, request: FileUploadRequest, file_data: Union[bytes, io.IOBase]) -> FileUploadResponse:
        """Upload file directly to storage"""
        try:
            key = self._build_storage_path(request.domain, request.level, request.filename, request.user_id)
            
            # Process file data
            if isinstance(file_data, io.IOBase):
                file_data = file_data.read()
            
            original_size = len(file_data)
            
            # Compress if requested
            if request.compress:
                file_data = self._compress_data(file_data)
                logger.info(f"Compressed file from {original_size} to {len(file_data)} bytes")
            
            # Encrypt if requested
            if request.encrypt:
                file_data = self._encrypt_data(file_data)
                logger.info("Encrypted file data")
            
            # Upload to S3
            extra_args = {
                'ContentType': request.content_type,
                'Metadata': {
                    **request.metadata,
                    'original_size': str(original_size),
                    'compressed': str(request.compress),
                    'encrypted': str(request.encrypt)
                }
            }
            
            if request.encrypt:
                extra_args['Metadata']['encryption_version'] = '1.0'
            
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_data,
                **extra_args
            )
            
            logger.info(f"Uploaded file: {key} ({len(file_data)} bytes)")
            
            return FileUploadResponse(
                success=True,
                key=key,
                size=len(file_data),
                message="File uploaded successfully"
            )
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise FileUploadError(f"Failed to upload file: {str(e)}")

    def download_file(self, request: FileDownloadRequest) -> bytes:
        """Download file from storage"""
        try:
            key = self._build_storage_path(request.domain, request.level, request.filename, request.user_id)
            
            # Download from S3
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            file_data = response['Body'].read()
            
            metadata = response.get('Metadata', {})
            
            # Decrypt if needed
            if metadata.get('encrypted') == 'True':
                try:
                    file_data = self._decrypt_data(file_data)
                    logger.info("Decrypted file data")
                except Exception as e:
                    logger.error(f"Failed to decrypt file: {e}")
                    raise FileDownloadError(f"Failed to decrypt file: {str(e)}")
            
            # Decompress if needed
            if metadata.get('compressed') == 'True':
                try:
                    file_data = self._decompress_data(file_data)
                    logger.info("Decompressed file data")
                except Exception as e:
                    logger.error(f"Failed to decompress file: {e}")
                    raise FileDownloadError(f"Failed to decompress file: {str(e)}")
            
            logger.info(f"Downloaded file: {key} ({len(file_data)} bytes)")
            return file_data
            
        except self.s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise AppFileNotFoundError(f"File not found: {key}")
            raise FileDownloadError(f"Failed to download file: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            raise FileDownloadError(f"Failed to download file: {str(e)}")

    def delete_file(self, request: FileDeleteRequest) -> FileDeleteResponse:
        """Delete file from storage"""
        try:
            key = self._build_storage_path(request.domain, request.level, request.filename, request.user_id)
            
            # Delete from S3
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            
            logger.info(f"Deleted file: {key}")
            
            return FileDeleteResponse(
                success=True,
                message="File deleted successfully"
            )
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return FileDeleteResponse(
                success=False,
                message=f"Failed to delete file: {str(e)}"
            )

    def list_files(self, request: FileListRequest) -> FileListResponse:
        """List files in storage"""
        try:
            prefix = self._build_storage_path(request.domain, request.level, "", request.user_id)
            if request.prefix:
                prefix += request.prefix
            
            # List objects from S3
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
                MaxKeys=request.max_keys
            )
            
            files = []
            for obj in response.get('Contents', []):
                # Extract filename from full key
                filename = obj['Key'].replace(prefix, '')
                if filename:
                    metadata = FileMetadata(
                        key=obj['Key'],
                        filename=filename,
                        size=obj['Size'],
                        content_type=obj.get('ContentType', 'application/octet-stream'),
                        last_modified=obj['LastModified'],
                        etag=obj.get('ETag', '').strip('"')
                    )
                    files.append(metadata)
            
            return FileListResponse(
                files=files,
                total=len(files),
                truncated=response.get('IsTruncated', False)
            )
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            raise StorageError(f"Failed to list files: {str(e)}")

    def get_file_metadata(self, domain: str, level: StorageLevel, filename: str, user_id: Optional[str] = None) -> FileMetadata:
        """Get file metadata"""
        try:
            key = self._build_storage_path(domain, level, filename, user_id)
            
            # Get object metadata from S3
            response = self.s3_client.head_object(Bucket=self.bucket, Key=key)
            
            return FileMetadata(
                key=key,
                filename=filename,
                size=response['ContentLength'],
                content_type=response.get('ContentType', 'application/octet-stream'),
                last_modified=response['LastModified'],
                etag=response.get('ETag', '').strip('"'),
                metadata=response.get('Metadata', {})
            )
        except self.s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise AppFileNotFoundError(f"File not found: {key}")
            raise StorageError(f"Failed to get file metadata: {str(e)}")


# Convenience functions
def create_storage_service() -> StorageService:
    """Create and return a storage service instance"""
    return StorageService()


__all__ = [
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
    
    # Client
    'StorageService',
    'create_storage_service',
]
