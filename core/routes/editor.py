"""Editor Routes - Single-site visual editor for draft version.

Architecture:
- Single site per installation
- Editor works on draft version
- Session-based editing with auto-save
"""

from fasthtml.common import *
from core.services.editor import OmniviewEditorService, get_editor_capabilities
from core.services.auth.decorators import require_permission
from core.state.persistence import get_persister

router_editor = APIRouter()
editor_service = OmniviewEditorService(persister=get_persister())

# Single site identifier
SITE_ID = "main"


@router_editor.get("/editor")
async def editor_page(request):
    """Main editor interface for single site."""
    user = request.state.user
    
    # Start editing session for draft version
    result = await editor_service.start_editing(SITE_ID, user["_id"], partition_key="draft")
    
    if not result["success"]:
        return Alert(f"Error: {result.get('error')}", cls="alert-error")
    
    # Get user capabilities
    capabilities = get_editor_capabilities(user.get("roles", []))
    
    return EditorLayout(
        site_id=SITE_ID,
        session_id=result["session_id"],
        site_state=result["site_state"],
        theme_state=result["theme_state"],
        component_templates=result["component_templates"],
        capabilities=capabilities
    )


@router_editor.post("/api/editor/sections/add")
async def add_section(request, session_id: str, section_id: str, section_type: str):
    """Add section to site"""
    result = await editor_service.add_section(
        session_id=session_id,
        section_id=section_id,
        section_type=section_type
    )
    return result


@router_editor.post("/api/editor/components/add")
async def add_component(
    request,
    session_id: str,
    section_id: str,
    component_template_id: str
):
    """Add component to section"""
    result = await editor_service.add_component(
        session_id=session_id,
        section_id=section_id,
        component_template_id=component_template_id
    )
    return result


@router_editor.put("/api/editor/components/update")
async def update_component(
    request,
    session_id: str,
    section_id: str,
    component_id: str,
    updates: Dict[str, Any]
):
    """Update component configuration"""
    result = await editor_service.update_component(
        session_id=session_id,
        section_id=section_id,
        component_id=component_id,
        updates=updates
    )
    return result


@router_editor.put("/api/editor/theme/colors")
async def update_theme_colors(request, session_id: str, colors: Dict[str, str]):
    """Update theme colors"""
    result = await editor_service.update_theme_colors(
        session_id=session_id,
        colors=colors
    )
    return result


@router_editor.get("/api/editor/preview/{user_type}")
async def preview_as_user(request, session_id: str, user_type: str):
    """Preview as different user type"""
    result = await editor_service.preview_as_user_type(
        session_id=session_id,
        user_type=user_type
    )
    return result


@router_editor.post("/api/editor/publish")
async def publish_site(request, session_id: str):
    """Publish current draft"""
    result = await editor_service.publish(session_id=session_id)
    return result