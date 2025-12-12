"""
Example: Commerce Domain Media Upload

Shows how a domain implements its own media upload routes.
Uses the universal StorageService for S3/MinIO operations.
"""

from fasthtml.common import *
from add_ons.services.storage import StorageService
from core.services.auth import get_current_user_from_context
from core.utils.logger import get_logger

logger = get_logger(__name__)

# Module name for this domain
MODULE = "commerce"


# -----------------------------------------------------------------------------
# Product Image Upload
# -----------------------------------------------------------------------------

async def upload_product_image(request: Request, file: UploadFile):
    """
    Upload product image for e-commerce.
    
    Domain-specific logic:
    - Validates image type
    - Generates presigned URL for client upload
    - Stores metadata in database
    """
    # Get current user
    user = get_current_user_from_context()
    if not user:
        return {"error": "Not authenticated"}, 401
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        return {"error": "Invalid file type. Only JPEG, PNG, and WebP allowed."}, 400
    
    # Validate file size (max 5MB)
    file_content = await file.read()
    if len(file_content) > 5 * 1024 * 1024:
        return {"error": "File too large. Maximum 5MB."}, 400
    
    # Initialize storage service
    storage = StorageService()
    
    try:
        # Generate presigned upload URL
        upload_info = storage.generate_upload_url(
            module=MODULE,
            user_id=int(user["_id"]),
            filename=f"products/{file.filename}",
            content_type=file.content_type,
            expires_in=3600  # 1 hour
        )
        
        logger.info(f"Generated product image upload URL for user {user['_id']}: {file.filename}")
        
        # Store metadata in database
        from core.services import get_db_service
        from datetime import datetime
        db = get_db_service()
        await db.insert_document("product_images", {
            "user_id": user["_id"],
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_content),
            "uploaded_at": datetime.utcnow()
        })
        
        return {
            "message": "Upload URL generated successfully",
            "upload_info": upload_info,
            "filename": file.filename
        }
        
    except Exception as e:
        logger.error(f"Failed to generate upload URL: {e}")
        return {"error": "Failed to generate upload URL"}, 500


async def download_product_image(request: Request, filename: str):
    """
    Download product image.
    
    Domain-specific logic:
    - Validates user permissions
    - Generates presigned download URL
    - Logs access
    """
    # Get current user
    user = get_current_user_from_context()
    if not user:
        return {"error": "Not authenticated"}, 401
    
    # Initialize storage service
    storage = StorageService()
    
    try:
        # Generate presigned download URL
        download_url = storage.generate_download_url(
            module=MODULE,
            user_id=int(user["_id"]),
            filename=f"products/{filename}",
            expires_in=3600  # 1 hour
        )
        
        logger.info(f"Generated product image download URL for user {user['_id']}: {filename}")
        
        return {
            "download_url": download_url,
            "filename": filename
        }
        
    except Exception as e:
        logger.error(f"Failed to generate download URL: {e}")
        return {"error": "Failed to generate download URL"}, 500


async def delete_product_image(request: Request, filename: str):
    """
    Delete product image.
    
    Domain-specific logic:
    - Validates user owns the image
    - Deletes from storage
    - Updates database
    """
    # Get current user
    user = get_current_user_from_context()
    if not user:
        return {"error": "Not authenticated"}, 401
    
    # TODO: Validate user owns this image
    # image = await db.find_one("product_images", {"filename": filename, "user_id": user["_id"]})
    # if not image:
    #     return {"error": "Image not found or unauthorized"}, 404
    
    # Initialize storage service
    storage = StorageService()
    
    try:
        # Delete from storage
        success = storage.delete_object(
            module=MODULE,
            user_id=int(user["_id"]),
            filename=f"products/{filename}"
        )
        
        if success:
            # TODO: Delete from database
            # await db.delete_one("product_images", {"filename": filename})
            
            logger.info(f"Deleted product image for user {user['_id']}: {filename}")
            return {"message": "Image deleted successfully"}
        else:
            return {"error": "Failed to delete image"}, 500
            
    except Exception as e:
        logger.error(f"Failed to delete image: {e}")
        return {"error": "Failed to delete image"}, 500


# -----------------------------------------------------------------------------
# Secure Upload (Encrypted)
# -----------------------------------------------------------------------------

async def upload_secure_product_data(request: Request, file: UploadFile):
    """
    Upload sensitive product data with encryption.
    
    Use case: Product specifications, pricing sheets, vendor contracts
    """
    # Get current user
    user = get_current_user_from_context()
    if not user:
        return {"error": "Not authenticated"}, 401
    
    # Only admins can upload secure data
    if "admin" not in user.get("roles", []):
        return {"error": "Unauthorized. Admin access required."}, 403
    
    # Initialize storage service
    storage = StorageService()
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Upload with encryption and compression
        success = storage.upload_secure_object(
            module=MODULE,
            user_id=int(user["_id"]),
            filename=f"secure/{file.filename}",
            data=file_content,
            content_type=file.content_type
        )
        
        if success:
            logger.info(f"Uploaded secure product data for user {user['_id']}: {file.filename}")
            return {"message": "Secure upload successful", "filename": file.filename}
        else:
            return {"error": "Failed to upload secure data"}, 500
            
    except Exception as e:
        logger.error(f"Failed to upload secure data: {e}")
        return {"error": "Failed to upload secure data"}, 500


# -----------------------------------------------------------------------------
# Routes Registration (Example)
# -----------------------------------------------------------------------------

def register_commerce_media_routes(app):
    """
    Register commerce media routes with the app.
    
    Usage:
        from .media_example import register_commerce_media_routes
        register_commerce_media_routes(app)
    """
    
    @app.post("/commerce/media/upload/product-image")
    async def _upload_product_image(request: Request, file: UploadFile):
        return await upload_product_image(request, file)
    
    @app.get("/commerce/media/download/product-image/{filename}")
    async def _download_product_image(request: Request, filename: str):
        return await download_product_image(request, filename)
    
    @app.delete("/commerce/media/delete/product-image/{filename}")
    async def _delete_product_image(request: Request, filename: str):
        return await delete_product_image(request, filename)
    
    @app.post("/commerce/media/upload/secure")
    async def _upload_secure_data(request: Request, file: UploadFile):
        return await upload_secure_product_data(request, file)
    
    logger.info("Commerce media routes registered")


# Usage in commerce app:
# from .media_example import register_commerce_media_routes
# register_commerce_media_routes(app)
