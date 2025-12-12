"""MinIO Adapter - Handles object storage"""
from typing import Any, Dict, List, Optional, BinaryIO
from io import BytesIO
import aiobotocore.session
from botocore.exceptions import ClientError
from core.utils.logger import get_logger

logger = get_logger(__name__)


class MinioAdapter:
    """
    MinIO/S3-compatible adapter for object storage.
    
    Use for: File uploads, media storage, backups, static assets, large objects
    """
    
    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        region: str = "us-east-1",
        secure: bool = True
    ):
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.region = region
        self.secure = secure
        self.session = aiobotocore.session.get_session()
        self.client = None
        
    async def connect(self):
        """Initialize S3 client"""
        if not self.client:
            self.client = self.session.create_client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                use_ssl=self.secure
            )
            
            try:
                async with self.client as s3:
                    await s3.head_bucket(Bucket=self.bucket_name)
                logger.info(f"MinIO connected: {self.endpoint_url}/{self.bucket_name}")
            except ClientError:
                async with self.client as s3:
                    await s3.create_bucket(Bucket=self.bucket_name)
                logger.info(f"MinIO bucket created: {self.bucket_name}")
                
    async def disconnect(self):
        """Close S3 client"""
        if self.client:
            async with self.client as s3:
                pass
            self.client = None
            
    async def upload_file(
        self,
        file_path: str,
        object_name: str,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> str:
        """Upload file to bucket"""
        extra_args = {}
        if metadata:
            extra_args['Metadata'] = metadata
        if content_type:
            extra_args['ContentType'] = content_type
            
        async with self.client as s3:
            await s3.upload_file(
                file_path,
                self.bucket_name,
                object_name,
                ExtraArgs=extra_args if extra_args else None
            )
        return object_name
        
    async def upload_fileobj(
        self,
        file_obj: BinaryIO,
        object_name: str,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> str:
        """Upload file object to bucket"""
        extra_args = {}
        if metadata:
            extra_args['Metadata'] = metadata
        if content_type:
            extra_args['ContentType'] = content_type
            
        async with self.client as s3:
            await s3.upload_fileobj(
                file_obj,
                self.bucket_name,
                object_name,
                ExtraArgs=extra_args if extra_args else None
            )
        return object_name
        
    async def upload_bytes(
        self,
        data: bytes,
        object_name: str,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> str:
        """Upload bytes to bucket"""
        file_obj = BytesIO(data)
        return await self.upload_fileobj(file_obj, object_name, metadata, content_type)
        
    async def download_file(self, object_name: str, file_path: str):
        """Download file from bucket"""
        async with self.client as s3:
            await s3.download_file(self.bucket_name, object_name, file_path)
            
    async def download_fileobj(self, object_name: str) -> BytesIO:
        """Download file object from bucket"""
        file_obj = BytesIO()
        async with self.client as s3:
            await s3.download_fileobj(self.bucket_name, object_name, file_obj)
        file_obj.seek(0)
        return file_obj
        
    async def download_bytes(self, object_name: str) -> bytes:
        """Download bytes from bucket"""
        file_obj = await self.download_fileobj(object_name)
        return file_obj.read()
        
    async def get_object(self, object_name: str) -> Dict[str, Any]:
        """Get object metadata and body"""
        async with self.client as s3:
            response = await s3.get_object(Bucket=self.bucket_name, Key=object_name)
            body = await response['Body'].read()
            return {
                'body': body,
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'metadata': response.get('Metadata', {}),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag')
            }
            
    async def delete_object(self, object_name: str):
        """Delete object from bucket"""
        async with self.client as s3:
            await s3.delete_object(Bucket=self.bucket_name, Key=object_name)
            
    async def delete_objects(self, object_names: List[str]):
        """Delete multiple objects from bucket"""
        objects = [{'Key': name} for name in object_names]
        async with self.client as s3:
            await s3.delete_objects(
                Bucket=self.bucket_name,
                Delete={'Objects': objects}
            )
            
    async def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 1000
    ) -> List[Dict[str, Any]]:
        """List objects in bucket"""
        async with self.client as s3:
            response = await s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            if 'Contents' not in response:
                return []
                
            return [
                {
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag']
                }
                for obj in response['Contents']
            ]
            
    async def object_exists(self, object_name: str) -> bool:
        """Check if object exists"""
        try:
            async with self.client as s3:
                await s3.head_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except ClientError:
            return False
            
    async def get_presigned_url(
        self,
        object_name: str,
        expiration: int = 3600,
        method: str = 'get_object'
    ) -> str:
        """Generate presigned URL for object access"""
        async with self.client as s3:
            url = await s3.generate_presigned_url(
                method,
                Params={'Bucket': self.bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
        return url
        
    async def copy_object(
        self,
        source_object: str,
        dest_object: str,
        source_bucket: Optional[str] = None
    ):
        """Copy object within or between buckets"""
        source_bucket = source_bucket or self.bucket_name
        copy_source = {'Bucket': source_bucket, 'Key': source_object}
        
        async with self.client as s3:
            await s3.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=dest_object
            )
            
    async def get_object_metadata(self, object_name: str) -> Dict[str, Any]:
        """Get object metadata without downloading"""
        async with self.client as s3:
            response = await s3.head_object(Bucket=self.bucket_name, Key=object_name)
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'metadata': response.get('Metadata', {}),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag')
            }
            
    async def set_object_metadata(
        self,
        object_name: str,
        metadata: Dict[str, str]
    ):
        """Update object metadata"""
        copy_source = {'Bucket': self.bucket_name, 'Key': object_name}
        
        async with self.client as s3:
            await s3.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=object_name,
                Metadata=metadata,
                MetadataDirective='REPLACE'
            )