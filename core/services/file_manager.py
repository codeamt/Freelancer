"""
FileManager Service - Unified file management with caching and storage

This service provides a high-level interface for file operations across all add-ons/domains,
integrating HybridCache for performance and StorageService for persistence.
"""

import asyncio
import hashlib
import io
import json
import time
import mimetypes
import os
from typing import Optional, Dict, List, Union, BinaryIO, Any, Set
from datetime import datetime, timedelta

from core.utils.cache import cache
from core.integrations.storage import (
    StorageService, 
    StorageLevel, 
    FileMetadata, 
    UploadUrlRequest, 
    DownloadUrlRequest,
    FileUploadRequest,
    FileDownloadRequest,
    FileDeleteRequest,
    FileListRequest,
    AppFileNotFoundError,
    FileUploadError,
    FileDownloadError,
    StorageError
)
from core.utils.logger import get_logger
from core.exceptions import ValidationError

logger = get_logger(__name__)


# File validation configuration
class FileValidationConfig:
    """Configuration for file validation rules"""
    
    # Default allowed extensions (can be overridden per domain)
    DEFAULT_ALLOWED_EXTENSIONS = {
        'image': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'},
        'document': {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'},
        'spreadsheet': {'.xls', '.xlsx', '.csv', '.ods'},
        'presentation': {'.ppt', '.pptx', '.odp'},
        'video': {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'},
        'audio': {'.mp3', '.wav', '.ogg', '.flac', '.aac'},
        'archive': {'.zip', '.rar', '.7z', '.tar', '.gz'}
    }
    
    # Default file size limits (in bytes)
    DEFAULT_SIZE_LIMITS = {
        'image': 10 * 1024 * 1024,      # 10MB
        'document': 50 * 1024 * 1024,   # 50MB
        'spreadsheet': 20 * 1024 * 1024, # 20MB
        'presentation': 100 * 1024 * 1024, # 100MB
        'video': 500 * 1024 * 1024,    # 500MB
        'audio': 50 * 1024 * 1024,     # 50MB
        'archive': 100 * 1024 * 1024,  # 100MB
        'default': 10 * 1024 * 1024     # 10MB
    }
    
    # Dangerous file extensions to block
    BLOCKED_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
        '.app', '.deb', '.pkg', '.dmg', '.rpm', '.msi', '.dll', '.so', '.dylib'
    }
    
    # MIME types that should be blocked
    BLOCKED_MIME_TYPES = {
        'application/x-executable',
        'application/x-msdownload',
        'application/x-msdos-program',
        'application/x-sh',
        'application/x-shellscript'
    }


# Quota management
class FileQuotaManager:
    """Manages file storage quotas per domain and user"""
    
    def __init__(self):
        # Default quotas (in bytes)
        self.default_quotas = {
            'app': {
                'total_storage': 5 * 1024 * 1024 * 1024,  # 5GB per domain
                'file_count': 10000,
                'max_file_size': 100 * 1024 * 1024        # 100MB per file
            },
            'user': {
                'total_storage': 1 * 1024 * 1024 * 1024,  # 1GB per user
                'file_count': 1000,
                'max_file_size': 50 * 1024 * 1024         # 50MB per file
            }
        }
        
        # Domain-specific quotas (can override defaults)
        self.domain_quotas = {}
    
    def get_quota(self, domain: str, level: StorageLevel, user_id: Optional[str] = None) -> Dict[str, int]:
        """Get quota limits for a specific domain/level/user"""
        level_key = 'app' if level == StorageLevel.APP else 'user'
        
        # Start with default quotas
        quota = self.default_quotas[level_key].copy()
        
        # Apply domain-specific overrides if any
        if domain in self.domain_quotas and level_key in self.domain_quotas[domain]:
            quota.update(self.domain_quotas[domain][level_key])
        
        return quota
    
    async def check_quota(self, domain: str, level: StorageLevel, user_id: Optional[str] = None, 
                         file_size: int = 0) -> Dict[str, Any]:
        """Check if upload would exceed quota limits"""
        quota = self.get_quota(domain, level, user_id)
        
        # Get current usage (this would need to be implemented with actual storage stats)
        current_usage = await self._get_current_usage(domain, level, user_id)
        
        # Check file size limit
        if file_size > quota['max_file_size']:
            return {
                'allowed': False,
                'reason': 'file_size_exceeded',
                'message': f'File size {file_size} exceeds maximum allowed size {quota["max_file_size"]}'
            }
        
        # Check storage quota
        if current_usage['total_storage'] + file_size > quota['total_storage']:
            return {
                'allowed': False,
                'reason': 'storage_quota_exceeded',
                'message': f'Storage quota would be exceeded. Current: {current_usage["total_storage"]}, Limit: {quota["total_storage"]}'
            }
        
        # Check file count quota
        if current_usage['file_count'] >= quota['file_count']:
            return {
                'allowed': False,
                'reason': 'file_count_exceeded',
                'message': f'File count quota exceeded. Current: {current_usage["file_count"]}, Limit: {quota["file_count"]}'
            }
        
        return {
            'allowed': True,
            'quota_remaining': quota['total_storage'] - current_usage['total_storage'] - file_size,
            'files_remaining': quota['file_count'] - current_usage['file_count']
        }
    
    async def _get_current_usage(self, domain: str, level: StorageLevel, user_id: Optional[str] = None) -> Dict[str, int]:
        """Get current storage usage statistics"""
        # This is a placeholder - would need to be implemented with actual storage tracking
        # For now, return zero usage
        return {
            'total_storage': 0,
            'file_count': 0
        }
    
    def set_domain_quota(self, domain: str, level: StorageLevel, quota_config: Dict[str, int]) -> None:
        """Set custom quota for a specific domain"""
        level_key = 'app' if level == StorageLevel.APP else 'user'
        
        if domain not in self.domain_quotas:
            self.domain_quotas[domain] = {}
        
        self.domain_quotas[domain][level_key] = quota_config
        logger.info(f"Set custom quota for domain {domain} ({level_key}): {quota_config}")


class FileManager:
    """
    Unified file management service that combines caching and storage.
    
    Provides:
    - File upload/download with automatic caching
    - Presigned URL generation for direct client uploads
    - File metadata management
    - Domain and user-level isolation
    - Automatic cache invalidation on file operations
    """
    
    def __init__(self, storage_service: Optional[StorageService] = None):
        """Initialize FileManager with optional custom storage service"""
        self.storage = storage_service or StorageService()
        self.cache_ttl = 3600  # 1 hour default cache TTL
        self.validation_config = FileValidationConfig()
        self.quota_manager = FileQuotaManager()
        
    def _generate_cache_key(self, domain: str, level: StorageLevel, filename: str, user_id: Optional[str] = None) -> str:
        """Generate cache key for file operations"""
        if level == StorageLevel.APP:
            return f"file:{domain}:app:{filename}"
        else:
            return f"file:{domain}:user:{user_id}:{filename}"
    
    def _generate_metadata_cache_key(self, domain: str, level: StorageLevel, filename: str, user_id: Optional[str] = None) -> str:
        """Generate cache key for file metadata"""
        return f"metadata:{self._generate_cache_key(domain, level, filename, user_id)}"
    
    def _generate_list_cache_key(self, domain: str, level: StorageLevel, user_id: Optional[str] = None, prefix: str = "") -> str:
        """Generate cache key for file listings"""
        if level == StorageLevel.APP:
            return f"list:{domain}:app:{prefix}"
        else:
            return f"list:{domain}:user:{user_id}:{prefix}"
    
    def _validate_file(self, filename: str, file_data: Union[bytes, BinaryIO], content_type: str, 
                      domain: str, allowed_extensions: Optional[Set[str]] = None) -> Dict[str, Any]:
        """Validate file against security rules and limits"""
        # Get file size
        if isinstance(file_data, (bytes, bytearray)):
            file_size = len(file_data)
        else:
            # For file-like objects, get size by seeking to end
            current_pos = file_data.tell() if hasattr(file_data, 'tell') else 0
            file_data.seek(0, 2)  # Seek to end
            file_size = file_data.tell() if hasattr(file_data, 'tell') else 0
            file_data.seek(current_pos)  # Reset position
        
        # Check filename
        if not filename or '..' in filename or filename.startswith('/'):
            return {
                'valid': False,
                'error': 'INVALID_FILENAME',
                'message': 'Invalid filename provided'
            }
        
        # Get file extension
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Check blocked extensions
        if file_ext in self.validation_config.BLOCKED_EXTENSIONS:
            return {
                'valid': False,
                'error': 'BLOCKED_EXTENSION',
                'message': f'File extension {file_ext} is not allowed'
            }
        
        # Check MIME type
        if content_type in self.validation_config.BLOCKED_MIME_TYPES:
            return {
                'valid': False,
                'error': 'BLOCKED_MIME_TYPE',
                'message': f'MIME type {content_type} is not allowed'
            }
        
        # Validate MIME type matches extension
        expected_mime, _ = mimetypes.guess_type(filename)
        if expected_mime and content_type != expected_mime:
            # Allow some flexibility for common types
            if not (expected_mime.startswith('text/') and content_type.startswith('text/') or
                   expected_mime.startswith('image/') and content_type.startswith('image/') or
                   expected_mime.startswith('application/') and content_type.startswith('application/')):
                logger.warning(f"MIME type mismatch: expected {expected_mime}, got {content_type}")
        
        # Check allowed extensions if specified
        if allowed_extensions and file_ext not in allowed_extensions:
            return {
                'valid': False,
                'error': 'EXTENSION_NOT_ALLOWED',
                'message': f'File extension {file_ext} is not in allowed list'
            }
        
        # Determine file category and size limit
        file_category = self._get_file_category(file_ext, content_type)
        size_limit = self.validation_config.DEFAULT_SIZE_LIMITS.get(file_category, 
                                                                   self.validation_config.DEFAULT_SIZE_LIMITS['default'])
        
        # Check file size
        if file_size > size_limit:
            return {
                'valid': False,
                'error': 'FILE_TOO_LARGE',
                'message': f'File size {file_size} exceeds limit {size_limit} for {file_category} files'
            }
        
        return {
            'valid': True,
            'file_size': file_size,
            'file_category': file_category,
            'file_extension': file_ext
        }
    
    def _get_file_category(self, file_ext: str, content_type: str) -> str:
        """Determine file category based on extension and MIME type"""
        # Check by extension first
        for category, extensions in self.validation_config.DEFAULT_ALLOWED_EXTENSIONS.items():
            if file_ext in extensions:
                return category
        
        # Check by MIME type
        if content_type.startswith('image/'):
            return 'image'
        elif content_type.startswith('video/'):
            return 'video'
        elif content_type.startswith('audio/'):
            return 'audio'
        elif content_type.startswith('text/'):
            return 'document'
        elif 'pdf' in content_type:
            return 'document'
        elif 'zip' in content_type or 'archive' in content_type:
            return 'archive'
        
        return 'default'
    
    async def upload_file(
        self,
        domain: str,
        level: StorageLevel,
        filename: str,
        file_data: Union[bytes, BinaryIO, io.IOBase],
        content_type: str = "application/octet-stream",
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        compress: bool = False,
        encrypt: bool = True,
        cache_content: bool = True,
        allowed_extensions: Optional[Set[str]] = None,
        skip_validation: bool = False
    ) -> Dict[str, Any]:
        """
        Upload file with caching support, validation, and quota checking
        
        Args:
            domain: Domain name for isolation
            level: Storage level (APP or USER)
            filename: Name of the file
            file_data: File content as bytes or file-like object
            content_type: MIME type
            user_id: User ID (required for USER level)
            metadata: Additional metadata
            compress: Whether to compress the file
            encrypt: Whether to encrypt the file
            cache_content: Whether to cache file content in memory
            allowed_extensions: Optional set of allowed file extensions
            skip_validation: Skip validation checks (for system uploads)
            
        Returns:
            Dict with upload result and metadata
        """
        try:
            # Validate file unless explicitly skipped
            validation_result = {'valid': True, 'file_size': 0}
            if not skip_validation:
                validation_result = self._validate_file(filename, file_data, content_type, domain, allowed_extensions)
                if not validation_result['valid']:
                    logger.error(f"File validation failed: {validation_result['message']}")
                    return {
                        'success': False,
                        'error': validation_result['error'],
                        'message': validation_result['message']
                    }
            
            # Check quota
            quota_check = await self.quota_manager.check_quota(
                domain=domain,
                level=level,
                user_id=user_id,
                file_size=validation_result.get('file_size', 0)
            )
            
            if not quota_check['allowed']:
                logger.error(f"Quota check failed: {quota_check['message']}")
                return {
                    'success': False,
                    'error': quota_check['reason'],
                    'message': quota_check['message']
                }
            
            # Prepare request with enhanced metadata
            enhanced_metadata = metadata or {}
            if not skip_validation:
                enhanced_metadata.update({
                    'file_category': validation_result.get('file_category', 'unknown'),
                    'file_extension': validation_result.get('file_extension', ''),
                    'validated_at': datetime.utcnow().isoformat(),
                    'quota_remaining': str(quota_check.get('quota_remaining', 0))
                })
            
            request = FileUploadRequest(
                domain=domain,
                level=level,
                filename=filename,
                content_type=content_type,
                user_id=user_id,
                metadata=enhanced_metadata,
                compress=compress,
                encrypt=encrypt
            )
            
            # Upload to storage
            response = self.storage.upload_file(request, file_data)
            
            if response.success:
                # Cache file content if requested
                if cache_content and isinstance(file_data, (bytes, bytearray)):
                    cache_key = self._generate_cache_key(domain, level, filename, user_id)
                    await cache.set(cache_key, file_data, self.cache_ttl)
                    logger.info(f"Cached file content: {cache_key}")
                
                # Invalidate list cache
                list_cache_key = self._generate_list_cache_key(domain, level, user_id)
                await cache.set(list_cache_key, None, 1)  # Invalidate immediately
                
                # Cache metadata
                metadata_response = await self.get_file_metadata(domain, level, filename, user_id)
                
                return {
                    'success': True,
                    'key': response.key,
                    'size': response.size,
                    'message': response.message,
                    'metadata': metadata_response
                }
            else:
                return {
                    'success': False,
                    'message': response.message or 'Upload failed'
                }
                
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            raise FileUploadError(f"Upload failed: {str(e)}")
    
    async def download_file(
        self,
        domain: str,
        level: StorageLevel,
        filename: str,
        user_id: Optional[str] = None,
        use_cache: bool = True
    ) -> bytes:
        """
        Download file with caching support
        
        Args:
            domain: Domain name
            level: Storage level
            filename: Name of the file
            user_id: User ID (required for USER level)
            use_cache: Whether to use cached content
            
        Returns:
            File content as bytes
        """
        try:
            cache_key = self._generate_cache_key(domain, level, filename, user_id)
            
            # Try cache first
            if use_cache:
                cached_data = await cache.get(cache_key)
                if cached_data:
                    logger.info(f"Cache hit for file: {cache_key}")
                    return cached_data
            
            # Download from storage
            request = FileDownloadRequest(
                domain=domain,
                level=level,
                filename=filename,
                user_id=user_id
            )
            
            file_data = self.storage.download_file(request)
            
            # Cache the downloaded content
            if use_cache:
                await cache.set(cache_key, file_data, self.cache_ttl)
                logger.info(f"Cached downloaded file: {cache_key}")
            
            return file_data
            
        except AppFileNotFoundError:
            # Remove from cache if file doesn't exist
            cache_key = self._generate_cache_key(domain, level, filename, user_id)
            await cache.set(cache_key, None, 1)
            raise
        except Exception as e:
            logger.error(f"File download failed: {e}")
            raise FileDownloadError(f"Download failed: {str(e)}")
    
    async def delete_file(
        self,
        domain: str,
        level: StorageLevel,
        filename: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete file and clear cache
        
        Args:
            domain: Domain name
            level: Storage level
            filename: Name of the file
            user_id: User ID (required for USER level)
            
        Returns:
            Dict with deletion result
        """
        try:
            # Delete from storage
            request = FileDeleteRequest(
                domain=domain,
                level=level,
                filename=filename,
                user_id=user_id
            )
            
            response = self.storage.delete_file(request)
            
            # Clear cache entries
            cache_key = self._generate_cache_key(domain, level, filename, user_id)
            metadata_cache_key = self._generate_metadata_cache_key(domain, level, filename, user_id)
            list_cache_key = self._generate_list_cache_key(domain, level, user_id)
            
            await cache.set(cache_key, None, 1)  # Invalidate file cache
            await cache.set(metadata_cache_key, None, 1)  # Invalidate metadata cache
            await cache.set(list_cache_key, None, 1)  # Invalidate list cache
            
            logger.info(f"Deleted file and cleared cache: {filename}")
            
            return {
                'success': response.success,
                'message': response.message
            }
            
        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            return {
                'success': False,
                'message': f"Deletion failed: {str(e)}"
            }
    
    async def get_file_metadata(
        self,
        domain: str,
        level: StorageLevel,
        filename: str,
        user_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get file metadata with caching
        
        Args:
            domain: Domain name
            level: Storage level
            filename: Name of the file
            user_id: User ID (required for USER level)
            use_cache: Whether to use cached metadata
            
        Returns:
            File metadata dict or None if not found
        """
        try:
            cache_key = self._generate_metadata_cache_key(domain, level, filename, user_id)
            
            # Try cache first
            if use_cache:
                cached_metadata = await cache.get(cache_key)
                if cached_metadata:
                    logger.info(f"Metadata cache hit: {cache_key}")
                    return cached_metadata
            
            # Get from storage
            metadata = self.storage.get_file_metadata(domain, level, filename, user_id)
            
            # Convert to dict for caching
            metadata_dict = {
                'key': metadata.key,
                'filename': metadata.filename,
                'size': metadata.size,
                'content_type': metadata.content_type,
                'last_modified': metadata.last_modified.isoformat(),
                'etag': metadata.etag,
                'metadata': metadata.metadata
            }
            
            # Cache metadata
            if use_cache:
                await cache.set(cache_key, metadata_dict, self.cache_ttl)
                logger.info(f"Cached file metadata: {cache_key}")
            
            return metadata_dict
            
        except AppFileNotFoundError:
            # Remove from cache if file doesn't exist
            cache_key = self._generate_metadata_cache_key(domain, level, filename, user_id)
            await cache.set(cache_key, None, 1)
            return None
        except Exception as e:
            logger.error(f"Failed to get file metadata: {e}")
            return None
    
    async def list_files(
        self,
        domain: str,
        level: StorageLevel,
        user_id: Optional[str] = None,
        prefix: str = "",
        max_keys: int = 1000,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        List files with caching
        
        Args:
            domain: Domain name
            level: Storage level
            user_id: User ID (required for USER level)
            prefix: Prefix filter for filenames
            max_keys: Maximum number of results
            use_cache: Whether to use cached listing
            
        Returns:
            Dict with file list and metadata
        """
        try:
            cache_key = self._generate_list_cache_key(domain, level, user_id, prefix)
            
            # Try cache first
            if use_cache:
                cached_list = await cache.get(cache_key)
                if cached_list:
                    logger.info(f"List cache hit: {cache_key}")
                    return cached_list
            
            # Get from storage
            request = FileListRequest(
                domain=domain,
                level=level,
                user_id=user_id,
                prefix=prefix,
                max_keys=max_keys
            )
            
            response = self.storage.list_files(request)
            
            # Convert to dict for caching
            files_list = []
            for file_meta in response.files:
                files_list.append({
                    'key': file_meta.key,
                    'filename': file_meta.filename,
                    'size': file_meta.size,
                    'content_type': file_meta.content_type,
                    'last_modified': file_meta.last_modified.isoformat(),
                    'etag': file_meta.etag,
                    'metadata': file_meta.metadata
                })
            
            result = {
                'files': files_list,
                'total': response.total,
                'truncated': response.truncated
            }
            
            # Cache listing (shorter TTL for lists)
            if use_cache:
                await cache.set(cache_key, result, 300)  # 5 minutes
                logger.info(f"Cached file list: {cache_key}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return {
                'files': [],
                'total': 0,
                'truncated': False,
                'error': str(e)
            }
    
    def generate_upload_url(
        self,
        domain: str,
        level: StorageLevel,
        filename: str,
        content_type: str,
        user_id: Optional[str] = None,
        expires_in: int = 3600
    ) -> Dict[str, Any]:
        """
        Generate presigned upload URL for direct client uploads
        
        Args:
            domain: Domain name
            level: Storage level
            filename: Name of the file
            content_type: MIME type
            user_id: User ID (required for USER level)
            expires_in: URL expiration time in seconds
            
        Returns:
            Dict with upload URL and metadata
        """
        try:
            request = UploadUrlRequest(
                domain=domain,
                level=level,
                filename=filename,
                content_type=content_type,
                user_id=user_id,
                expires_in=expires_in
            )
            
            response = self.storage.generate_upload_url(request)
            
            return {
                'url': response.url,
                'fields': response.fields,
                'key': response.key,
                'expires_in': response.expires_in
            }
            
        except Exception as e:
            logger.error(f"Failed to generate upload URL: {e}")
            raise StorageError(f"Failed to generate upload URL: {str(e)}")
    
    def generate_download_url(
        self,
        domain: str,
        level: StorageLevel,
        filename: str,
        user_id: Optional[str] = None,
        expires_in: int = 3600
    ) -> Dict[str, Any]:
        """
        Generate presigned download URL
        
        Args:
            domain: Domain name
            level: Storage level
            filename: Name of the file
            user_id: User ID (required for USER level)
            expires_in: URL expiration time in seconds
            
        Returns:
            Dict with download URL
        """
        try:
            request = DownloadUrlRequest(
                domain=domain,
                level=level,
                filename=filename,
                user_id=user_id,
                expires_in=expires_in
            )
            
            response = self.storage.generate_download_url(request)
            
            return {
                'url': response.url,
                'expires_in': response.expires_in
            }
            
        except Exception as e:
            logger.error(f"Failed to generate download URL: {e}")
            raise StorageError(f"Failed to generate download URL: {str(e)}")
    
    async def invalidate_cache(
        self,
        domain: str,
        level: StorageLevel,
        filename: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> None:
        """
        Invalidate cache entries for files
        
        Args:
            domain: Domain name
            level: Storage level
            filename: Specific filename to invalidate (None for all)
            user_id: User ID (required for USER level)
        """
        if filename:
            # Invalidate specific file
            cache_key = self._generate_cache_key(domain, level, filename, user_id)
            metadata_cache_key = self._generate_metadata_cache_key(domain, level, filename, user_id)
            
            await cache.set(cache_key, None, 1)
            await cache.set(metadata_cache_key, None, 1)
            
            logger.info(f"Invalidated cache for file: {filename}")
        else:
            # Invalidate all files for domain/level/user
            list_cache_key = self._generate_list_cache_key(domain, level, user_id)
            await cache.set(list_cache_key, None, 1)
            
            logger.info(f"Invalidated list cache for domain: {domain}, level: {level}")
    
    def get_quota_info(self, domain: str, level: StorageLevel, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get quota information for a domain/level/user
        
        Args:
            domain: Domain name
            level: Storage level
            user_id: User ID (required for USER level)
            
        Returns:
            Dict with quota information
        """
        quota = self.quota_manager.get_quota(domain, level, user_id)
        return {
            'domain': domain,
            'level': level.value,
            'user_id': user_id,
            'total_storage_quota': quota['total_storage'],
            'file_count_quota': quota['file_count'],
            'max_file_size': quota['max_file_size'],
            'total_storage_quota_mb': quota['total_storage'] // (1024 * 1024),
            'max_file_size_mb': quota['max_file_size'] // (1024 * 1024)
        }
    
    def set_domain_quota(self, domain: str, level: StorageLevel, quota_config: Dict[str, int]) -> None:
        """
        Set custom quota for a specific domain
        
        Args:
            domain: Domain name
            level: Storage level
            quota_config: Dict with 'total_storage', 'file_count', 'max_file_size'
        """
        self.quota_manager.set_domain_quota(domain, level, quota_config)
    
    def get_allowed_extensions(self, category: Optional[str] = None) -> Set[str]:
        """
        Get allowed file extensions
        
        Args:
            category: Optional file category (image, document, etc.)
            
        Returns:
            Set of allowed extensions
        """
        if category and category in self.validation_config.DEFAULT_ALLOWED_EXTENSIONS:
            return self.validation_config.DEFAULT_ALLOWED_EXTENSIONS[category]
        
        # Return all allowed extensions
        all_extensions = set()
        for extensions in self.validation_config.DEFAULT_ALLOWED_EXTENSIONS.values():
            all_extensions.update(extensions)
        return all_extensions
    
    def set_domain_allowed_extensions(self, domain: str, extensions: Set[str]) -> None:
        """
        Set custom allowed extensions for a domain
        
        Args:
            domain: Domain name
            extensions: Set of allowed extensions
        """
        # This would need to be stored and used in validation
        # For now, just log it
        logger.info(f"Set custom allowed extensions for domain {domain}: {extensions}")
    
    async def get_file_info_hash(
        self,
        domain: str,
        level: StorageLevel,
        filename: str,
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a hash of file metadata for cache invalidation purposes
        
        Args:
            domain: Domain name
            level: Storage level
            filename: Name of the file
            user_id: User ID (required for USER level)
            
        Returns:
            Hash string or None if file not found
        """
        metadata = await self.get_file_metadata(domain, level, filename, user_id)
        if metadata:
            # Create hash from key metadata
            hash_data = f"{metadata['key']}:{metadata['size']}:{metadata['last_modified']}:{metadata['etag']}"
            return hashlib.md5(hash_data.encode()).hexdigest()
        return None


# Global instance for easy access
file_manager = FileManager()


# Convenience functions for add-ons
async def upload_file_with_validation(
    domain: str,
    level: StorageLevel,
    filename: str,
    file_data: Union[bytes, BinaryIO],
    content_type: str = "application/octet-stream",
    user_id: Optional[str] = None,
    allowed_extensions: Optional[Set[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function for file upload with validation and quota checking"""
    return await file_manager.upload_file(
        domain=domain,
        level=level,
        filename=filename,
        file_data=file_data,
        content_type=content_type,
        user_id=user_id,
        allowed_extensions=allowed_extensions,
        **kwargs
    )


async def upload_file_with_cache(
    domain: str,
    level: StorageLevel,
    filename: str,
    file_data: Union[bytes, BinaryIO],
    content_type: str = "application/octet-stream",
    user_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function for file upload with caching (backward compatibility)"""
    return await file_manager.upload_file(
        domain=domain,
        level=level,
        filename=filename,
        file_data=file_data,
        content_type=content_type,
        user_id=user_id,
        **kwargs
    )


async def download_file_with_cache(
    domain: str,
    level: StorageLevel,
    filename: str,
    user_id: Optional[str] = None,
    use_cache: bool = True
) -> bytes:
    """Convenience function for file download with caching"""
    return await file_manager.download_file(
        domain=domain,
        level=level,
        filename=filename,
        user_id=user_id,
        use_cache=use_cache
    )


async def get_cached_file_metadata(
    domain: str,
    level: StorageLevel,
    filename: str,
    user_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Convenience function for getting cached file metadata"""
    return await file_manager.get_file_metadata(
        domain=domain,
        level=level,
        filename=filename,
        user_id=user_id
    )


__all__ = [
    'FileManager',
    'file_manager',
    'upload_file_with_validation',
    'upload_file_with_cache',
    'download_file_with_cache',
    'get_cached_file_metadata',
    'FileValidationConfig',
    'FileQuotaManager'
]
