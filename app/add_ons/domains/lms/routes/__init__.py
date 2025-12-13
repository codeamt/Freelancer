"""LMS Routes Package"""
from fasthtml.common import *
from .courses import router_courses
from .enrollments import router_enrollments
from .checkout import router_lms_checkout

# -----------------------------------------------------------------------------
# Router Configuration
# -----------------------------------------------------------------------------

# Combine all LMS routers
router_lms = FastHTML()

# Include routes from sub-routers
# Note: FastHTML routers combine via route registration
for route in router_courses.routes:
    router_lms.routes.append(route)

for route in router_enrollments.routes:
    router_lms.routes.append(route)

for route in router_lms_checkout.routes:
    router_lms.routes.append(route)

__all__ = ["router_lms"]
