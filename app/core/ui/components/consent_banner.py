from fasthtml.common import *
  
def consent_banner():
    return Div(
        H3("Cookie Preferences"),
        P("We use cookies to enhance your experience..."),
        Div(
            Button("Accept All", onclick="acceptCookies('all')"),
            Button("Reject Non-Essential", onclick="acceptCookies('necessary')"),
            Button("Customize", onclick="showCookieSettings()"),
            cls="cookie-banner-buttons"
        ),
        id="cookie-banner",
        cls="cookie-banner",
        style="display: none;"  # Show via JS if needed
    )
  
def cookie_settings_modal():
    return Dialog(
        H2("Cookie Settings"),
        Label(
            Input(type="checkbox", checked=True, disabled=True),
            "Essential Cookies (Required)"
        ),
        Label(
            Input(type="checkbox", id="analytics-consent"),
            "Analytics Cookies"
        ),
        Label(
            Input(type="checkbox", id="marketing-consent"),
            "Marketing Cookies"
        ),
        Button("Save Preferences", onclick="saveCookiePreferences()"),
        id="cookie-settings-modal"
    )