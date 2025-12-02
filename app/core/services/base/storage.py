"""Base Storage Service - Abstract Base Class"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, BinaryIO
from datetime import timedelta


class BaseStorageService(ABC):
    """
    Abstract base class for storage services.
    Add-ons can extend this to implement custom file storage logic
    with module-specific paths, validation, and processing.
    """

    @abstractmethod
    def get_module_prefix(self) -> str:
        """
        Get the storage prefix/namespace for this module.
        E.g., 'lms', 'commerce', 'social'
        
        Returns:
            Module prefix string
        """
        pass

    @abstractmethod
    def generate_upload_url(
        self, 
        user_id: int, 
        filename: str, 
        content_type: str,
        expires_in: int = 3600
    ) -> Dict:
        """
        Generate a presigned URL for direct client upload.
        
        Args:
            user_id: User ID for path organization
            filename: Name of file to upload
            content_type: MIME type of file
            expires_in: URL expiration time in seconds
            
        Returns:
            Dict with upload URL and fields
        """
        pass

    @abstractmethod
    def generate_download_url(
        self, 
        user_id: int, 
        filename: str,
        expires_in: int = 3600
    ) -> str:
        """
        Generate a presigned URL for file download.
        
        Args:
            user_id: User ID for path organization
            filename: Name of file to download
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned download URL
        """
        pass

    @abstractmethod
    def upload_file(
        self, 
        user_id: int, 
        filename: str, 
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Upload a file directly from server.
        
        Args:
            user_id: User ID for path organization
            filename: Name of file
            data: File data as bytes
            content_type: MIME type
            metadata: Optional metadata dict
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def download_file(self, user_id: int, filename: str) -> Optional[bytes]:
        """
        Download a file to server memory.
        
        Args:
            user_id: User ID for path organization
            filename: Name of file to download
            
        Returns:
            File data as bytes or None if not found
        """
        pass

    @abstractmethod
    def delete_file(self, user_id: int, filename: str) -> bool:
        """
        Delete a file.
        
        Args:
            user_id: User ID for path organization
            filename: Name of file to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def list_files(
        self, 
        user_id: int, 
        prefix: Optional[str] = None,
        max_keys: int = 1000
    ) -> List[Dict]:
        """
        List files for a user.
        
        Args:
            user_id: User ID for path organization
            prefix: Optional prefix filter
            max_keys: Maximum number of results
            
        Returns:
            List of file metadata dicts
        """
        pass

    @abstractmethod
    def get_file_metadata(self, user_id: int, filename: str) -> Optional[Dict]:
        """
        Get metadata for a file without downloading it.
        
        Args:
            user_id: User ID for path organization
            filename: Name of file
            
        Returns:
            Metadata dict or None if not found
        """
        pass

    # Validation methods (can be overridden)
    def validate_file_type(self, filename: str, allowed_extensions: List[str]) -> bool:
        """
        Validate file extension.
        
        Args:
            filename: Name of file
            allowed_extensions: List of allowed extensions (e.g., ['.jpg', '.png'])
            
        Returns:
            True if valid, False otherwise
        """
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        return f'.{ext}' in [e.lower() for e in allowed_extensions]

    def validate_file_size(self, size_bytes: int, max_size_mb: int) -> bool:
        """
        Validate file size.
        
        Args:
            size_bytes: File size in bytes
            max_size_mb: Maximum allowed size in MB
            
        Returns:
            True if valid, False otherwise
        """
        max_bytes = max_size_mb * 1024 * 1024
        return size_bytes <= max_bytes

    @abstractmethod
    def get_storage_path(self, user_id: int, filename: str) -> str:
        """
        Get the full storage path/key for a file.
        Format: {module}/{user_id}/{filename}
        
        Args:
            user_id: User ID
            filename: File name
            
        Returns:
            Full storage path
        """
        pass
