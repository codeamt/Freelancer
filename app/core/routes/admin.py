from fastapi import APIRouter, Request
from app.core.services.auth import require_role, require_scope
from app.core.ui.layout import Layout
from app.core.ui.pages import AdminDashboardPage
from app.core.services.analytics import AnalyticsService

router_admin = APIRouter(prefix="/admin", tags=["admin"])

@router_admin.get("/dashboard")
@require_role("admin")
async def admin_dashboard(request: Request):
    metrics = AnalyticsService.summarize_metrics()
    return Layout(AdminDashboardPage(metrics), title="Admin Dashboard", page="admin")

@router_admin.get("/summary")
@require_scope("view:content")
async def get_summary():
    return AnalyticsService.summarize_metrics()