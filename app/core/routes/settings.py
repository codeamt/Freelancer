"""
Settings Routes - UI and API endpoints for settings management

Features:
- Settings dashboard organized by category
- Permission-aware (only shows accessible settings)
- Masked display of sensitive values
- Integration testing
- Import/export
"""

from fasthtml.common import *
from monsterui.all import *
from typing import Dict, Any, List
import json

from core.services.settings import (
    settings_service,
    settings_registry,
    SettingType,
    SettingSensitivity
)
from core.services.auth.decorators import require_permission, require_auth
from core.ui.layout import Layout
from core.utils.logger import get_logger

logger = get_logger(__name__)

router_settings = APIRouter()


# ============================================================================
# Settings Dashboard
# ============================================================================

@router_settings.get("/settings")
@require_auth(redirect_to="/auth?tab=login")
async def settings_dashboard(request):
    """Main settings page - shows categories user has access to"""
    user = request.state.user
    demo = getattr(request.app.state, 'demo', False)
    
    # Build user dict for Layout - handle both dict and object user
    if isinstance(user, dict):
        user_dict = user
        user_roles = user.get("roles", [user.get("role", "user")])
        user_id = user.get("_id") or user.get("id")
    else:
        user_dict = {
            "username": getattr(user, 'username', getattr(user, 'email', '').split('@')[0]),
            "email": getattr(user, 'email', ''),
            "role": getattr(user, 'role', 'user'),
            "_id": str(getattr(user, 'id', ''))
        }
        user_roles = [getattr(user, 'role', 'user')]
        user_id = getattr(user, 'id', None)
    
    # Get all settings user can see
    result = await settings_service.get_all_settings(
        user_roles=user_roles,
        context={"user_id": user_id}
    )
    
    if not result["success"]:
        return Alert("Failed to load settings", cls="alert-error")
    
    settings_by_category = result["settings"]
    
    content = Div(
        # Header
        Div(
            H1("Settings", cls="text-3xl font-bold"),
            P("Manage your platform, integrations, and preferences", 
              cls="text-gray-600 mt-2"),
            cls="mb-8"
        ),
        
        # Category groups
        *[
            SettingsGroup(
                group_name=group_name,
                categories=categories,
                settings_by_category=settings_by_category,
                user=user_dict
            )
            for group_name, categories in get_category_groups().items()
            if any(c in settings_by_category for c in categories)
        ],
        
        cls="container mx-auto p-8"
    )
    
    return Layout(content, title="Settings | FastApp", current_path="/settings", user=user_dict, show_auth=True, demo=demo)


def get_category_groups() -> Dict[str, List[str]]:
    """Get organized category groups"""
    return {
        "Platform": ["platform", "auth"],
        "Integrations": ["integrations", "analytics"],
        "Site": ["seo", "social"],
        "User": ["preferences", "cookies"],
        # Add-on categories will be detected dynamically
    }


def SettingsGroup(
    group_name: str,
    categories: List[str],
    settings_by_category: Dict,
    user: Dict
):
    """Group of related settings categories with inline switches"""
    # Collect all settings for this group
    group_settings = []
    for category in categories:
        if category in settings_by_category:
            for key, setting_data in settings_by_category[category].items():
                group_settings.append((key, setting_data, category))
    
    if not group_settings:
        return None
    
    return Div(
        H2(group_name, cls="text-2xl font-bold mb-4"),
        
        # Settings list with switches/inputs
        Div(
            *[
                SettingRow(key, setting_data, category)
                for key, setting_data, category in group_settings
            ],
            cls="space-y-2 mb-8"
        ),
        
        id=group_name.lower().replace(" ", "-")
    )


def SettingRow(key: str, setting_data: Dict, category: str):
    """Single setting row with appropriate input control"""
    definition = setting_data.get("definition", {})
    value = setting_data.get("value")
    masked = setting_data.get("masked", False)
    
    setting_type = definition.get("type", "string")
    name = definition.get("name", key.split(".")[-1].replace("_", " ").title())
    description = definition.get("description", "")
    options = definition.get("options", [])
    ui_component = definition.get("ui_component", "text")
    
    # Determine the input control based on type
    if setting_type == "boolean":
        input_control = Div(
            Input(
                type="checkbox",
                name=key,
                checked=bool(value),
                cls="toggle toggle-primary",
                hx_post=f"/api/settings/{key}",
                hx_trigger="change",
                hx_swap="none"
            ),
            cls="flex items-center"
        )
    elif options and ui_component == "select":
        input_control = Select(
            *[Option(opt, value=opt, selected=(value == opt)) for opt in options],
            name=key,
            cls="select select-bordered select-sm w-40",
            hx_post=f"/api/settings/{key}",
            hx_trigger="change",
            hx_swap="none"
        )
    elif ui_component == "password" or masked:
        input_control = Input(
            type="password",
            name=key,
            value="********" if masked else (value or ""),
            placeholder="Enter value...",
            cls="input input-bordered input-sm w-48",
            disabled=masked
        )
    elif setting_type == "integer":
        input_control = Input(
            type="number",
            name=key,
            value=str(value) if value is not None else "",
            cls="input input-bordered input-sm w-24",
            hx_post=f"/api/settings/{key}",
            hx_trigger="change",
            hx_swap="none"
        )
    else:
        input_control = Input(
            type="text",
            name=key,
            value=str(value) if value is not None else "",
            placeholder=definition.get("placeholder", ""),
            cls="input input-bordered input-sm w-48",
            hx_post=f"/api/settings/{key}",
            hx_trigger="change delay:500ms",
            hx_swap="none"
        )
    
    return Div(
        # Left side: name and description
        Div(
            Span(name, cls="font-medium"),
            P(description, cls="text-xs text-gray-500") if description else None,
            cls="flex-1"
        ),
        # Right side: input control
        input_control,
        cls="flex items-center justify-between p-3 bg-base-200 rounded-lg hover:bg-base-300 transition-colors"
    )


def get_category_icon(category: str) -> str:
    """Get FontAwesome icon for category"""
    icons = {
        "platform": "server",
        "auth": "lock",
        "integrations": "plug",
        "analytics": "chart-line",
        "seo": "search",
        "social": "share-alt",
        "preferences": "user-cog"
    }
    return icons.get(category, "cog")


# ============================================================================
# Category Settings View
# ============================================================================

@router_settings.get("/settings/{category}")
async def category_settings(request, category: str):
    """Settings for specific category"""
    user = request.state.user if hasattr(request.state, 'user') else None
    
    if not user:
        return RedirectResponse("/auth/login")
    
    user_roles = user.get("roles", [])
    
    result = await settings_service.get_category_settings(
        category=category,
        user_roles=user_roles,
        context={"user_id": user.get("_id")}
    )
    
    if not result["success"]:
        return Alert(f"Failed to load {category} settings", cls="alert-error")
    
    return CategorySettingsPanel(
        category=category,
        settings=result["settings"],
        user_roles=user_roles
    )


def CategorySettingsPanel(category: str, settings: Dict, user_roles: List[str]):
    """Panel showing all settings in a category"""
    return Div(
        # Header
        Div(
            Div(
                H2(category.replace("_", " ").title(), cls="text-2xl font-bold"),
                Badge(f"{len(settings)} settings", cls="badge badge-neutral"),
                cls="flex items-center gap-3"
            ),
            Button(
                I(cls="fas fa-arrow-left"),
                " Back",
                cls="btn btn-sm btn-ghost",
                hx_get="/settings",
                hx_target="body",
                hx_swap="innerHTML"
            ),
            cls="flex items-center justify-between mb-6 pb-4 border-b"
        ),
        
        # Settings form
        Form(
            *[
                SettingField(key, setting_data)
                for key, setting_data in settings.items()
            ],
            
            # Save button
            Div(
                Button(
                    I(cls="fas fa-save"),
                    " Save Changes",
                    type="submit",
                    cls="btn btn-primary"
                ),
                Button(
                    "Reset",
                    type="reset",
                    cls="btn btn-ghost"
                ),
                cls="flex gap-2 mt-6 pt-6 border-t"
            ),
            
            hx_post="/api/settings/bulk",
            hx_target="#settings-content",
            hx_swap="innerHTML"
        ),
        
        id="settings-content",
        cls="p-6"
    )


def SettingField(key: str, setting_data: Dict):
    """Individual setting field"""
    definition = setting_data.get("definition", {})
    value = setting_data.get("value")
    masked = setting_data.get("masked", False)
    
    name = definition.get("name", key)
    description = definition.get("description", "")
    setting_type = definition.get("type", "string")
    ui_component = definition.get("ui_component", "text")
    options = definition.get("options", [])
    placeholder = definition.get("placeholder", "")
    help_text = definition.get("help_text", "")
    
    return Div(
        # Label and description
        Div(
            Label(
                name,
                _for=key,
                cls="label-text text-lg font-bold"
            ),
            P(description, cls="text-sm text-gray-600 mt-1"),
            cls="mb-2"
        ),
        
        # Input field
        _render_input_field(
            key,
            value,
            setting_type,
            ui_component,
            options,
            placeholder,
            masked
        ),
        
        # Help text
        (P(help_text, cls="text-xs text-gray-500 mt-1") if help_text else None),
        
        cls="form-control mb-6"
    )


def _render_input_field(
    key: str,
    value: Any,
    setting_type: str,
    ui_component: str,
    options: List,
    placeholder: str,
    masked: bool
):
    """Render appropriate input field based on type"""
    
    # Masked field (password-like)
    if masked:
        return Div(
            Input(
                type="password",
                name=key,
                value="********",
                placeholder="Enter new value to change",
                cls="input input-bordered w-full"
            ),
            Div(
                I(cls="fas fa-lock text-warning"),
                Span(" Value is hidden for security", cls="ml-2"),
                cls="flex items-center text-sm text-warning mt-1"
            )
        )
    
    # Boolean (checkbox)
    if setting_type == "boolean":
        return Label(
            Input(
                type="checkbox",
                name=key,
                checked=bool(value),
                cls="toggle toggle-primary"
            ),
            Span(" Enabled", cls="ml-3"),
            cls="label cursor-pointer justify-start"
        )
    
    # Select dropdown
    if ui_component == "select" and options:
        return Select(
            *[
                Option(opt, value=opt, selected=(opt == value))
                for opt in options
            ],
            name=key,
            cls="select select-bordered w-full"
        )
    
    # Integer
    if setting_type == "integer":
        return Input(
            type="number",
            name=key,
            value=value if value is not None else "",
            placeholder=placeholder,
            cls="input input-bordered w-full"
        )
    
    # JSON (textarea)
    if setting_type == "json" or ui_component == "json":
        json_value = json.dumps(value, indent=2) if value else ""
        return Textarea(
            json_value,
            name=key,
            rows=6,
            placeholder=placeholder or '{"key": "value"}',
            cls="textarea textarea-bordered w-full font-mono text-sm"
        )
    
    # Password
    if ui_component == "password":
        return Input(
            type="password",
            name=key,
            value=value if value else "",
            placeholder=placeholder,
            cls="input input-bordered w-full"
        )
    
    # Default: text input
    return Input(
        type="text",
        name=key,
        value=value if value else "",
        placeholder=placeholder,
        cls="input input-bordered w-full"
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router_settings.put("/api/settings/{key}")
async def update_setting(request, key: str):
    """Update a single setting"""
    user = request.state.user if hasattr(request.state, 'user') else None
    
    if not user:
        return {"success": False, "error": "Unauthorized"}
    
    # Get value from form data
    form = await request.form()
    value = form.get("value")
    
    user_roles = user.get("roles", [])
    
    result = await settings_service.set_setting(
        key=key,
        value=value,
        user_roles=user_roles,
        context={"user_id": user.get("_id")}
    )
    
    if result["success"]:
        return Alert("Setting updated successfully", cls="alert-success")
    else:
        return Alert(f"Error: {result.get('error')}", cls="alert-error")


@router_settings.post("/api/settings/bulk")
async def update_multiple_settings(request):
    """Update multiple settings at once"""
    user = request.state.user if hasattr(request.state, 'user') else None
    
    if not user:
        return {"success": False, "error": "Unauthorized"}
    
    # Get form data
    form = await request.form()
    settings = dict(form)
    
    user_roles = user.get("roles", [])
    
    result = await settings_service.set_multiple_settings(
        settings=settings,
        user_roles=user_roles,
        context={"user_id": user.get("_id")}
    )
    
    if result["success"]:
        return Alert(
            f"✓ Updated {result['succeeded']} settings successfully",
            cls="alert-success"
        )
    else:
        return Alert(
            f"Updated {result['succeeded']} settings, {result['failed']} failed",
            cls="alert-warning"
        )


# ============================================================================
# Preferences API
# ============================================================================

@router_settings.post("/api/preferences")
@require_auth(redirect_to="/auth?tab=login")
async def save_preferences(request: Request):
    """Save user preferences."""
    user = request.state.user
    
    # Build user info
    if isinstance(user, dict):
        user_id = user.get("_id") or user.get("id")
        user_roles = user.get("roles", [user.get("role", "user")])
    else:
        user_id = getattr(user, 'id', None)
        user_roles = [getattr(user, 'role', 'user')]
    
    form = await request.form()
    
    # Map form fields to setting keys
    preference_mappings = {
        "theme": "user.theme",
        "language": "user.language",
        "timezone": "user.timezone",
        "notifications_email": "user.notifications.email",
        "notifications_push": "user.notifications.push",
        "font_size": "user.accessibility.font_size",
        "reduced_motion": "user.accessibility.reduced_motion",
        "high_contrast": "user.accessibility.high_contrast",
    }
    
    settings_to_save = {}
    for form_key, setting_key in preference_mappings.items():
        if form_key in form:
            value = form.get(form_key)
            # Handle checkboxes (present = true, absent = false)
            if form_key in ["notifications_email", "notifications_push", "reduced_motion", "high_contrast"]:
                settings_to_save[setting_key] = value == "on" or value == "true" or value == True
            else:
                settings_to_save[setting_key] = value
        elif form_key in ["notifications_email", "notifications_push", "reduced_motion", "high_contrast"]:
            # Checkbox not present means unchecked
            settings_to_save[preference_mappings[form_key]] = False
    
    # Save preferences
    result = await settings_service.set_multiple_settings(
        settings=settings_to_save,
        user_roles=user_roles,
        context={"user_id": str(user_id)}
    )
    
    if result["success"]:
        return Span(
            UkIcon("check", width="16", height="16", cls="inline mr-1"),
            "Saved!",
            cls="text-success"
        )
    else:
        return Span(
            UkIcon("alert-circle", width="16", height="16", cls="inline mr-1"),
            f"Failed to save {result['failed']} preferences",
            cls="text-error"
        )


# ============================================================================
# Individual Setting API
# ============================================================================

@router_settings.post("/api/settings/{key:path}")
@require_auth(redirect_to="/auth?tab=login")
async def save_single_setting(request: Request, key: str):
    """Save a single setting value via HTMX."""
    user = request.state.user
    
    # Build user info
    if isinstance(user, dict):
        user_id = user.get("_id") or user.get("id")
        user_roles = user.get("roles", [user.get("role", "user")])
    else:
        user_id = getattr(user, 'id', None)
        user_roles = [getattr(user, 'role', 'user')]
    
    form = await request.form()
    
    # Get the value - handle checkbox (on/off) vs regular values
    value = form.get(key)
    
    # Check if this is a boolean setting
    definition = settings_registry.get(key)
    if definition and definition.type.value == "boolean":
        # Checkbox: "on" means true, absence means false
        value = value == "on" or value == "true"
    elif definition and definition.type.value == "integer":
        try:
            value = int(value) if value else None
        except ValueError:
            pass
    
    # Save the setting
    result = await settings_service.set_setting(
        key=key,
        value=value,
        user_roles=user_roles,
        context={"user_id": str(user_id)}
    )
    
    # Return empty response for HTMX (hx-swap="none")
    return ""


# Export router
__all__ = ["router_settings"]