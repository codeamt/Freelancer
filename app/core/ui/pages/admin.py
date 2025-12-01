"""Admin Dashboard Page"""
from fasthtml.common import *
from monsterui.all import *

def AdminDashboardPage(metrics: dict):
    if not metrics:
        metrics = {}
    
    return Container(
        Div(
            H1("Admin Dashboard", cls="mb-4"),
            P("System analytics and metrics overview", cls="text-muted mb-5"),
            
            # Metrics Cards
            Div(
                *[Div(
                    Card(
                        CardBody(
                            H5(key.replace('_', ' ').title(), cls="card-title text-muted"),
                            H2(str(value), cls="mb-0")
                        )
                    ),
                    cls="col-md-4 mb-4"
                ) for key, value in metrics.items()],
                cls="row"
            ) if metrics else Div(
                P("No metrics available yet.", cls="text-muted text-center"),
                cls="alert alert-info"
            ),
            
            # Quick Actions
            Div(
                H2("Quick Actions", cls="mb-3"),
                Div(
                    A("View Detailed Analytics", href="/admin/analytics", cls="btn btn-primary me-2"),
                    A("System Settings", href="/admin/settings", cls="btn btn-secondary"),
                    cls="mb-4"
                ),
                cls="mt-5"
            ),
            
            cls="py-5"
        )
    )
