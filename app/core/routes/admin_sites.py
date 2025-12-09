"""
Admin routes for site management workflow.

Provides web interface for managing sites using the state machine workflow.
"""

from fasthtml.common import *
from monsterui.all import *
from core.services.admin.decorators import require_admin
from core.state.persistence import InMemoryPersister, MongoPersister
from core.workflows.admin import SiteWorkflowManager
from core.utils.logger import get_logger
import os

logger = get_logger(__name__)

# Initialize workflow manager
# Use MongoDB if available, otherwise in-memory
try:
    from core.services.base.mongo_service import get_db
    db = get_db()
    persister = MongoPersister(db, "site_states") if db else InMemoryPersister()
except:
    persister = InMemoryPersister()

workflow_manager = SiteWorkflowManager(persister=persister)

# Create router
router_admin_sites = Router()


# ============================================================================
# Site Management Dashboard
# ============================================================================

@router_admin_sites.get("/admin/sites")
@require_admin
async def admin_sites_dashboard(request):
    """Admin dashboard for site management."""
    
    # Get current user
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    # List user's sites
    sites_result = await workflow_manager.list_user_sites(user_id) if user_id else {"success": True, "sites": []}
    sites = sites_result.get("sites", [])
    
    return Card(
        Div(
            H1("Site Management", cls="text-3xl font-bold mb-6"),
            
            # Create new site button
            ButtonPrimary(
                "Create New Site",
                hx_get="/admin/sites/new",
                hx_target="#site-content",
                cls="mb-6"
            ),
            
            # Sites list
            Div(
                H2("Your Sites", cls="text-2xl font-bold mb-4"),
                
                Div(
                    *[
                        Card(
                            Div(
                                H3(site["site_name"], cls="text-xl font-bold"),
                                P(f"Status: {site['status']}", cls="text-sm text-gray-600"),
                                P(f"Sections: {site['section_count']}", cls="text-sm text-gray-600"),
                                P(f"Created: {site['created_at']}", cls="text-sm text-gray-600"),
                                
                                Div(
                                    ButtonSecondary(
                                        "Edit",
                                        hx_get=f"/admin/sites/{site['site_id']}/edit",
                                        hx_target="#site-content"
                                    ),
                                    ButtonSecondary(
                                        "View",
                                        hx_get=f"/admin/sites/{site['site_id']}/view",
                                        hx_target="#site-content"
                                    ),
                                    ButtonPrimary(
                                        "Publish" if site["status"] == "draft" else "Published",
                                        hx_post=f"/admin/sites/{site['site_id']}/publish",
                                        hx_target="#site-content",
                                        disabled=site["status"] == "published"
                                    ),
                                    cls="flex gap-2 mt-4"
                                ),
                                
                                cls="p-4"
                            ),
                            cls="mb-4"
                        )
                        for site in sites
                    ] if sites else [
                        P("No sites yet. Create your first site!", cls="text-gray-600")
                    ],
                    id="sites-list"
                )
            ),
            
            # Content area for forms/details
            Div(id="site-content", cls="mt-8"),
            
            cls="max-w-6xl mx-auto p-6"
        )
    )


# ============================================================================
# Create New Site
# ============================================================================

@router_admin_sites.get("/admin/sites/new")
@require_admin
async def new_site_form(request):
    """Form for creating a new site."""
    
    return Card(
        Form(
            H2("Create New Site", cls="text-2xl font-bold mb-4"),
            
            # Site name
            Div(
                Label("Site Name", cls="block text-sm font-bold mb-2"),
                Input(
                    type="text",
                    name="site_name",
                    placeholder="My Awesome Site",
                    required=True,
                    cls="w-full p-2 border rounded"
                ),
                cls="mb-4"
            ),
            
            # Theme selection
            Div(
                Label("Theme", cls="block text-sm font-bold mb-2"),
                Select(
                    Option("Slate", value="slate"),
                    Option("Light", value="light"),
                    Option("Dark", value="dark"),
                    Option("Cupcake", value="cupcake"),
                    name="theme",
                    cls="w-full p-2 border rounded"
                ),
                cls="mb-4"
            ),
            
            # Initial sections
            Div(
                H3("Initial Sections", cls="text-lg font-bold mb-2"),
                P("Add sections after creation", cls="text-sm text-gray-600 mb-2"),
                cls="mb-4"
            ),
            
            # Actions
            Div(
                ButtonPrimary(
                    "Create Site",
                    type="submit",
                    cls="mr-2"
                ),
                ButtonSecondary(
                    "Cancel",
                    hx_get="/admin/sites",
                    hx_target="#site-content"
                ),
                cls="flex gap-2"
            ),
            
            hx_post="/admin/sites/create",
            hx_target="#site-content",
            cls="p-4"
        )
    )


@router_admin_sites.post("/admin/sites/create")
@require_admin
async def create_site(request, site_name: str, theme: str = "slate"):
    """Create a new site."""
    
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    # Create site
    result = await workflow_manager.create_new_site(
        site_name=site_name,
        theme={"theme": theme},
        user_id=user_id
    )
    
    if result["success"]:
        site_id = result["site_id"]
        
        return Div(
            Alert(
                f"Site '{site_name}' created successfully!",
                cls="alert-success mb-4"
            ),
            ButtonPrimary(
                "Edit Site",
                hx_get=f"/admin/sites/{site_id}/edit",
                hx_target="#site-content"
            ),
            ButtonSecondary(
                "Back to Dashboard",
                hx_get="/admin/sites",
                hx_target="body",
                cls="ml-2"
            )
        )
    else:
        return Alert(
            f"Error creating site: {result.get('error')}",
            cls="alert-error"
        )


# ============================================================================
# Edit Site
# ============================================================================

@router_admin_sites.get("/admin/sites/{site_id}/edit")
@require_admin
async def edit_site(request, site_id: str):
    """Edit site configuration."""
    
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    # Load site
    site_result = await workflow_manager.load_site(site_id, user_id)
    
    if not site_result["success"]:
        return Alert(f"Error loading site: {site_result.get('error')}", cls="alert-error")
    
    state = site_result["state"]
    site_graph = state.get("site_graph", {})
    sections = site_graph.get("sections", [])
    theme_state = state.get("theme_state", {})
    
    return Card(
        Div(
            H2(f"Edit Site: {state.get('site_name')}", cls="text-2xl font-bold mb-6"),
            
            # Site status
            Alert(
                f"Status: {state.get('status', 'draft').upper()}",
                cls="mb-4"
            ),
            
            # Sections management
            Div(
                H3("Sections", cls="text-xl font-bold mb-4"),
                
                Div(
                    *[
                        Card(
                            Div(
                                Span(f"#{section['order'] + 1}", cls="font-bold mr-2"),
                                Span(section['id'], cls="text-lg"),
                                Span(f"({section['type']})", cls="text-sm text-gray-600 ml-2"),
                                
                                ButtonDanger(
                                    "Remove",
                                    hx_post=f"/admin/sites/{site_id}/sections/remove",
                                    hx_vals=f'{{"section_id": "{section["id"]}"}}',
                                    hx_target="#site-content",
                                    cls="ml-auto"
                                ),
                                
                                cls="flex items-center justify-between p-3"
                            ),
                            cls="mb-2"
                        )
                        for section in sections
                    ],
                    id="sections-list",
                    cls="mb-4"
                ),
                
                # Add section form
                Form(
                    H4("Add Section", cls="text-lg font-bold mb-2"),
                    
                    Div(
                        Input(
                            type="text",
                            name="section_id",
                            placeholder="section-id",
                            required=True,
                            cls="p-2 border rounded mr-2"
                        ),
                        Select(
                            Option("Hero", value="hero"),
                            Option("Features", value="features"),
                            Option("About", value="about"),
                            Option("Contact", value="contact"),
                            Option("Gallery", value="gallery"),
                            name="section_type",
                            cls="p-2 border rounded mr-2"
                        ),
                        ButtonPrimary("Add", type="submit"),
                        cls="flex items-center gap-2"
                    ),
                    
                    hx_post=f"/admin/sites/{site_id}/sections/add",
                    hx_target="#site-content",
                    cls="p-4 bg-gray-50 rounded"
                ),
                
                cls="mb-6"
            ),
            
            # Theme settings
            Div(
                H3("Theme", cls="text-xl font-bold mb-4"),
                
                Form(
                    Select(
                        Option("Slate", value="slate", selected=theme_state.get("theme") == "slate"),
                        Option("Light", value="light", selected=theme_state.get("theme") == "light"),
                        Option("Dark", value="dark", selected=theme_state.get("theme") == "dark"),
                        name="theme",
                        cls="p-2 border rounded mr-2"
                    ),
                    ButtonPrimary("Update Theme", type="submit"),
                    
                    hx_post=f"/admin/sites/{site_id}/theme/update",
                    hx_target="#site-content",
                    cls="flex items-center gap-2"
                ),
                
                cls="mb-6"
            ),
            
            # Actions
            Div(
                ButtonPrimary(
                    "Publish Site",
                    hx_post=f"/admin/sites/{site_id}/publish",
                    hx_target="#site-content",
                    cls="mr-2"
                ),
                ButtonSecondary(
                    "Back to Dashboard",
                    hx_get="/admin/sites",
                    hx_target="body"
                ),
                cls="flex gap-2"
            ),
            
            cls="p-4"
        )
    )


# ============================================================================
# Section Operations
# ============================================================================

@router_admin_sites.post("/admin/sites/{site_id}/sections/add")
@require_admin
async def add_section(request, site_id: str, section_id: str, section_type: str):
    """Add a section to the site."""
    
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    result = await workflow_manager.update_site_sections(
        site_id=site_id,
        operations=[
            {
                "action": "add",
                "data": {
                    "section_id": section_id,
                    "section_type": section_type
                }
            }
        ],
        user_id=user_id
    )
    
    if result["success"]:
        # Return to edit page
        return RedirectResponse(url=f"/admin/sites/{site_id}/edit")
    else:
        return Alert(f"Error adding section: {result.get('error')}", cls="alert-error")


@router_admin_sites.post("/admin/sites/{site_id}/sections/remove")
@require_admin
async def remove_section(request, site_id: str, section_id: str):
    """Remove a section from the site."""
    
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    result = await workflow_manager.update_site_sections(
        site_id=site_id,
        operations=[
            {
                "action": "remove",
                "data": {"section_id": section_id}
            }
        ],
        user_id=user_id
    )
    
    if result["success"]:
        return RedirectResponse(url=f"/admin/sites/{site_id}/edit")
    else:
        return Alert(f"Error removing section: {result.get('error')}", cls="alert-error")


# ============================================================================
# Theme Operations
# ============================================================================

@router_admin_sites.post("/admin/sites/{site_id}/theme/update")
@require_admin
async def update_theme(request, site_id: str, theme: str):
    """Update site theme."""
    
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    # Load and update
    site_result = await workflow_manager.load_site(site_id, user_id)
    if not site_result["success"]:
        return Alert(f"Error: {site_result.get('error')}", cls="alert-error")
    
    from core.state.state import State
    from core.state.actions import UpdateThemeAction
    
    state = State(site_result["state"])
    action = UpdateThemeAction()
    new_state, result = await action.execute(state, theme_updates={"theme": theme})
    
    # Save
    if persister:
        partition_key = f"user:{user_id}" if user_id else None
        await persister.save(site_id, new_state, partition_key)
    
    return RedirectResponse(url=f"/admin/sites/{site_id}/edit")


# ============================================================================
# Publish Operations
# ============================================================================

@router_admin_sites.post("/admin/sites/{site_id}/publish")
@require_admin
async def publish_site(request, site_id: str):
    """Publish a site."""
    
    user = request.state.user if hasattr(request.state, 'user') else None
    user_id = user.get("id") if user else None
    
    result = await workflow_manager.publish_site(site_id, user_id)
    
    if result["success"]:
        return Div(
            Alert(
                f"Site published successfully at {result.get('published_at')}!",
                cls="alert-success mb-4"
            ),
            ButtonSecondary(
                "Back to Dashboard",
                hx_get="/admin/sites",
                hx_target="body"
            )
        )
    else:
        validation_errors = result.get("validation_errors", [])
        return Div(
            Alert(
                f"Cannot publish site: {result.get('error')}",
                cls="alert-error mb-4"
            ),
            Ul(
                *[Li(error) for error in validation_errors],
                cls="list-disc list-inside mb-4"
            ) if validation_errors else None,
            ButtonSecondary(
                "Back to Edit",
                hx_get=f"/admin/sites/{site_id}/edit",
                hx_target="#site-content"
            )
        )


# Export router
__all__ = ["router_admin_sites"]