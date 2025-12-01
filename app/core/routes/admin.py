from fasthtml.common import *
from core.services.auth import require_role, require_scope
from core.ui.layout import Layout
from core.ui.pages import AdminDashboardPage
from core.services.analytics import AnalyticsService

router_admin = APIRouter()

@router_admin.get("/admin/dashboard")
@require_role("admin")
async def admin_dashboard(request: Request):
    metrics = AnalyticsService.summarize_metrics()
    return Layout(AdminDashboardPage(metrics), title="Admin Dashboard", page="admin")

@router_admin.get("/admin/summary")
@require_scope("view:content")
async def get_summary():
    return AnalyticsService.summarize_metrics()