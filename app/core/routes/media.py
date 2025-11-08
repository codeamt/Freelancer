from fastapi import APIRouter, UploadFile, Depends
from app.core.services.storage import StorageService
from app.core.workers.media_tasks import process_media_upload

router_media = APIRouter(prefix="/media", tags=["media"])


def get_storage_service():
    return StorageService()

@router_media.post("/upload/process")
async def process_upload(
    module: str, 
    user_id: int, 
    file: UploadFile, 
    storage: StorageService = Depends(get_storage_service)
):
    # Generate a presigned URL for direct client upload (more efficient)
    try:
        upload_info = storage.generate_upload_url(
            module, user_id, file.filename, file.content_type
        )
        return {
            "message": "Upload URL generated successfully",
            "upload_info": upload_info
        }
    except Exception as e:
        # Fallback to direct upload if presigned URL generation fails
        # Save file content to temp file
        temp_path = f"/tmp/{file.filename}"
        try:
            # Seek to beginning of file if it was already read
            await file.seek(0)
        except:
            pass  # If seek fails, continue with read
        
        file_content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(file_content)
        
        process_media_upload.delay(module, user_id, file.filename, temp_path, file.content_type)
        return {"message": "Upload queued for processing (fallback method)."}

@router_media.post("/upload/direct")
async def direct_upload(
    module: str, 
    user_id: int, 
    file: UploadFile,
    storage: StorageService = Depends(get_storage_service)
):
    # Direct upload through the server (less efficient but more controlled)
    try:
        file_content = await file.read()
        success = storage.upload_secure_object(
            module, user_id, file.filename, file_content, file.content_type
        )
        
        if success:
            return {"message": "File uploaded successfully", "file": file.filename}
        else:
            return {"message": "Failed to upload file", "file": file.filename}
    except Exception as e:
        return {"message": f"Upload failed: {str(e)}", "file": file.filename}

@router_media.get("/download/{module}/{user_id}/{filename}")
async def download_file(
    module: str, 
    user_id: int, 
    filename: str,
    storage: StorageService = Depends(get_storage_service)
):
    # Generate a presigned download URL
    try:
        download_url = storage.generate_download_url(module, user_id, filename)
        return {"download_url": download_url}
    except Exception as e:
        return {"message": f"Failed to generate download URL: {str(e)}"}