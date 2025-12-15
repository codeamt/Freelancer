import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-please-change-000000000000000000000000")
os.environ.setdefault("APP_MEDIA_KEY", "test-media-key-please-change-000000000000000000000000")
