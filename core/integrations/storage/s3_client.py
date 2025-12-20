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
from core.services.base.storage import BaseStorageService
from core.utils.logger import get_logger
from core.exceptions import (
    FileNotFoundError as AppFileNotFoundError,
    FileUploadError,
    FileDownloadError,
    StorageError
)
from core.integrations.storage.models import (
    FileUploadRequest,
    FileUploadResponse,
    UploadUrlRequest,
    UploadUrlResponse,
    DownloadUrlRequest,
    DownloadUrlResponse,
    FileMetadata,
    StorageLevel as ModelStorageLevel
)

logger = get_logger(__name__)
logger.setLevel(logging.INFO)


class StorageLevel(Enum):
    """Storage isolation levels"""
    APP = 'app'    # Shared across all users in domain
    USER = 'user'  # Isolated per user in domain


class StorageService(BaseStorageService):
    """Enhanced domain-aware storage service with isolation levels"""

    def __init__(self):
        self.bucket = os.getenv("APP_BUCKET", "fastapp-dev-assets")
        self.endpoint = os.getenv("S3_URL", "http://localhost:9000")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
        
        # Encryption key MUST be set via environment variable
        # Generating it dynamically would make encrypted data unreadable after restart
        self.encryption_key = os.getenv("APP_MEDIA_KEY")
        if not self.encryption_key:
            raise ValueError(
                "APP_MEDIA_KEY environment variable is required for media encryption. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        self.encryptor = Fernet(self.encryption_key.encode())

        self.provider = "aws" if "amazonaws.com" in self.endpoint else "minio"
        self.s3 = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
            config=Config(signature_version="s3v4"),
        )
        logger.info(f"Initialized StorageService ({self.provider}) for bucket: {self.bucket}")

    def _get_path(self, domain: str, level: StorageLevel, user_id: Optional[str] = None, filename: Optional[str] = None) -> str:
        """Generate storage path based on domain and isolation level"""
        if level == StorageLevel.APP:
            base = f"{domain}/app/"
        elif level == StorageLevel.USER:
            if not user_id:
                raise ValueError("user_id required for USER-level storage")
            base = f"{domain}/user/{user_id}/"
        else:
            raise ValueError(f"Invalid storage level: {level}")

        return base + filename if filename else base

    def _encrypt_and_compress(self, data: bytes) -> bytes:
        compressed = io.BytesIO()
        with gzip.GzipFile(fileobj=compressed, mode="wb") as gz:
            gz.write(data)
        encrypted = self.encryptor.encrypt(compressed.getvalue())
        return encrypted

    def _decrypt_and_decompress(self, data: bytes) -> bytes:
        decrypted = self.encryptor.decrypt(data)
        with gzip.GzipFile(fileobj=io.BytesIO(decrypted), mode="rb") as gz:
            return gz.read()

    def upload_domain_file(
        self,
        request: FileUploadRequest,
        data: bytes
    ) -> FileUploadResponse:
        """Upload file with domain and isolation level awareness
        
        Args:
            request: File upload request with domain, level, filename, etc.
            data: File data bytes
            
        Returns:
            FileUploadResponse with upload details
            
        Raises:
            FileUploadError: If upload fails
        """
        key = self._get_path(
            request.domain,
            StorageLevel(request.level.value),
            request.user_id,
            request.filename
        )
        
        # Add domain metadata
        file_metadata = {
            "domain": request.domain,
            "storage_level": request.level.value,
            "user_id": str(request.user_id) if request.user_id else "",
            **request.metadata
        }

        try:
            # Encrypt and compress if requested
            if request.encrypt:
                if request.compress:
                    processed_data = self._encrypt_and_compress(data)
                else:
                    processed_data = self.encryptor.encrypt(data)
            else:
                processed_data = data
                
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=processed_data,
                ContentType=request.content_type,
                Metadata=file_metadata,
            )
            logger.info(f"Uploaded domain file to {key}")
            
            return FileUploadResponse(
                success=True,
                key=key,
                size=len(data),
                message="File uploaded successfully"
            )
        except Exception as e:
            logger.error(f"Failed to upload domain file {key}: {e}")
            raise FileUploadError(request.filename, reason=str(e))

    def download_domain_file(
        self,
        domain: str,
        level: StorageLevel,
        filename: str,
        user_id: Optional[str] = None
    ) -> bytes:
        """Download file with domain and isolation level awareness
        
        Raises:
            FileNotFoundError: If file doesn't exist
            FileDownloadError: If download fails
        """
        key = self._get_path(domain, level, user_id, filename)
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            raw_data = response["Body"].read()
            decrypted_data = self._decrypt_and_decompress(raw_data)
            logger.info(f"Downloaded domain file from {key}")
            return decrypted_data
        except self.s3.exceptions.NoSuchKey:
            logger.error(f"File not found: {key}")
            raise AppFileNotFoundError(filename, path=key)
        except Exception as e:
            logger.error(f"Download failed for {key}: {e}")
            raise FileDownloadError(filename, reason=str(e))

    def generate_upload_url(
        self,
        request: UploadUrlRequest
    ) -> UploadUrlResponse:
        """Generate presigned upload URL with domain and isolation level awareness
        
        Args:
            request: Upload URL request with domain, level, filename, etc.
            
        Returns:
            UploadUrlResponse with presigned URL and fields
        """
        key = self._get_path(
            request.domain,
            StorageLevel(request.level.value),
            request.user_id,
            request.filename
        )
        logger.info(f"Generating presigned upload URL for {key}")

        result = self.s3.generate_presigned_post(
            Bucket=self.bucket,
            Key=key,
            Fields={"Content-Type": request.content_type},
            Conditions=[{"Content-Type": request.content_type}],
            ExpiresIn=request.expires_in,
        )
        
        return UploadUrlResponse(
            url=result['url'],
            fields=result['fields'],
            key=key,
            expires_in=request.expires_in
        )

    def generate_download_url(
        self,
        request: DownloadUrlRequest
    ) -> DownloadUrlResponse:
        """Generate presigned download URL with domain and isolation level awareness
        
        Args:
            request: Download URL request with domain, level, filename, etc.
            
        Returns:
            DownloadUrlResponse with presigned URL
        """
        key = self._get_path(
            request.domain,
            StorageLevel(request.level.value),
            request.user_id,
            request.filename
        )
        logger.info(f"Generating presigned download URL for {key}")

        url = self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=request.expires_in,
        )
        
        return DownloadUrlResponse(
            url=url,
            expires_in=request.expires_in
        )

    def delete_object(
        self,
        domain: str,
        level: StorageLevel,
        filename: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Delete object with domain and isolation level awareness"""
        key = self._get_path(domain, level, user_id, filename)
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted object: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {key}: {e}")
            raise StorageError(f"Failed to delete: {str(e)}")

    def head_object(
        self,
        domain: str,
        level: StorageLevel,
        filename: str,
        user_id: Optional[str] = None
    ) -> Dict:
        """Get object metadata with domain and isolation level awareness
        
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        key = self._get_path(domain, level, user_id, filename)
        try:
            response = self.s3.head_object(Bucket=self.bucket, Key=key)
            logger.info(f"Fetched metadata for {key}")
            return {
                "key": key,
                "size": response.get("ContentLength"),
                "mime_type": response.get("ContentType"),
                "last_modified": response.get("LastModified"),
                "metadata": response.get("Metadata", {}),
            }
        except self.s3.exceptions.NoSuchKey:
            logger.warning(f"Metadata not found for {key}")
            raise AppFileNotFoundError(filename, path=key)
        except Exception as e:
            logger.error(f"Failed to get metadata for {key}: {e}")
            raise StorageError(f"Failed to get metadata: {str(e)}")

    def cleanup_temp_files(
        self,
        domain: str,
        level: StorageLevel,
        user_id: Optional[str] = None,
        older_than_hours: int = 24
    ):
        """Cleanup temporary files with domain and isolation level awareness"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
        prefix = self._get_path(domain, level, user_id, "temp/")

        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            for obj in response.get("Contents", []):
                if obj["LastModified"] < cutoff:
                    self.s3.delete_object(Bucket=self.bucket, Key=obj["Key"])
                    logger.info(f"Deleted stale temp file: {obj['Key']}")
        except Exception as e:
            logger.error(f"Cleanup failed for {domain}/{level.value}: {e}")

    def list_domain_files(
        self,
        domain: str,
        level: StorageLevel,
        user_id: str = None,
        prefix: str = ""
    ) -> list:
        """List files with metadata"""
        path = self._get_path(domain, level, user_id, prefix)
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket,
                Prefix=path,
                FetchOwner=True
            )
            return [
                {
                    'key': obj['Key'].replace(path, ''),
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    **self.s3.head_object(Bucket=self.bucket, Key=obj['Key'])['Metadata']
                }
                for obj in response.get('Contents', [])
            ]
        except Exception as e:
            logger.error(f"List failed for {path}: {e}")
            return []

    def get_with_cache(
        self,
        domain: str,
        level: StorageLevel,
        filename: str,
        user_id: str = None,
        cache_ttl: int = 3600
    ) -> bytes:
        """Get file with local caching"""
        cache_key = hashlib.md5(f"{domain}:{user_id or 'app'}:{filename}".encode()).hexdigest()
        cache_path = f"/tmp/{cache_key}"
        
        if os.path.exists(cache_path):
            if (time.time() - os.path.getmtime(cache_path)) < cache_ttl:
                with open(cache_path, 'rb') as f:
                    return f.read()
        
        data = self.download_domain_file(domain, level, filename, user_id)
        if data:
            with open(cache_path, 'wb') as f:
                f.write(data)
        return data

    def add_cdn_url(self, path: str) -> str:
        """Generate CDN URL if configured"""
        cdn_base = os.getenv("CDN_BASE_URL")
        return f"{cdn_base}/{path}" if cdn_base else None

    # -------------------------------------------------------------------------
    # BaseStorageService Interface Implementation
    # These methods provide a simplified interface for add-ons
    # -------------------------------------------------------------------------
    
    def get_module_prefix(self) -> str:
        """Get the storage prefix/namespace for this module."""
        return "core"  # Default module, can be overridden by add-on implementations
    
    def upload_file(
        self, 
        user_id: int, 
        filename: str, 
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """Upload a file directly from server (BaseStorageService interface)."""
        return self.upload_domain_file(
            domain=self.get_module_prefix(),
            level=StorageLevel.USER,
            filename=filename,
            data=data,
            user_id=str(user_id),
            content_type=content_type,
            metadata=metadata or {}
        )
    
    def download_file(self, user_id: int, filename: str) -> Optional[bytes]:
        """Download a file to server memory (BaseStorageService interface)."""
        return self.download_domain_file(
            domain=self.get_module_prefix(),
            level=StorageLevel.USER,
            filename=filename,
            user_id=str(user_id)
        )
    
    def delete_file(self, user_id: int, filename: str) -> bool:
        """Delete a file (BaseStorageService interface)."""
        return self.delete_object(
            domain=self.get_module_prefix(),
            level=StorageLevel.USER,
            filename=filename,
            user_id=str(user_id)
        )
    
    def list_files(
        self, 
        user_id: int, 
        prefix: Optional[str] = None,
        max_keys: int = 1000
    ) -> List[Dict]:
        """List files for a user (BaseStorageService interface)."""
        return self.list_domain_files(
            domain=self.get_module_prefix(),
            level=StorageLevel.USER,
            user_id=str(user_id),
            prefix=prefix or ""
        )
    
    def get_file_metadata(self, user_id: int, filename: str) -> Optional[Dict]:
        """Get metadata for a file (BaseStorageService interface)."""
        return self.head_object(
            domain=self.get_module_prefix(),
            level=StorageLevel.USER,
            filename=filename,
            user_id=str(user_id)
        )
    
    def get_storage_path(self, user_id: int, filename: str) -> str:
        """Get the full storage path/key for a file (BaseStorageService interface)."""
        return self._get_path(
            domain=self.get_module_prefix(),
            level=StorageLevel.USER,
            user_id=str(user_id),
            filename=filename
        )


# Example usage:
# storage = StorageService()
# with open('sample.png', 'rb') as f:
#     storage.upload_domain_file('social', StorageLevel.USER, 'sample.png', f.read(), '12', 'image/png')
# data = storage.download_domain_file('social', StorageLevel.USER, 'sample.png', '12')
# print(len(data))
