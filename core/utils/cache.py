# Hybrid Cache: In-Memory + S3
import asyncio
import json
import os
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError
from app.utils.logger import get_logger

logger = get_logger(__name__)

class HybridCache:
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket = os.getenv('S3_CACHE_BUCKET', 'fastapp-cache')

    async def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            return self._cache[key]
        try:
            obj = self.s3.get_object(Bucket=self.bucket, Key=key)
            data = json.loads(obj['Body'].read())
            self._cache[key] = data
            logger.info(f"Cache hit from S3: {key}")
            return data
        except ClientError:
            logger.debug(f"Cache miss for key: {key}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        self._cache[key] = value
        asyncio.create_task(self._expire_key(key, ttl))
        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=json.dumps(value).encode('utf-8'),
                ContentType='application/json'
            )
            logger.info(f"Cached to S3: {key}")
        except ClientError as e:
            logger.error(f"Failed to cache to S3: {e}")

    async def _expire_key(self, key: str, ttl: int):
        await asyncio.sleep(ttl)
        self._cache.pop(key, None)

cache = HybridCache()