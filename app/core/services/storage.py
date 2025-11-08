import os
import boto3
import gzip
import io
import logging
from botocore.client import Config
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from cryptography.fernet import Fernet
from app.core.utils.logger import get_logger

logger = get_logger(__name__)
logger.setLevel(logging.INFO)


class StorageService:
    """Unified storage service supporting AWS S3 and MinIO with optional encryption and compression."""

    def __init__(self):
        self.bucket = os.getenv("APP_BUCKET", "fastapp-dev-assets")
        self.endpoint = os.getenv("S3_URL", "http://localhost:9000")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
        self.encryption_key = os.getenv("APP_MEDIA_KEY", Fernet.generate_key().decode())
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

    # ----------------------------------------------------------------------
    # Internal Helpers
    # ----------------------------------------------------------------------

    def _prefix(self, module: str, user_id: int, filename: Optional[str] = None) -> str:
        base = f"{module}/{user_id}/"
        return base + filename if filename else base

    # ----------------------------------------------------------------------
    # Uploads
    # ----------------------------------------------------------------------

    def generate_upload_url(self, module: str, user_id: int, filename: str, content_type: str, expires_in: int = 3600) -> Dict:
        key = self._prefix(module, user_id, filename)
        logger.info(f"Generating presigned upload URL for {key}")

        return self.s3.generate_presigned_post(
            Bucket=self.bucket,
            Key=key,
            Fields={"Content-Type": content_type},
            Conditions=[{"Content-Type": content_type}],
            ExpiresIn=expires_in,
        )

    # ----------------------------------------------------------------------
    # Encryption + Compression
    # ----------------------------------------------------------------------

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

    def upload_secure_object(self, module: str, user_id: int, filename: str, data: bytes, content_type: str = "application/octet-stream") -> bool:
        key = self._prefix(module, user_id, filename)
        try:
            encrypted_data = self._encrypt_and_compress(data)
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=encrypted_data,
                ContentType=content_type,
                Metadata={"encrypted": "true", "compressed": "true"},
            )
            logger.info(f"Encrypted + compressed upload complete for {key}")
            return True
        except Exception as e:
            logger.error(f"Secure upload failed for {key}: {e}")
            return False

    def download_secure_object(self, module: str, user_id: int, filename: str) -> Optional[bytes]:
        key = self._prefix(module, user_id, filename)
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            raw_data = response["Body"].read()
            decrypted_data = self._decrypt_and_decompress(raw_data)
            logger.info(f"Secure download and decryption successful for {key}")
            return decrypted_data
        except Exception as e:
            logger.error(f"Secure download failed for {key}: {e}")
            return None

    # ----------------------------------------------------------------------
    # Downloads
    # ----------------------------------------------------------------------

    def generate_download_url(self, module: str, user_id: int, filename: str, expires_in: int = 3600) -> str:
        key = self._prefix(module, user_id, filename)
        logger.info(f"Generating presigned download URL for {key}")

        return self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    # ----------------------------------------------------------------------
    # Metadata & Cleanup
    # ----------------------------------------------------------------------

    def delete_object(self, module: str, user_id: int, filename: str) -> bool:
        key = self._prefix(module, user_id, filename)
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted object: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {key}: {e}")
            return False

    def head_object(self, module: str, user_id: int, filename: str) -> Optional[Dict]:
        key = self._prefix(module, user_id, filename)
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
        except Exception as e:
            logger.warning(f"Metadata not found for {key}: {e}")
            return None

    def cleanup_temp_files(self, module: str, user_id: int, older_than_hours: int = 24):
        cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
        prefix = self._prefix(module, user_id, "temp/")

        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            for obj in response.get("Contents", []):
                if obj["LastModified"] < cutoff:
                    self.s3.delete_object(Bucket=self.bucket, Key=obj["Key"])
                    logger.info(f"Deleted stale temp file: {obj['Key']}")
        except Exception as e:
            logger.error(f"Cleanup failed for {module}/{user_id}: {e}")


# Example usage:
# storage = StorageService()
# with open('sample.png', 'rb') as f:
#     storage.upload_secure_object('social', 12, 'sample.png', f.read(), 'image/png')
# data = storage.download_secure_object('social', 12, 'sample.png')
# print(len(data))
