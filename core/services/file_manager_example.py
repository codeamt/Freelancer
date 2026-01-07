"""
FileManager Usage Examples for Add-ons

This file demonstrates how different add-ons/domains can use the FileManager
service for unified file operations with caching and storage.
"""

import asyncio
from typing import Optional

from core.services.file_manager import (
    FileManager,
    file_manager,
    upload_file_with_cache,
    download_file_with_cache,
    get_cached_file_metadata
)
from core.integrations.storage import StorageLevel


class BlogFileManager:
    """Example: Blog domain file management"""
    
    def __init__(self, domain: str = "blog"):
        self.domain = domain
        self.fm = file_manager
    
    async def upload_featured_image(
        self, 
        post_id: str, 
        image_data: bytes, 
        filename: str,
        content_type: str = "image/jpeg"
    ) -> dict:
        """Upload featured image for blog post"""
        return await self.fm.upload_file(
            domain=self.domain,
            level=StorageLevel.APP,  # Shared across all users
            filename=f"posts/{post_id}/{filename}",
            file_data=image_data,
            content_type=content_type,
            metadata={"post_id": post_id, "type": "featured_image"},
            cache_content=True
        )
    
    async def get_featured_image(self, post_id: str, filename: str) -> bytes:
        """Get featured image for blog post"""
        return await self.fm.download_file(
            domain=self.domain,
            level=StorageLevel.APP,
            filename=f"posts/{post_id}/{filename}"
        )


class LMSFileManager:
    """Example: Learning Management System file management"""
    
    def __init__(self, domain: str = "lms"):
        self.domain = domain
        self.fm = file_manager
    
    async def upload_course_material(
        self,
        course_id: str,
        user_id: str,
        file_data: bytes,
        filename: str,
        content_type: str
    ) -> dict:
        """Upload course material (instructor only)"""
        return await self.fm.upload_file(
            domain=self.domain,
            level=StorageLevel.USER,  # Instructor-specific
            filename=f"courses/{course_id}/materials/{filename}",
            file_data=file_data,
            content_type=content_type,
            user_id=user_id,
            metadata={"course_id": course_id, "type": "course_material"},
            encrypt=True,  # Encrypt educational content
            cache_content=False  # Don't cache large files
        )
    
    async def upload_student_assignment(
        self,
        course_id: str,
        student_id: str,
        file_data: bytes,
        filename: str,
        content_type: str
    ) -> dict:
        """Upload student assignment"""
        return await self.fm.upload_file(
            domain=self.domain,
            level=StorageLevel.USER,  # Student-specific
            filename=f"courses/{course_id}/assignments/{student_id}/{filename}",
            file_data=file_data,
            content_type=content_type,
            user_id=student_id,
            metadata={"course_id": course_id, "student_id": student_id, "type": "assignment"},
            encrypt=True,
            cache_content=False
        )
    
    async def get_course_material(
        self, 
        course_id: str, 
        instructor_id: str, 
        filename: str
    ) -> bytes:
        """Get course material (instructor access)"""
        return await self.fm.download_file(
            domain=self.domain,
            level=StorageLevel.USER,
            filename=f"courses/{course_id}/materials/{filename}",
            user_id=instructor_id
        )


class CommerceFileManager:
    """Example: E-commerce file management"""
    
    def __init__(self, domain: str = "commerce"):
        self.domain = domain
        self.fm = file_manager
    
    async def upload_product_image(
        self,
        product_id: str,
        image_data: bytes,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> dict:
        """Upload product image"""
        return await self.fm.upload_file(
            domain=self.domain,
            level=StorageLevel.APP,  # Shared product images
            filename=f"products/{product_id}/images/{filename}",
            file_data=image_data,
            content_type=content_type,
            metadata={"product_id": product_id, "type": "product_image"},
            compress=True,  # Compress images
            cache_content=True
        )
    
    async def get_product_image(self, product_id: str, filename: str) -> bytes:
        """Get product image"""
        return await self.fm.download_file(
            domain=self.domain,
            level=StorageLevel.APP,
            filename=f"products/{product_id}/images/{filename}"
        )
    
    async def upload_customer_document(
        self,
        customer_id: str,
        file_data: bytes,
        filename: str,
        content_type: str
    ) -> dict:
        """Upload customer-specific document (invoice, receipt, etc.)"""
        return await self.fm.upload_file(
            domain=self.domain,
            level=StorageLevel.USER,  # Customer-specific
            filename=f"customers/{customer_id}/documents/{filename}",
            file_data=file_data,
            content_type=content_type,
            user_id=customer_id,
            metadata={"customer_id": customer_id, "type": "customer_document"},
            encrypt=True,  # Encrypt customer documents
            cache_content=False
        )


class SocialFileManager:
    """Example: Social media file management"""
    
    def __init__(self, domain: str = "social"):
        self.domain = domain
        self.fm = file_manager
    
    async def upload_profile_picture(
        self,
        user_id: str,
        image_data: bytes,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> dict:
        """Upload user profile picture"""
        return await self.fm.upload_file(
            domain=self.domain,
            level=StorageLevel.USER,  # User-specific
            filename=f"profiles/{user_id}/{filename}",
            file_data=image_data,
            content_type=content_type,
            user_id=user_id,
            metadata={"user_id": user_id, "type": "profile_picture"},
            compress=True,
            cache_content=True  # Cache profile pictures
        )
    
    async def upload_post_media(
        self,
        user_id: str,
        post_id: str,
        file_data: bytes,
        filename: str,
        content_type: str
    ) -> dict:
        """Upload media for social post"""
        return await self.fm.upload_file(
            domain=self.domain,
            level=StorageLevel.USER,  # User-specific posts
            filename=f"posts/{user_id}/{post_id}/{filename}",
            file_data=file_data,
            content_type=content_type,
            user_id=user_id,
            metadata={"user_id": user_id, "post_id": post_id, "type": "post_media"},
            compress=True if content_type.startswith('image/') else False,
            cache_content=True
        )
    
    async def get_profile_picture(self, user_id: str, filename: str) -> bytes:
        """Get user profile picture"""
        return await self.fm.download_file(
            domain=self.domain,
            level=StorageLevel.USER,
            filename=f"profiles/{user_id}/{filename}",
            user_id=user_id
        )


# Usage examples
async def example_usage():
    """Demonstrate FileManager usage across different domains"""
    
    # Blog example
    blog_fm = BlogFileManager()
    image_data = b"fake_image_data"
    result = await blog_fm.upload_featured_image("post-123", image_data, "featured.jpg")
    print(f"Blog upload result: {result}")
    
    # LMS example
    lms_fm = LMSFileManager()
    pdf_data = b"fake_pdf_data"
    result = await lms_fm.upload_course_material(
        "course-456", "instructor-789", pdf_data, "lesson1.pdf", "application/pdf"
    )
    print(f"LMS upload result: {result}")
    
    # Commerce example
    commerce_fm = CommerceFileManager()
    result = await commerce_fm.upload_product_image(
        "prod-999", image_data, "main.jpg"
    )
    print(f"Commerce upload result: {result}")
    
    # Social example
    social_fm = SocialFileManager()
    result = await social_fm.upload_profile_picture(
        "user-555", image_data, "avatar.jpg"
    )
    print(f"Social upload result: {result}")
    
    # Direct FileManager usage
    direct_result = await upload_file_with_cache(
        domain="custom",
        level=StorageLevel.APP,
        filename="test.txt",
        file_data=b"Hello, World!",
        content_type="text/plain"
    )
    print(f"Direct upload result: {direct_result}")


if __name__ == "__main__":
    asyncio.run(example_usage())
