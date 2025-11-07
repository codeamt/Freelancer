# File Utilities for Uploads and S3 Storage with Signed URLs
import os
import boto3
from botocore.exceptions import ClientError
from app.utils.logger import get_logger

logger = get_logger(__name__)

class FileUtils:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket = os.getenv('S3_BUCKET', 'fastapp-assets')

    def save_local(self, file_data: bytes, filename: str, directory: str = "uploads") -> str:
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, filename)
        with open(path, "wb") as f:
            f.write(file_data)
        logger.info(f"Saved file locally at {path}")
        return path

    def upload_to_s3(self, file_path: str, key: str) -> str:
        try:
            self.s3.upload_file(file_path, self.bucket, key, ExtraArgs={'ACL': 'public-read'})
            url = f"https://{self.bucket}.s3.amazonaws.com/{key}"
            logger.info(f"Uploaded file to S3: {url}")
            return url
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise

    def delete_from_s3(self, key: str) -> bool:
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted file from S3: {key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete {key} from S3: {e}")
            return False

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expiration
            )
            logger.info(f"Generated presigned GET URL for {key}")
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned GET URL: {e}")
            raise

    def generate_presigned_post(self, key: str, expiration: int = 3600) -> dict:
        try:
            response = self.s3.generate_presigned_post(
                Bucket=self.bucket,
                Key=key,
                ExpiresIn=expiration,
                Fields={"acl": "public-read"},
                Conditions=[["acl", "public-read"]]
            )
            logger.info(f"Generated presigned POST for {key}")
            return response
        except ClientError as e:
            logger.error(f"Failed to generate presigned POST: {e}")
            raise

file_utils = FileUtils()