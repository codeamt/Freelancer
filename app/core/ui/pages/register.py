"""Register Page"""
from fasthtml.common import *
from monsterui.all import *

def RegisterPage():
    return Container(
        Div(
            Card(
                CardBody(
                    H1("Create an Account", cls="text-center mb-4"),
                    Form(
                        Div(
                            Label("Email", fr="email", cls="form-label"),
                            Input(type="email", id="email", name="email", placeholder="your@email.com", 
                                  cls="form-control", required=True),
                            cls="mb-3"
                        ),
                        Div(
                            Label("Password", fr="password", cls="form-label"),
                            Input(type="password", id="password", name="password", placeholder="••••••••", 
                                  cls="form-control", required=True),
                            cls="mb-3"
                        ),
                        Button("Register", type="submit", cls="btn btn-success w-100 mb-3"),
                        Div(
                            P(A("Already have an account? Login here", href="/auth/login", cls="text-decoration-none"), 
                              cls="text-center mb-0"),
                        ),
                        hx_post="/auth/register",
                        hx_target="#register-result"
                    ),
                    Div(id="register-result", cls="mt-3")
                ),
                cls="shadow"
            ),
            cls="col-md-6 col-lg-4 mx-auto"
        ),
        cls="min-vh-100 d-flex align-items-center py-5"
    )
