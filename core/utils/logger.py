import logging
import sys
import os
from typing import Optional

def get_logger(
    name: str, 
    level: int = logging.INFO,
    enable_cloudwatch: bool = False
) -> logging.Logger:
    """
    Configurable logger factory with optional CloudWatch integration.
    
    Args:
        name: Logger name
        level: Logging level (default: INFO)
        enable_cloudwatch: Enable CloudWatch Logs integration if AWS credentials available
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
        
        # Optional CloudWatch Logs integration
        if enable_cloudwatch and os.getenv("AWS_REGION") and os.getenv("AWS_ACCESS_KEY_ID"):
            try:
                import boto3
                import watchtower
                
                session = boto3.Session(region_name=os.getenv("AWS_REGION", "us-east-1"))
                cw_handler = watchtower.CloudWatchLogHandler(
                    log_group=os.getenv("CLOUDWATCH_LOG_GROUP", "FastApp/Logs"),
                    stream_name=os.getenv("CLOUDWATCH_LOG_STREAM", name),
                    boto3_session=session,
                )
                cw_formatter = logging.Formatter(
                    "%(asctime)s [%(levelname)s] %(message)s"
                )
                cw_handler.setFormatter(cw_formatter)
                logger.addHandler(cw_handler)
                logger.info("✅ CloudWatch Logs initialized.")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize CloudWatch Logs: {e}")
    
    return logger