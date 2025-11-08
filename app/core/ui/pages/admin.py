from fasthtml.common import *
from app.core.ui.components import Container, AnalyticsWidget

def AdminDashboardPage(metrics: dict):
    return Container(
        Div(
            H1("Admin Dashboard", cls="text-3xl font-bold mb-2"),
            P("System analytics and metrics overview", cls="text-gray-600 mb-6"),
            cls="mb-8"
        ),
        Div(
            Div(
                AnalyticsWidget(metrics),
                cls="mb-8"
            ),
            Div(
                H2("Quick Actions", cls="text-2xl font-bold mb-4"),
                Div(
                    A("View Detailed Analytics", href="/admin/analytics", 
                      cls="inline-block bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 mr-4"),
                    A("System Settings", href="/admin/settings", 
                      cls="inline-block bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700"),
                    cls="mb-6"
                ),
                cls="mb-8"
            ),
            cls="max-w-6xl mx-auto"
        ),
        cls="py-8"
    )