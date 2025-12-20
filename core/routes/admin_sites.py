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
    
    # Load draft theme
    theme_state = await persister.load(f"theme_{SITE_ID}", partition_key="draft")
    
    current_theme = theme_state.get("theme_state", {}) if theme_state else {}
    
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
                            cls="text-center"
                        )
                        for preset_name in ["modern", "minimal", "bold", "dark", "warm", "cool"]
                    ],
                    cls="grid grid-cols-3 md:grid-cols-6 gap-4 mb-6"
                )
            ),
            
            # Color scheme editor
            Div(
                H3("Colors", cls="text-lg font-bold mb-4"),
                Form(
                    Div(
                        *[
                            Div(
                                Label(color_name.replace("_", " ").title(), cls="block text-sm font-bold mb-1"),
                                Input(
                                    type="color",
                                    name=color_name,
                                    value=current_theme.get("colors", {}).get(color_name, "#000000"),
                                    cls="w-full h-10"
                                ),
                                cls="mb-2"
                            )
                            for color_name in ["primary", "secondary", "accent", "neutral"]
                        ],
                        cls="grid grid-cols-2 md:grid-cols-4 gap-4"
                    ),
                    ButtonPrimary("Update Colors", type="submit", cls="mt-4"),
                    hx_post="/admin/site/theme/colors",
                    hx_target="#theme-editor"
                ),
                cls="mb-6"
            ),
            
            # Typography editor
            Div(
                H3("Typography", cls="text-lg font-bold mb-4"),
                Form(
                    Div(
                        Label("Primary Font", cls="block text-sm font-bold mb-1"),
                        Input(
                            type="text",
                            name="font_family_primary",
                            value=current_theme.get("typography", {}).get("font_family_primary", "Inter, sans-serif"),
                            placeholder="Inter, sans-serif",
                            cls="input input-bordered w-full mb-2"
                        )
                    ),
                    Div(
                        Label("Base Font Size", cls="block text-sm font-bold mb-1"),
                        Input(
                            type="text",
                            name="font_size_base",
                            value=current_theme.get("typography", {}).get("font_size_base", "16px"),
                            placeholder="16px",
                            cls="input input-bordered w-full mb-2"
                        )
                    ),
                    ButtonPrimary("Update Typography", type="submit", cls="mt-4"),
                    hx_post="/admin/site/theme/typography",
                    hx_target="#theme-editor"
                ),
                cls="mb-6"
            ),
            
            # Custom CSS editor
            Div(
                H3("Custom CSS", cls="text-lg font-bold mb-4"),
                Form(
                    Textarea(
                        current_theme.get("custom_css", ""),
                        name="custom_css",
                        rows=10,
                        placeholder="/* Add your custom CSS here */",
                        cls="textarea textarea-bordered w-full font-mono text-sm"
                    ),
                    ButtonPrimary("Update CSS", type="submit", cls="mt-4"),
                    hx_post="/admin/site/theme/css",
                    hx_target="#theme-editor"
                ),
                cls="mb-6"
            ),
            
            # Preview & Actions
            Div(
                ButtonPrimary(
                    "Preview Theme",
                    hx_get="/admin/site/preview",
                    hx_target="#preview-window",
                    cls="mr-2"
                ),
                ButtonSecondary(
                    "Back to Site Editor",
                    hx_get="/admin/site/edit",
                    hx_target="#site-content"
                ),
                cls="flex gap-2"
            ),
            
            Div(id="preview-window", cls="mt-6"),
            
            cls="p-4",
            id="theme-editor"
        )
    )


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
    """Preview site from draft version."""
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    # Generate preview
    result = await preview_manager.generate_preview(SITE_ID, user_context=user, user_id=user_id)
    
    if not result["success"]:
        return Alert(f"Error: {result.get('error')}", cls="alert-error")
    
    preview_data = result["preview_data"]
    
    return Card(
        Div(
            Div(
                H2("Site Preview", cls="text-2xl font-bold"),
                Badge("Preview Mode", cls="badge-warning"),
                cls="flex items-center justify-between mb-4"
            ),
            
            # Preview iframe or content
            Div(
                H3(preview_data.get("site_name"), cls="text-3xl font-bold mb-4"),
                
                *[
                    Div(
                        H4(f"Section: {section['id']}", cls="text-xl font-bold mb-2"),
                        Badge(f"Type: {section['type']}", cls="badge-primary mb-2"),
                        
                        P(f"{len(section['components'])} components", cls="text-sm text-gray-600"),
                        
                        # Show which components are visible
                        Ul(
                            *[
                                Li(f"✓ {comp['name']}", cls="text-sm")
                                for comp in section['components']
                            ],
                            cls="list-disc list-inside ml-4"
                        ) if section['components'] else P("No visible components", cls="text-sm text-gray-600"),
                        
                        cls="p-4 border rounded mb-4"
                    )
                    for section in preview_data.get("sections", [])
                ],
                
                cls="bg-white p-6 rounded shadow"
            ),
            
            # Actions
            Div(
                ButtonPrimary(
                    "Publish This Version",
                    hx_post="/admin/site/publish",
                    hx_target="#site-content",
                    hx_confirm="Publish this version?",
                    cls="mr-2"
                ),
                ButtonSecondary(
                    "Compare with Published",
                    hx_get="/admin/site/compare",
                    hx_target="#site-content"
                ),
                ButtonSecondary(
                    "Back to Editor",
                    hx_get="/admin/site/edit",
                    hx_target="#site-content",
                    cls="ml-2"
                ),
                cls="flex gap-2 mt-6"
            ),
            
            cls="p-4"
        )
    )


@router_admin_sites.post("/admin/site/publish")
@require_admin
async def publish_draft_version(request):
    """Publish the current draft version."""
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    result = await preview_manager.publish_draft(SITE_ID, user_id)
    
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