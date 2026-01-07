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
from typing import Optional, Dict, List, Union, BinaryIO, Any
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

logger = get_logger(__name__)


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
        cache_content: bool = True
    ) -> Dict[str, Any]:
        """
        Upload file with caching support
        
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
            
        Returns:
            Dict with upload result and metadata
        """
        try:
            # Prepare request
            request = FileUploadRequest(
                domain=domain,
                level=level,
                filename=filename,
                content_type=content_type,
                user_id=user_id,
                metadata=metadata or {},
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
async def upload_file_with_cache(
    domain: str,
    level: StorageLevel,
    filename: str,
    file_data: Union[bytes, BinaryIO],
    content_type: str = "application/octet-stream",
    user_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function for file upload with caching"""
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
    'upload_file_with_cache',
    'download_file_with_cache',
    'get_cached_file_metadata'
]
