"""
Cookie Consent Banner Component

Displays a cookie consent banner for GDPR compliance.
Only handles essential cookies (necessary for site functionality).
"""

from fasthtml.common import *
from monsterui.all import *


def CookieConsentBanner(base_path: str = ""):
    """
    Cookie consent banner component.
    
    Shows a simple banner for essential cookies only.
    Uses localStorage to track consent and hide banner after acceptance.
    
    Args:
        base_path: Base path for the app (e.g., "/eshop-example")
    """
    return Div(
        Div(
            # Cookie icon and message
            Div(
                Div(
                    UkIcon("cookie", width="24", height="24"),
                    cls="mr-3 text-primary"
                ),
                Div(
                    P(
                        Strong("We use essential cookies"),
                        " to ensure the best experience on our site. These cookies are necessary for the website to function properly.",
                        cls="text-sm mb-0"
                    ),
                    A(
                        "Learn more",
                        href=f"{base_path}/privacy" if base_path else "/privacy",
                        cls="text-xs text-primary hover:underline"
                    ),
                    cls="flex-1"
                ),
                cls="flex items-start"
            ),
            
            # Accept button
            Div(
                Button(
                    "Accept",
                    onclick="acceptCookies()",
                    cls="btn btn-primary btn-sm"
                ),
                cls="mt-3 md:mt-0 md:ml-4"
            ),
            
            cls="flex flex-col md:flex-row md:items-center justify-between"
        ),
        
        # JavaScript for consent handling
        Script("""
            function acceptCookies() {
                // Set consent in localStorage
                localStorage.setItem('cookie_consent', 'true');
                localStorage.setItem('cookie_consent_date', new Date().toISOString());
                
                // Set cookie for server-side detection
                document.cookie = 'cookie_consent=true; path=/; max-age=31536000; SameSite=Lax';
                
                // Hide the banner and reset footer position
                document.getElementById('cookie-consent-banner').style.display = 'none';
                var footer = document.getElementById('main-footer');
                if (footer) footer.style.bottom = '0';
            }
            
            // Check if consent already given and adjust footer - run after small delay to ensure DOM is ready
            setTimeout(function() {
                var banner = document.getElementById('cookie-consent-banner');
                var footer = document.getElementById('main-footer');
                
                // Check cookie directly (more reliable than localStorage on page load)
                var hasConsent = document.cookie.split(';').some(function(c) {
                    return c.trim().startsWith('cookie_consent=true');
                }) || localStorage.getItem('cookie_consent') === 'true';
                
                if (hasConsent) {
                    if (banner) banner.style.display = 'none';
                    if (footer) footer.style.bottom = '0';
                } else {
                    // Show banner and push footer up
                    if (banner) {
                        banner.style.display = 'block';
                        if (footer) {
                            footer.style.bottom = banner.offsetHeight + 'px';
                        }
                    }
                }
            }, 100);
        """),
        
        id="cookie-consent-banner",
        cls="fixed bottom-0 left-0 right-0 bg-base-100 border-t border-base-300 p-4 shadow-lg z-50"
    )


def CookieSettingsPanel(user_preferences: dict = None):
    """
    Cookie settings panel for the settings page.
    
    Shows cookie preferences that users can manage.
    For essential-only cookies, this is informational.
    
    Args:
        user_preferences: Current user preferences dict
    """
    prefs = user_preferences or {}
    consent_given = prefs.get("cookies.consent_given", False)
    consent_date = prefs.get("cookies.consent_date", "")
    
    return Card(
        Div(
            H3("Cookie Preferences", cls="text-lg font-semibold mb-4"),
            
            # Essential cookies (always on)
            Div(
                Div(
                    Div(
                        Strong("Essential Cookies"),
                        Span("Always Active", cls="badge badge-success badge-sm ml-2"),
                        cls="flex items-center"
                    ),
                    P(
                        "These cookies are necessary for the website to function and cannot be switched off. "
                        "They are usually only set in response to actions made by you such as logging in or filling in forms.",
                        cls="text-sm text-gray-600 mt-1"
                    ),
                    cls="flex-1"
                ),
                cls="p-4 bg-base-200 rounded-lg mb-4"
            ),
            
            # Consent status
            Div(
                H4("Your Consent Status", cls="font-medium mb-2"),
                Div(
                    UkIcon("check-circle" if consent_given else "alert-circle", width="20", height="20"),
                    Span(
                        "Consent given" if consent_given else "No consent recorded",
                        cls="ml-2"
                    ),
                    cls=f"flex items-center {'text-success' if consent_given else 'text-warning'}"
                ),
                P(
                    f"Date: {consent_date}" if consent_date else "You can accept cookies using the banner at the bottom of the page.",
                    cls="text-sm text-gray-500 mt-1"
                ) if consent_given else None,
                cls="mt-4"
            ),
            
            # Withdraw consent button (if consent given)
            Div(
                Button(
                    "Withdraw Consent",
                    onclick="withdrawCookieConsent()",
                    cls="btn btn-outline btn-sm mt-4"
                ),
                Script("""
                    function withdrawCookieConsent() {
                        localStorage.removeItem('cookie_consent');
                        localStorage.removeItem('cookie_consent_date');
                        document.cookie = 'cookie_consent=; path=/; max-age=0';
                        location.reload();
                    }
                """),
                cls="mt-4"
            ) if consent_given else None,
            
            cls="p-4"
        )
    )
