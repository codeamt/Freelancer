from fasthtml.common import *
from monsterui.all import *
import sys
import os
from pathlib import Path

# Add app directory to path if not already there
app_dir = Path(__file__).parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.routes.main import router_main
from core.utils.logger import get_logger
from examples.eshop import create_eshop_app
from examples.lms import create_lms_app
from examples.social import create_social_app
from examples.streaming import create_streaming_app

logger = get_logger(__name__)

# Initialize FastHTML app with MonsterUI theme
app, rt = fast_app(
    hdrs=[
        *Theme.slate.headers(),
        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css"),
    ],
)

# Mount core routes (landing pages only)
router_main.to_app(app)

# Mount auth add-on
try:
    from add_ons.auth import router_auth
    router_auth.to_app(app)
    logger.info("✓ Auth add-on mounted at /auth")
except Exception as e:
    logger.error(f"Failed to mount auth add-on: {e}")

# Mount e-shop example
try:
    eshop_app = create_eshop_app()
    app.mount("/eshop-example", eshop_app)
    logger.info("✓ E-Shop example mounted at /eshop-example")
except Exception as e:
    logger.error(f"Failed to mount e-shop example: {e}")

# Mount LMS example
try:
    lms_app = create_lms_app()
    app.mount("/lms-example", lms_app)
    logger.info("✓ LMS example mounted at /lms-example")
except Exception as e:
    logger.error(f"Failed to mount LMS example: {e}")

# Mount Social example
try:
    social_app = create_social_app()
    app.mount("/social-example", social_app)
    logger.info("✓ Social example mounted at /social-example")
except Exception as e:
    logger.error(f"Failed to mount Social example: {e}")

# Mount Streaming example
try:
    streaming_app = create_streaming_app()
    app.mount("/streaming-example", streaming_app)
    logger.info("✓ Streaming example mounted at /streaming-example")
except Exception as e:
    logger.error(f"Failed to mount Streaming example: {e}")

logger.info("FastApp started successfully")
logger.info("Available routes:")
logger.info("  - / (Home)")
logger.info("  - /docs (Documentation)")
logger.info("  - /auth/login (Login)")
logger.info("  - /auth/register (Register)")
logger.info("  - /eshop-example (E-Shop Demo)")
logger.info("  - /lms-example (LMS Demo)")
logger.info("  - /social-example (Social Network Demo)")
logger.info("  - /streaming-example (Streaming Platform Demo)")



if __name__ == "__main__":
    #import uvicorn
    #uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
    serve()


