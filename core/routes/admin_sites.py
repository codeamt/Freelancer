"""Admin routes for single-site management with draft/published versions.

Architecture:
- Single site per installation (not multi-tenant SaaS)
- Draft version for editing
- Published version for live site
- Version history for rollback
"""

from fasthtml.common import *
from monsterui.all import *
from core.services.admin.decorators import require_admin
from core.state.persistence import InMemoryPersister, MongoPersister
from core.workflows.admin import SiteWorkflowManager
from core.ui.state.config import ComponentLibrary, ComponentType, VisibilityCondition
from core.ui.state.actions import AddComponentAction, RemoveComponentAction, ToggleComponentAction
from core.ui.theme.editor import ThemeEditorManager
from core.ui.pages.landing_page import LandingPage, Section, SiteGraph, ThemeStyles
from core.ui.pages.home import HomePage
from core.utils.logger import get_logger

logger = get_logger(__name__)

# Single site identifier (could be from config or environment)
SITE_ID = "main"  # Single site for this installation

# Initialize managers
try:
    from core.services.base.mongo_service import get_db
    db = get_db()
    persister = MongoPersister(db, "site_states") if db else InMemoryPersister()
except:
    persister = InMemoryPersister()

workflow_manager = SiteWorkflowManager(persister=persister)
theme_manager = ThemeEditorManager(persister=persister)

router_admin_sites = APIRouter()


# ============================================================================
# Main Site Editor Dashboard
# ============================================================================

@router_admin_sites.get("/admin/site")
@require_admin
async def site_editor_dashboard(request):
    """Main site editor dashboard - overview of all site management tools."""
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    # Initialize the landing page
    landing_page = HomePage(SITE_ID)
    
    # Load site state if available
    try:
        site_result = await workflow_manager.load_site(SITE_ID, user_id, partition_key="draft")
        if site_result["success"]:
            state = site_result["state"]
            landing_page.from_dict(state)
    except Exception as e:
        logger.warning(f"Could not load site state: {e}")
        # Use default sections
        pass
    
    sections = landing_page.site_graph.sections
    
    return Card(
        Div(
            H2("Site Editor Dashboard", cls="text-2xl font-bold mb-6"),
            
            # Quick stats
            Div(
                Div(
                    H4("Site Status", cls="font-bold"),
                    P("Draft Mode", cls="text-sm text-gray-600"),
                    Span("In Progress" if landing_page.is_dirty() else "Saved", cls="badge badge-warning" if landing_page.is_dirty() else "badge badge-success")
                ),
                Div(
                    H4("Last Updated", cls="font-bold"),
                    P("Just now", cls="text-sm text-gray-600"),
                    Span("Active", cls="badge badge-success")
                ),
                Div(
                    H4("Components", cls="font-bold"),
                    P(f"{len(sections)} sections", cls="text-sm text-gray-600"),
                    Span("Ready", cls="badge badge-info")
                ),
                cls="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6"
            ),
            
            # Quick actions
            H3("Quick Actions", cls="text-lg font-bold mb-4"),
            Div(
                A("Manage Components", href="/admin/site/components", cls="btn btn-primary mr-2"),
                A("Edit Theme", href="/admin/site/theme", cls="btn btn-secondary mr-2"),
                A("Preview Site", href="/admin/site/preview", cls="btn btn-outline mr-2"),
                A("Compare & Publish", href="/admin/site/compare", cls="btn btn-accent"),
                cls="mb-6"
            ),
            
            # Section overview
            H3("Current Sections", cls="text-lg font-bold mb-4"),
            Div(
                *[Div(
                    Div(
                        Div(
                            H5(section.title, cls="font-bold"),
                            P(f"Type: {section.type}", cls="text-sm text-gray-600"),
                            P(f"Order: {section.order}", cls="text-sm text-gray-600"),
                            Span("Visible" if section.visible else "Hidden", cls=f"badge {'badge-success' if section.visible else 'badge-secondary'}")
                        ),
                        Div(
                            Button("Edit", cls="btn btn-sm btn-outline mr-1"),
                            Button("Toggle", cls="btn btn-sm btn-outline mr-1"),
                            Button("Remove", cls="btn btn-sm btn-error")
                        ),
                        cls="flex justify-between items-center"
                    ),
                    cls="border rounded p-3 mb-2"
                ) for section in sections],
                cls="space-y-2 mb-6"
            ),
            
            # Recent activity
            H3("Recent Activity", cls="text-lg font-bold mb-4"),
            Div(
                Div(
                    P("Dashboard accessed", cls="text-sm"),
                    P("Just now", cls="text-xs text-gray-500"),
                    cls="border-l-4 border-blue-500 pl-4 mb-2"
                ),
                Div(
                    P(f"Site loaded with {len(sections)} sections", cls="text-sm"),
                    P("1 minute ago", cls="text-xs text-gray-500"),
                    cls="border-l-4 border-green-500 pl-4 mb-2"
                ),
                Div(
                    P("Admin session started", cls="text-sm"),
                    P("2 minutes ago", cls="text-xs text-gray-500"),
                    cls="border-l-4 border-yellow-500 pl-4 mb-2"
                ),
                cls="space-y-2"
            ),
            
            cls="p-6"
        )
    )


@router_admin_sites.get("/admin/site/edit")
@require_admin
async def site_editor(request):
    """Alias for main site editor dashboard."""
    return await site_editor_dashboard(request)


# ============================================================================
# Component Management Routes
# ============================================================================

@router_admin_sites.get("/admin/site/components")
@require_admin
async def manage_components(request):
    """Component management interface."""
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    # Load draft version of site
    site_result = await workflow_manager.load_site(SITE_ID, user_id, partition_key="draft")
    if not site_result["success"]:
        return Alert(f"Error: {site_result.get('error')}", cls="alert-error")
    
    state = site_result["state"]
    site_graph = state.get("site_graph", {})
    sections = site_graph.get("sections", [])
    
    return Card(
        Div(
            H2("Component Management", cls="text-2xl font-bold mb-6"),
            
            # Section selector
            Select(
                *[Option(f"{s['id']} ({s['type']})", value=s['id']) for s in sections],
                name="section_id",
                id="section-selector",
                hx_get="/admin/site/components/section",
                hx_target="#component-list",
                hx_trigger="change",
                cls="select select-bordered w-full mb-4"
            ),
            
            # Component list for selected section
            Div(id="component-list", cls="mb-6"),
            
            # Component library
            Details(
                Summary("Add Component from Library", cls="font-bold cursor-pointer mb-2"),
                Div(
                    H3("Pre-built Components", cls="text-lg font-bold mb-4"),
                    
                    Div(
                        *[
                            Card(
                                Div(
                                    H4(comp_name, cls="font-bold"),
                                    P(comp_desc, cls="text-sm text-gray-600 mb-2"),
                                    ButtonPrimary(
                                        "Add to Section",
                                        hx_post="/admin/site/components/add-preset",
                                        hx_vals=f'{{"preset": "{comp_id}"}}',
                                        hx_include="#section-selector",
                                        hx_target="#component-list"
                                    ),
                                    cls="p-3"
                                ),
                                cls="mb-2"
                            )
                            for comp_id, comp_name, comp_desc in [
                                ("signup_cta", "Sign Up CTA", "Call-to-action for new users (hidden for members)"),
                                ("dashboard_cta", "Dashboard CTA", "Link to dashboard (members only)"),
                                ("contact_form", "Contact Form", "Standard contact form"),
                                ("hero_banner", "Hero Banner", "Large hero section with CTA"),
                                ("admin_nav", "Admin Navigation", "Admin-only navigation menu")
                            ]
                        ],
                        cls="grid grid-cols-1 md:grid-cols-2 gap-4"
                    )
                ),
                cls="mb-4"
            ),
            
            # Back button
            ButtonSecondary(
                "Back to Site Editor",
                hx_get="/admin/site/edit",
                hx_target="#site-content"
            ),
            
            cls="p-4"
        )
    )


@router_admin_sites.get("/admin/site/components/section")
@require_admin
async def get_section_components(request, section_id: str):
    """Get components for a specific section."""
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    site_result = await workflow_manager.load_site(SITE_ID, user_id, partition_key="draft")
    if not site_result["success"]:
        return Alert(f"Error: {site_result.get('error')}", cls="alert-error")
    
    state = site_result["state"]
    site_graph = state.get("site_graph", {})
    
    # Find section
    section = None
    for s in site_graph.get("sections", []):
        if s["id"] == section_id:
            section = s
            break
    
    if not section:
        return P("Section not found", cls="text-gray-600")
    
    components = section.get("components", [])
    
    if not components:
        return P("No components in this section", cls="text-gray-600")
    
    return Div(
        H3(f"Components in {section_id}", cls="text-lg font-bold mb-4"),
        *[
            Card(
                Div(
                    Div(
                        H4(comp["name"], cls="font-bold"),
                        Badge(comp["type"], cls="badge-primary"),
                        Badge("Enabled" if comp.get("enabled", True) else "Disabled",
                              cls="badge-success" if comp.get("enabled", True) else "badge-error"),
                        cls="flex items-center gap-2 mb-2"
                    ),
                    
                    P(f"Visibility: {comp.get('visibility', 'always')}", cls="text-sm text-gray-600 mb-2"),
                    
                    # Content preview
                    Details(
                        Summary("View Content", cls="text-sm cursor-pointer"),
                        Pre(str(comp.get("content", {})), cls="text-xs bg-gray-100 p-2 rounded"),
                        cls="mb-2"
                    ),
                    
                    # Actions
                    Div(
                        ButtonSecondary(
                            "Toggle",
                            hx_post="/admin/site/components/toggle",
                            hx_vals=f'{{"section_id": "{section_id}", "component_id": "{comp["id"]}"}}',
                            hx_target="#component-list",
                            cls="btn-sm"
                        ),
                        ButtonSecondary(
                            "Edit Visibility",
                            hx_get=f"/admin/site/components/{comp['id']}/visibility",
                            hx_vals=f'{{"section_id": "{section_id}"}}',
                            hx_target="#visibility-modal",
                            cls="btn-sm"
                        ),
                        ButtonDanger(
                            "Remove",
                            hx_post="/admin/site/components/remove",
                            hx_vals=f'{{"section_id": "{section_id}", "component_id": "{comp["id"]}"}}',
                            hx_target="#component-list",
                            hx_confirm="Remove this component?",
                            cls="btn-sm"
                        ),
                        cls="flex gap-2"
                    ),
                    
                    cls="p-3"
                ),
                cls="mb-2"
            )
            for comp in components
        ],
        
        # Modal container
        Div(id="visibility-modal")
    )


@router_admin_sites.post("/admin/site/components/add-preset")
@require_admin
async def add_preset_component(request, preset: str, section_id: str):
    """Add a preset component to a section."""
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    # Get preset component
    library = ComponentLibrary()
    component_map = {
        "signup_cta": library.create_signup_cta,
        "dashboard_cta": library.create_member_dashboard_cta,
        "admin_nav": library.create_admin_only_nav,
        "contact_form": library.create_contact_form,
        "hero_banner": library.create_hero_banner
    }
    
    if preset not in component_map:
        return Alert("Invalid preset", cls="alert-error")
    
    component_config = component_map[preset]()
    
    # Load draft state and add component
    site_result = await workflow_manager.load_site(SITE_ID, user_id, partition_key="draft")
    if not site_result["success"]:
        return Alert(f"Error: {site_result.get('error')}", cls="alert-error")
    
    from core.state.state import State
    state = State(site_result["state"])
    
    action = AddComponentAction()
    new_state, result = await action.execute(
        state,
        section_id=section_id,
        component_config=component_config.to_dict()
    )
    
    if result.success and persister:
        partition_key = f"user:{user_id}" if user_id else None
        await persister.save(SITE_ID, new_state, partition_key="draft")
    
    # Reload component list
    return RedirectResponse(url=f"/admin/site/components/section?section_id={section_id}")


@router_admin_sites.post("/admin/site/components/toggle")
@require_admin
async def toggle_component(request, section_id: str, component_id: str):
    """Toggle component enabled state."""
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    site_result = await workflow_manager.load_site(SITE_ID, user_id, partition_key="draft")
    from core.state.state import State
    state = State(site_result["state"])
    
    action = ToggleComponentAction()
    new_state, result = await action.execute(
        state,
        section_id=section_id,
        component_id=component_id
    )
    
    if result.success and persister:
        partition_key = f"user:{user_id}" if user_id else None
        await persister.save(SITE_ID, new_state, partition_key="draft")
    
    return RedirectResponse(url=f"/admin/site/components/section?section_id={section_id}")


# ============================================================================
# Theme Editor Routes
# ============================================================================

@router_admin_sites.get("/admin/site/theme")
@require_admin
async def theme_editor(request):
    """Theme editor interface."""
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    # Initialize the landing page
    landing_page = HomePage(SITE_ID)
    
    # Load site state if available
    try:
        site_result = await workflow_manager.load_site(SITE_ID, user_id, partition_key="draft")
        if site_result["success"]:
            state = site_result["state"]
            landing_page.from_dict(state)
    except Exception as e:
        logger.warning(f"Could not load site state for theme editor: {e}")
        # Use default theme
        pass
    
    current_theme = landing_page.theme_styles
    
    return Card(
        Div(
            H2("Theme Editor", cls="text-2xl font-bold mb-6"),
            
            # Theme presets
            Div(
                H3("Theme Presets", cls="text-lg font-bold mb-4"),
                Div(
                    *[
                        Card(
                            Div(
                                H4(preset_name.title(), cls="font-bold mb-2"),
                                ButtonPrimary(
                                    "Apply",
                                    hx_post="/admin/site/theme/preset",
                                    hx_vals=f'{{"preset": "{preset_name}"}}',
                                    hx_target="#theme-editor",
                                    cls="btn-sm"
                                ),
                                cls="p-3"
                            ),
                            cls="mb-2"
                        )
                        for preset_name in ["default", "dark", "blue", "green"]
                    ],
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6"
                )
            ),
            
            # Color customization
            Div(
                H3("Colors", cls="text-lg font-bold mb-4"),
                Div(
                    *[
                        Div(
                            Label(color_name.title().replace("_", " "), cls="block text-sm font-bold mb-1"),
                            Input(
                                type="color",
                                value=current_theme.colors.get(color_name, "#000000"),
                                name=f"color_{color_name}",
                                hx_post="/admin/site/theme/colors",
                                hx_target="#theme-editor",
                                hx_vals=f'{{"color": "{color_name}"}}',
                                cls="w-full"
                            ),
                            cls="mb-3"
                        )
                        for color_name in ["primary", "secondary", "accent", "background", "text"]
                    ],
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
                ),
                cls="mb-6"
            ),
            
            # Typography
            Div(
                H3("Typography", cls="text-lg font-bold mb-4"),
                Div(
                    *[
                        Div(
                            Label(typo_name.title().replace("_", " "), cls="block text-sm font-bold mb-1"),
                            Select(
                                *[Option(size, value=size, selected=current_theme.typography.get(typo_name) == size) 
                                  for size in ["xs", "sm", "base", "lg", "xl", "2xl", "3xl"]],
                                name=f"typo_{typo_name}",
                                hx_post="/admin/site/theme/typography",
                                hx_target="#theme-editor",
                                hx_vals=f'{{"typo": "{typo_name}"}}',
                                cls="w-full"
                            ),
                            cls="mb-3"
                        )
                        for typo_name in ["heading_size", "body_size", "button_size"]
                    ],
                    cls="grid grid-cols-1 md:grid-cols-3 gap-4"
                ),
                cls="mb-6"
            ),
            
            # Custom CSS
            Div(
                H3("Custom CSS", cls="text-lg font-bold mb-4"),
                Textarea(
                    current_theme.custom_css or "",
                    name="custom_css",
                    placeholder="Add custom CSS here...",
                    hx_post="/admin/site/theme/css",
                    hx_target="#theme-editor",
                    cls="w-full h-32 font-mono text-sm"
                ),
                cls="mb-6"
            ),
            
            # Preview button
            Div(
                ButtonSecondary(
                    "Preview Changes",
                    hx_get="/admin/site/preview",
                    hx_target="#site-content",
                    cls="mr-2"
                ),
                ButtonPrimary(
                    "Save Theme",
                    hx_post="/admin/site/theme/save",
                    hx_target="#theme-editor",
                    cls="mr-2"
                ),
                ButtonSecondary(
                    "Reset to Default",
                    hx_post="/admin/site/theme/reset",
                    hx_target="#theme-editor",
                    hx_confirm="Reset theme to default?"
                ),
                cls="flex gap-2"
            ),
            
            cls="p-6"
        ),
        id="theme-editor"
    )
    
@router_admin_sites.post("/admin/site/theme/save")
@require_admin
async def save_theme(request):
    """Save theme changes."""
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    # Initialize the landing page
    landing_page = HomePage(SITE_ID)
    
    # Load current state
    try:
        site_result = await workflow_manager.load_site(SITE_ID, user_id, partition_key="draft")
        if site_result["success"]:
            state = site_result["state"]
            landing_page.from_dict(state)
    except Exception as e:
        logger.warning(f"Could not load site state for theme save: {e}")
    
    # Save the updated state
    try:
        updated_data = landing_page.to_dict()
        result = await workflow_manager.save_site(
            SITE_ID, 
            user_id, 
            updated_data, 
            partition_key="draft"
        )
        
        if result["success"]:
            landing_page.mark_clean()
            return Alert("Theme saved successfully!", cls="alert-success")
        else:
            return Alert(f"Error saving theme: {result.get('error')}", cls="alert-error")
    except Exception as e:
        logger.error(f"Error saving theme: {e}")
        return Alert("Failed to save theme", cls="alert-error")


@router_admin_sites.post("/admin/site/theme/colors")
@require_admin
async def update_theme_colors(request):
    """Update theme colors."""
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    # Get form data
    form_data = await request.form()
    color_name = form_data.get("color")
    color_value = form_data.get(f"color_{color_name}")
    
    if not color_name or not color_value:
        return Alert("Invalid color data", cls="alert-error")
    
    # Initialize the landing page
    landing_page = HomePage(SITE_ID)
    
    # Load current state
    try:
        site_result = await workflow_manager.load_site(SITE_ID, user_id, partition_key="draft")
        if site_result["success"]:
            state = site_result["state"]
            landing_page.from_dict(state)
    except Exception as e:
        logger.warning(f"Could not load site state for color update: {e}")
    
    # Update color
    landing_page.theme_styles.colors[color_name] = color_value
    
    # Save the updated state
    try:
        updated_data = landing_page.to_dict()
        result = await workflow_manager.save_site(
            SITE_ID, 
            user_id, 
            updated_data, 
            partition_key="draft"
        )
        
        if result["success"]:
            return Alert(f"Color '{color_name}' updated successfully!", cls="alert-success")
        else:
            return Alert(f"Error updating color: {result.get('error')}", cls="alert-error")
    except Exception as e:
        logger.error(f"Error updating color: {e}")
        return Alert("Failed to update color", cls="alert-error")


@router_admin_sites.post("/admin/site/theme/css")
@require_admin
async def update_custom_css(request):
    """Update custom CSS."""
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    # Get form data
    form_data = await request.form()
    custom_css = form_data.get("custom_css", "")
    
    # Initialize the landing page
    landing_page = HomePage(SITE_ID)
    
    # Load current state
    try:
        site_result = await workflow_manager.load_site(SITE_ID, user_id, partition_key="draft")
        if site_result["success"]:
            state = site_result["state"]
            landing_page.from_dict(state)
    except Exception as e:
        logger.warning(f"Could not load site state for CSS update: {e}")
    
    # Update custom CSS
    landing_page.theme_styles.custom_css = custom_css
    
    # Save the updated state
    try:
        updated_data = landing_page.to_dict()
        result = await workflow_manager.save_site(
            SITE_ID, 
            user_id, 
            updated_data, 
            partition_key="draft"
        )
        
        if result["success"]:
            return Alert("Custom CSS updated successfully!", cls="alert-success")
        else:
            return Alert(f"Error updating CSS: {result.get('error')}", cls="alert-error")
    except Exception as e:
        logger.error(f"Error updating CSS: {e}")
        return Alert("Failed to update CSS", cls="alert-error")


@router_admin_sites.post("/admin/site/theme/reset")
@require_admin
async def reset_theme(request):
    """Reset theme to default."""
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    # Initialize the landing page
    landing_page = HomePage(SITE_ID)
    
    # Reset theme styles to default
    landing_page.theme_styles = ThemeStyles()
    
    # Save the updated state
    try:
        updated_data = landing_page.to_dict()
        result = await workflow_manager.save_site(
            SITE_ID, 
            user_id, 
            updated_data, 
            partition_key="draft"
        )
        
        if result["success"]:
            return Alert("Theme reset to default!", cls="alert-success")
        else:
            return Alert(f"Error resetting theme: {result.get('error')}", cls="alert-error")
    except Exception as e:
        logger.error(f"Error resetting theme: {e}")
        return Alert("Failed to reset theme", cls="alert-error")


@router_admin_sites.post("/admin/site/theme/preset")
@require_admin
async def apply_theme_preset(request):
    """Apply a theme preset."""
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    # Get form data
    form_data = await request.form()
    preset_name = form_data.get("preset")
    
    if not preset_name:
        return Alert("Invalid preset", cls="alert-error")
    
    # Initialize the landing page
    landing_page = HomePage(SITE_ID)
    
    # Define presets
    presets = {
        "default": {
            "colors": {"primary": "#3b82f6", "secondary": "#64748b", "accent": "#f59e0b", "background": "#ffffff", "text": "#1f2937"},
            "typography": {"heading_size": "2xl", "body_size": "base", "button_size": "sm"}
        },
        "dark": {
            "colors": {"primary": "#60a5fa", "secondary": "#94a3b8", "accent": "#fbbf24", "background": "#111827", "text": "#f9fafb"},
            "typography": {"heading_size": "2xl", "body_size": "base", "button_size": "sm"}
        },
        "blue": {
            "colors": {"primary": "#2563eb", "secondary": "#64748b", "accent": "#0ea5e9", "background": "#ffffff", "text": "#1e293b"},
            "typography": {"heading_size": "3xl", "body_size": "lg", "button_size": "base"}
        },
        "green": {
            "colors": {"primary": "#16a34a", "secondary": "#64748b", "accent": "#84cc16", "background": "#ffffff", "text": "#1f2937"},
            "typography": {"heading_size": "2xl", "body_size": "base", "button_size": "sm"}
        }
    }
    
    if preset_name not in presets:
        return Alert("Preset not found", cls="alert-error")
    
    # Load current state
    try:
        site_result = await workflow_manager.load_site(SITE_ID, user_id, partition_key="draft")
        if site_result["success"]:
            state = site_result["state"]
            landing_page.from_dict(state)
    except Exception as e:
        logger.warning(f"Could not load site state for preset: {e}")
    
    # Apply preset
    preset_data = presets[preset_name]
    landing_page.theme_styles.colors.update(preset_data["colors"])
    landing_page.theme_styles.typography.update(preset_data["typography"])
    
    # Save the updated state
    try:
        updated_data = landing_page.to_dict()
        result = await workflow_manager.save_site(
            SITE_ID, 
            user_id, 
            updated_data, 
            partition_key="draft"
        )
        
        if result["success"]:
            return Alert(f"Theme preset '{preset_name}' applied successfully!", cls="alert-success")
        else:
            return Alert(f"Error applying preset: {result.get('error')}", cls="alert-error")
    except Exception as e:
        logger.error(f"Error applying preset: {e}")
        return Alert("Failed to apply preset", cls="alert-error")
                    

@router_admin_sites.post("/admin/site/theme/preset")
@require_admin
async def apply_theme_preset(request, preset: str):
    """Apply a theme preset."""
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    result = await theme_manager.apply_preset(SITE_ID, preset, user_id=user_id, partition_key="draft")
    
    if result["success"]:
        return RedirectResponse(url="/admin/site/theme")
    
    return Alert(f"Error: {result.get('error')}", cls="alert-error")


@router_admin_sites.post("/admin/site/theme/colors")
@require_admin
async def update_theme_colors(request, **colors):
    """Update theme colors."""
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    result = await theme_manager.update_theme_colors(SITE_ID, colors, user_id, partition_key="draft")
    
    if result["success"]:
        return RedirectResponse(url="/admin/site/theme")
    
    return Alert(f"Error: {result.get('error')}", cls="alert-error")


# ============================================================================
# Preview and Publishing Routes
# ============================================================================

@router_admin_sites.get("/admin/site/preview")
@require_admin
async def preview_site(request):
    """Preview the site with current changes."""
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    # Initialize the landing page
    landing_page = HomePage(SITE_ID)
    
    # Load site state if available
    try:
        site_result = await workflow_manager.load_site(SITE_ID, user_id, partition_key="draft")
        if site_result["success"]:
            state = site_result["state"]
            landing_page.from_dict(state)
    except Exception as e:
        logger.warning(f"Could not load site state for preview: {e}")
        # Use default sections
        pass
    # Render the page in preview mode
    layout = landing_page.render(request=request, preview_mode=True)
    
    return Div(
        Div(
            H3("Preview Mode", cls="text-sm font-bold text-yellow-600 mb-2"),
            P("This is a preview of your site with current changes", cls="text-xs text-gray-600 mb-4"),
        A("Close Preview", href="/admin/site", cls="btn btn-sm btn-outline"),
        cls="bg-yellow-50 border border-yellow-200 rounded p-3 mb-4"
    ),
    layout.content,
    cls="preview-container"
)


@router_admin_sites.post("/admin/site/publish")
@require_admin
async def publish_draft_version(request):
    """Publish the current draft version."""
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    # Initialize the landing page
    landing_page = HomePage(SITE_ID)
    
    # Load current draft state
    try:
        site_result = await workflow_manager.load_site(SITE_ID, user_id, partition_key="draft")
        if site_result["success"]:
            state = site_result["state"]
            landing_page.from_dict(state)
    except Exception as e:
        logger.warning(f"Could not load site state for publishing: {e}")
        return Alert("Could not load site state for publishing", cls="alert-error")
    
    # Save to published partition
    try:
        published_data = landing_page.to_dict()
        result = await workflow_manager.save_site(
            SITE_ID, 
            user_id, 
            published_data, 
            partition_key="published"
        )
        
        if result["success"]:
            landing_page.mark_clean()
            return Alert("Site published successfully!", cls="alert-success")
        else:
            return Alert(f"Error publishing site: {result.get('error')}", cls="alert-error")
    except Exception as e:
        logger.error(f"Error publishing site: {e}")
        return Alert("Failed to publish site", cls="alert-error")
    
    if result["success"]:
        return Div(
            Alert(
                f"✓ Published version {result['version_number']}!",
                cls="alert-success mb-4"
            ),
            ButtonSecondary(
                "Back to Dashboard",
                hx_get="/admin/dashboard",
                hx_target="body"
            )
        )
    
    return Alert(f"Error: {result.get('error')}", cls="alert-error")


@router_admin_sites.get("/admin/site/compare")
@require_admin
async def compare_versions(request):
    """Compare draft and published versions."""
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    result = await preview_manager.compare_versions(SITE_ID, user_id)
    
    if not result["success"]:
        return Alert(f"Error: {result.get('error')}", cls="alert-error")
    
    comparison = result["comparison"]
    
    return Card(
        Div(
            H2("Version Comparison", cls="text-2xl font-bold mb-6"),
            
            Alert(
                "Changes detected!" if comparison["has_changes"] else "No changes",
                cls="alert-info mb-4" if comparison["has_changes"] else "alert-success mb-4"
            ),
            
            # Section changes
            Div(
                H3("Section Changes", cls="text-lg font-bold mb-2"),
                
                Div(
                    H4("Added Sections", cls="font-bold mb-1"),
                    Ul(
                        *[Li(section_id, cls="text-green-600") for section_id in comparison["sections"]["added"]],
                        cls="list-disc list-inside ml-4 mb-2"
                    ) if comparison["sections"]["added"] else P("None", cls="text-gray-600 ml-4 mb-2")
                ),
                
                Div(
                    H4("Removed Sections", cls="font-bold mb-1"),
                    Ul(
                        *[Li(section_id, cls="text-red-600") for section_id in comparison["sections"]["removed"]],
                        cls="list-disc list-inside ml-4 mb-2"
                    ) if comparison["sections"]["removed"] else P("None", cls="text-gray-600 ml-4 mb-2")
                ),
                
                cls="mb-6"
            ),
            
            # Theme changes
            Div(
                H3("Theme Changes", cls="text-lg font-bold mb-2"),
                P("Theme modified" if comparison["theme_changed"] else "No theme changes",
                  cls="text-orange-600" if comparison["theme_changed"] else "text-gray-600"),
                cls="mb-6"
            ),
            
            # Actions
            Div(
                ButtonPrimary(
                    "Publish Changes",
                    hx_post="/admin/site/publish",
                    hx_target="#site-content",
                    hx_confirm="Publish these changes?",
                    disabled=not comparison["has_changes"]
                ),
                ButtonSecondary(
                    "Back to Editor",
                    hx_get="/admin/site/edit",
                    hx_target="#site-content",
                    cls="ml-2"
                ),
                cls="flex gap-2"
            ),
            
            cls="p-4"
        )
    )


# Export router
__all__ = ["router_admin_sites"]