from fasthtml.common import *
from app.core.ui.components import CTAButton

def ContactPage():
    return section(
        div(
            H1("Contact Us", cls="text-4xl font-bold mb-6"),
            P("We'd love to hear from you! Reach out to us with any questions, feedback, or inquiries.", 
              cls="text-lg mb-8"),
            
            H2("Get in Touch", cls="text-2xl font-bold mt-8 mb-4"),
            
            # Contact form
            Form(
                Fieldset(
                    Legend("Send us a message", cls="text-xl font-semibold mb-4"),
                    Div(
                        Label("Name", fr="name", cls="block text-sm font-medium mb-1"),
                        Input(type="text", id="name", name="name", 
                              cls="w-full px-3 py-2 border border-gray-300 rounded-md"),
                        cls="mb-4"
                    ),
                    Div(
                        Label("Email", fr="email", cls="block text-sm font-medium mb-1"),
                        Input(type="email", id="email", name="email", 
                              cls="w-full px-3 py-2 border border-gray-300 rounded-md"),
                        cls="mb-4"
                    ),
                    Div(
                        Label("Subject", fr="subject", cls="block text-sm font-medium mb-1"),
                        Input(type="text", id="subject", name="subject", 
                              cls="w-full px-3 py-2 border border-gray-300 rounded-md"),
                        cls="mb-4"
                    ),
                    Div(
                        Label("Message", fr="message", cls="block text-sm font-medium mb-1"),
                        Textarea(id="message", name="message", rows="5", 
                                 cls="w-full px-3 py-2 border border-gray-300 rounded-md"),
                        cls="mb-6"
                    ),
                    Button("Send Message", type="submit", 
                           cls="bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700 transition-colors"),
                    cls="max-w-lg mx-auto"
                ),
                hx_post="/contact",
                hx_target="#form-response",
                cls="mb-12"
            ),
            Div(id="form-response", cls="max-w-lg mx-auto mb-8"),
            
            # Contact information
            H2("Contact Information", cls="text-2xl font-bold mt-12 mb-4"),
            Div(
                Div(
                    H3("Email", cls="text-lg font-semibold mb-2"),
                    P("support@fastapp.example.com", cls="mb-4"),
                    cls="mb-6"
                ),
                Div(
                    H3("Address", cls="text-lg font-semibold mb-2"),
                    P("123 Developer Street", cls="mb-1"),
                    P("San Francisco, CA 94103", cls="mb-4"),
                    cls="mb-6"
                ),
                Div(
                    H3("Phone", cls="text-lg font-semibold mb-2"),
                    P("+1 (555) 123-4567", cls="mb-4"),
                    cls="mb-6"
                ),
                cls="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto"
            ),
            cls="max-w-6xl mx-auto py-12"
        )
    )
