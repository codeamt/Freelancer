"""Contact Page"""
from fasthtml.common import *
from monsterui.all import *

def ContactPage():
    return Container(
        Div(
            H1("Contact Us", cls="display-4 mb-4"),
            P("We'd love to hear from you! Reach out with any questions or feedback.", cls="lead mb-5"),
            
            Div(
                # Contact Form
                Div(
                    H2("Send us a message", cls="mb-4"),
                    Form(
                        Div(
                            Label("Name", fr="name", cls="form-label"),
                            Input(type="text", id="name", name="name", cls="form-control", required=True),
                            cls="mb-3"
                        ),
                        Div(
                            Label("Email", fr="email", cls="form-label"),
                            Input(type="email", id="email", name="email", cls="form-control", required=True),
                            cls="mb-3"
                        ),
                        Div(
                            Label("Subject", fr="subject", cls="form-label"),
                            Input(type="text", id="subject", name="subject", cls="form-control", required=True),
                            cls="mb-3"
                        ),
                        Div(
                            Label("Message", fr="message", cls="form-label"),
                            Textarea(id="message", name="message", rows="5", cls="form-control", required=True),
                            cls="mb-3"
                        ),
                        Button("Send Message", type="submit", cls="btn btn-primary btn-lg"),
                        hx_post="/contact",
                        hx_target="#form-response"
                    ),
                    Div(id="form-response", cls="mt-3"),
                    cls="col-md-6"
                ),
                
                # Contact Information
                Div(
                    H2("Contact Information", cls="mb-4"),
                    Div(
                        H5("Email", cls="mb-2"),
                        P("support@fastapp.example.com", cls="text-muted"),
                        cls="mb-4"
                    ),
                    Div(
                        H5("Address", cls="mb-2"),
                        P("123 Developer Street", cls="mb-1"),
                        P("San Francisco, CA 94103", cls="text-muted"),
                        cls="mb-4"
                    ),
                    Div(
                        H5("Phone", cls="mb-2"),
                        P("+1 (555) 123-4567", cls="text-muted"),
                        cls="mb-4"
                    ),
                    cls="col-md-6"
                ),
                
                cls="row"
            ),
            
            cls="py-5"
        )
    )
