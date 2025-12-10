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
from core.services.auth.decorators import require_permission
from core.utils.logger import get_logger

logger = get_logger(__name__)

router_settings = Router()


# ============================================================================
# Settings Dashboard
# ============================================================================

@router.get("/settings")
async def settings_dashboard(request):
    """Main settings page - shows categories user has access to"""
    user = request.state.user if hasattr(request.state, 'user') else None
    
    if not user:
        return RedirectResponse("/auth/login")
    
    user_roles = user.get("roles", [])
    
    # Get all settings user can see
    result = await settings_service.get_all_settings(
        user_roles=user_roles,
        context={"user_id": user.get("_id")}
    )
    
    if not result["success"]:
        return Alert("Failed to load settings", cls="alert-error")
    
    settings_by_category = result["settings"]
    
    return Layout(
        Div(
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
                    user=user
                )
                for group_name, categories in get_category_groups().items()
                if any(c in settings_by_category for c in categories)
            ],
            
            cls="container mx-auto p-8"
        )
    )


def get_category_groups() -> Dict[str, List[str]]:
    """Get organized category groups"""
    return {
        "Platform": ["platform", "auth"],
        "Integrations": ["integrations", "analytics"],
        "Site": ["seo", "social"],
        "User": ["preferences"],
        # Add-on categories will be detected dynamically
    }


def SettingsGroup(
    group_name: str,
    categories: List[str],
    settings_by_category: Dict,
    user: Dict
):
    """Group of related settings categories"""
    return Div(
        H2(group_name, cls="text-2xl font-bold mb-4"),
        
        Div(
            *[
                CategoryCard(
                    category=category,
                    settings=settings_by_category.get(category, {}),
                    user=user
                )
                for category in categories
                if category in settings_by_category
            ],
            cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12"
        ),
        
        id=group_name.lower().replace(" ", "-")
    )


def CategoryCard(category: str, settings: Dict, user: Dict):
    """Card for a settings category"""
    setting_count = len(settings)
    icon = get_category_icon(category)
    
    return Card(
        Div(
            # Icon
            Div(
                I(cls=f"fas fa-{icon} text-3xl text-primary"),
                cls="mb-4"
            ),
            
            # Title and count
            H3(category.replace("_", " ").title(), cls="text-xl font-bold mb-2"),
            P(f"{setting_count} setting{'s' if setting_count != 1 else ''}", 
              cls="text-sm text-gray-600 mb-4"),
            
            # Configure button
            Button(
                "Configure",
                cls="btn btn-primary btn-sm w-full",
                hx_get=f"/settings/{category}",
                hx_target="#settings-content",
                hx_swap="innerHTML"
            ),
            
            cls="p-6 text-center"
        ),
        cls="hover:shadow-lg transition-shadow"
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

@router.get("/settings/{category}")
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

@router.put("/api/settings/{key}")
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


@router.post("/api/settings/bulk")
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


# Export router
__all__ = ["router"]