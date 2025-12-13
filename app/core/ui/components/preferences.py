"""
User Preferences Panel Component

Displays user preferences in the settings page.
Includes theme, language, timezone, notifications, and accessibility options.
"""

from fasthtml.common import *
from monsterui.all import *


def PreferencesPanel(user_preferences: dict = None, user_id: str = None):
    """
    User preferences panel for settings page.
    
    Args:
        user_preferences: Current user preferences dict
        user_id: User ID for form submission
    """
    prefs = user_preferences or {}
    
    return Card(
        Div(
            H3("User Preferences", cls="text-lg font-semibold mb-4"),
            
            Form(
                # Appearance Section
                Div(
                    H4("Appearance", cls="font-medium mb-3 flex items-center"),
                    
                    # Theme
                    Div(
                        Label("Theme", cls="block text-sm font-medium mb-1"),
                        Select(
                            Option("Light", value="light", selected=prefs.get("theme") == "light"),
                            Option("Dark", value="dark", selected=prefs.get("theme") == "dark"),
                            Option("Auto (System)", value="auto", selected=prefs.get("theme") == "auto"),
                            name="theme",
                            cls="select select-bordered w-full max-w-xs"
                        ),
                        P("Choose your preferred color scheme", cls="text-xs text-gray-500 mt-1"),
                        cls="mb-4"
                    ),
                    
                    cls="mb-6 pb-6 border-b border-base-300"
                ),
                
                # Localization Section
                Div(
                    H4("Localization", cls="font-medium mb-3"),
                    
                    # Language
                    Div(
                        Label("Language", cls="block text-sm font-medium mb-1"),
                        Select(
                            Option("English", value="en", selected=prefs.get("language") == "en"),
                            Option("Español", value="es", selected=prefs.get("language") == "es"),
                            Option("Français", value="fr", selected=prefs.get("language") == "fr"),
                            Option("Deutsch", value="de", selected=prefs.get("language") == "de"),
                            Option("Português", value="pt", selected=prefs.get("language") == "pt"),
                            Option("中文", value="zh", selected=prefs.get("language") == "zh"),
                            Option("日本語", value="ja", selected=prefs.get("language") == "ja"),
                            name="language",
                            cls="select select-bordered w-full max-w-xs"
                        ),
                        cls="mb-4"
                    ),
                    
                    # Timezone
                    Div(
                        Label("Timezone", cls="block text-sm font-medium mb-1"),
                        Select(
                            Option("UTC", value="UTC", selected=prefs.get("timezone") == "UTC"),
                            Option("Eastern Time (US)", value="America/New_York", selected=prefs.get("timezone") == "America/New_York"),
                            Option("Pacific Time (US)", value="America/Los_Angeles", selected=prefs.get("timezone") == "America/Los_Angeles"),
                            Option("Central Time (US)", value="America/Chicago", selected=prefs.get("timezone") == "America/Chicago"),
                            Option("London (UK)", value="Europe/London", selected=prefs.get("timezone") == "Europe/London"),
                            Option("Paris (France)", value="Europe/Paris", selected=prefs.get("timezone") == "Europe/Paris"),
                            Option("Tokyo (Japan)", value="Asia/Tokyo", selected=prefs.get("timezone") == "Asia/Tokyo"),
                            Option("Shanghai (China)", value="Asia/Shanghai", selected=prefs.get("timezone") == "Asia/Shanghai"),
                            Option("Sydney (Australia)", value="Australia/Sydney", selected=prefs.get("timezone") == "Australia/Sydney"),
                            name="timezone",
                            cls="select select-bordered w-full max-w-xs"
                        ),
                        P("Used for displaying dates and times", cls="text-xs text-gray-500 mt-1"),
                        cls="mb-4"
                    ),
                    
                    cls="mb-6 pb-6 border-b border-base-300"
                ),
                
                # Notifications Section
                Div(
                    H4("Notifications", cls="font-medium mb-3"),
                    
                    # Email notifications
                    Div(
                        Label(
                            Input(
                                type="checkbox",
                                name="notifications_email",
                                checked=prefs.get("notifications.email", True),
                                cls="checkbox checkbox-primary mr-2"
                            ),
                            "Email Notifications",
                            cls="flex items-center cursor-pointer"
                        ),
                        P("Receive important updates via email", cls="text-xs text-gray-500 ml-6"),
                        cls="mb-3"
                    ),
                    
                    # Push notifications
                    Div(
                        Label(
                            Input(
                                type="checkbox",
                                name="notifications_push",
                                checked=prefs.get("notifications.push", False),
                                cls="checkbox checkbox-primary mr-2"
                            ),
                            "Push Notifications",
                            cls="flex items-center cursor-pointer"
                        ),
                        P("Receive browser push notifications", cls="text-xs text-gray-500 ml-6"),
                        cls="mb-3"
                    ),
                    
                    cls="mb-6 pb-6 border-b border-base-300"
                ),
                
                # Accessibility Section
                Div(
                    H4("Accessibility", cls="font-medium mb-3"),
                    
                    # Font size
                    Div(
                        Label("Font Size", cls="block text-sm font-medium mb-1"),
                        Select(
                            Option("Small", value="small", selected=prefs.get("accessibility.font_size") == "small"),
                            Option("Medium", value="medium", selected=prefs.get("accessibility.font_size", "medium") == "medium"),
                            Option("Large", value="large", selected=prefs.get("accessibility.font_size") == "large"),
                            Option("Extra Large", value="x-large", selected=prefs.get("accessibility.font_size") == "x-large"),
                            name="font_size",
                            cls="select select-bordered w-full max-w-xs"
                        ),
                        cls="mb-4"
                    ),
                    
                    # Reduce motion
                    Div(
                        Label(
                            Input(
                                type="checkbox",
                                name="reduced_motion",
                                checked=prefs.get("accessibility.reduced_motion", False),
                                cls="checkbox checkbox-primary mr-2"
                            ),
                            "Reduce Motion",
                            cls="flex items-center cursor-pointer"
                        ),
                        P("Minimize animations and transitions", cls="text-xs text-gray-500 ml-6"),
                        cls="mb-3"
                    ),
                    
                    # High contrast
                    Div(
                        Label(
                            Input(
                                type="checkbox",
                                name="high_contrast",
                                checked=prefs.get("accessibility.high_contrast", False),
                                cls="checkbox checkbox-primary mr-2"
                            ),
                            "High Contrast",
                            cls="flex items-center cursor-pointer"
                        ),
                        P("Use high contrast colors for better visibility", cls="text-xs text-gray-500 ml-6"),
                        cls="mb-3"
                    ),
                    
                    cls="mb-6"
                ),
                
                # Save button
                Div(
                    Button(
                        "Save Preferences",
                        type="submit",
                        cls="btn btn-primary"
                    ),
                    Span(
                        id="preferences-save-status",
                        cls="ml-3 text-sm"
                    ),
                    cls="flex items-center"
                ),
                
                hx_post="/api/preferences",
                hx_target="#preferences-save-status",
                hx_swap="innerHTML"
            ),
            
            cls="p-4"
        )
    )


def PreferencesSaveResponse(success: bool, message: str = None):
    """Response component for preferences save action."""
    if success:
        return Span(
            UkIcon("check", width="16", height="16", cls="inline mr-1"),
            message or "Saved!",
            cls="text-success"
        )
    else:
        return Span(
            UkIcon("alert-circle", width="16", height="16", cls="inline mr-1"),
            message or "Failed to save",
            cls="text-error"
        )
