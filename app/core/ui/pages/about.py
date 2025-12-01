"""About Page"""
from fasthtml.common import *
from monsterui.all import *

def AboutPage():
    return Container(
        Div(
            H1("About FastApp", cls="display-4 mb-4"),
            P("FastApp is a modern web application framework built on FastHTML and MonsterUI.", cls="lead"),
            
            H2("Our Mission", cls="mt-5 mb-3"),
            P("We believe building web applications should be simple, fast, and enjoyable. "
              "Our mission is to provide developers with powerful tools without the complexity."),
            
            H2("Key Features", cls="mt-5 mb-3"),
            Ul(
                Li("Lightning-fast development with FastHTML"),
                Li("Beautiful UI with MonsterUI components"),
                Li("Modular add-on system (LMS, Commerce, Social)"),
                Li("Secure by default with built-in authentication"),
                Li("Full-stack Python development"),
                cls="list-group list-group-flush"
            ),
            
            H2("Technology Stack", cls="mt-5 mb-3"),
            Div(
                Div(
                    H5("Frontend", cls="card-title"),
                    P("FastHTML + MonsterUI + HTMX", cls="card-text"),
                    cls="card-body"
                ),
                Div(
                    H5("Backend", cls="card-title"),
                    P("Python + FastAPI + SQLAlchemy", cls="card-text"),
                    cls="card-body"
                ),
                Div(
                    H5("Database", cls="card-title"),
                    P("PostgreSQL + Redis", cls="card-text"),
                    cls="card-body"
                ),
                cls="row row-cols-1 row-cols-md-3 g-4"
            ),
            
            cls="py-5"
        )
    )
