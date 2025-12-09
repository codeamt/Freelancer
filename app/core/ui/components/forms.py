from fasthtml.common import *
from monsterui.all import *


def EmailCaptureForm(action: str = "/subscribe", placeholder: str = "Enter your email"):
    """Email capture form with HTMX"""
    return Container(
        Div(
            Form(
                Div(
                    Input(type="email", name="email", placeholder=placeholder, required=True, cls="form-control form-control-lg"),
                    Button("Subscribe", type="submit", cls="btn btn-primary btn-lg"),
                    cls="input-group input-group-lg"
                ),
                hx_post=action,
                hx_target="#subscribe-result"
            ),
            Div(id="subscribe-result", cls="mt-3"),
            cls="py-4"
        )
    )