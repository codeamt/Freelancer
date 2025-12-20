"""
Main Application Setup

Initializes all database adapters, repositories, services, and routes.
Provides dependency injection through app.state for child applications.
"""
from fasthtml.common import *
import os

from core.utils.logger import get_logger
from core.bootstrap import create_app
from core.mounting import mount_all

logger = get_logger(__name__)

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")

app, services = create_app(demo=DEMO_MODE)
mount_all(app, services, demo=DEMO_MODE)

logger.info("=" * 60)
logger.info("FastApp started successfully!")
logger.info("=" * 60)
logger.info("")
logger.info("Available routes:")
logger.info("  → / (Home)")
logger.info("  → /docs (Documentation)")
logger.info("  → /blog (Blog)")
if DEMO_MODE:
    logger.info("  → /eshop-example (E-Commerce Demo)")
    logger.info("  → /lms-example (Learning Management System)")
    logger.info("  → /social-example (Social Network)")
    logger.info("  → /streaming-example (Streaming Platform)")
logger.info("")
logger.info("Architecture:")
logger.info("  → Database: PostgreSQL + MongoDB + Redis")
logger.info("  → Pattern: Repository + Service Layer")
logger.info("  → Auth: JWT-based with session support")
logger.info("  → Security: Rate limiting, sanitization, headers")
logger.info("")
logger.info(f"Environment: {getattr(app.state, 'environment', 'unknown')}")
logger.info(f"Demo Mode: {DEMO_MODE}")
logger.info("=" * 60)

# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    serve()