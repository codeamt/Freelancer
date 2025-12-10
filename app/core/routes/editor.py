from fasthtml.common import *
from core.services.editor import OmniviewEditorService, get_editor_capabilities
from core.services.auth.decorators import require_permission
from core.state.persistence import get_persister

router_editor = Router()
editor_service = OmniviewEditorService(persister=get_persister())


@router_editor.get("/editor/{site_id}")
@require_permission("site", "update")
async def editor_page(request, site_id: str):
    """Main editor interface"""
    user = request.state.user
    
    # Start editing session
    result = await editor_service.start_editing(site_id, user["_id"])
    
    if not result["success"]:
        return Alert(f"Error: {result.get('error')}", cls="alert-error")
    
    # Get user capabilities
    capabilities = get_editor_capabilities(user.get("roles", []))
    
    return EditorLayout(
        site_id=site_id,
        session_id=result["session_id"],
        site_state=result["site_state"],
        theme_state=result["theme_state"],
        component_templates=result["component_templates"],
        capabilities=capabilities
    )


@router.post("/api/editor/sections/add")
async def add_section(request, session_id: str, section_id: str, section_type: str):
    """Add section to site"""
    result = await editor_service.add_section(
        session_id=session_id,
        section_id=section_id,
        section_type=section_type
    )
    return result


@router.post("/api/editor/components/add")
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


@router.put("/api/editor/components/update")
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


@router.put("/api/editor/theme/colors")
async def update_theme_colors(request, session_id: str, colors: Dict[str, str]):
    """Update theme colors"""
    result = await editor_service.update_theme_colors(
        session_id=session_id,
        colors=colors
    )
    return result


@router.get("/api/editor/preview/{user_type}")
async def preview_as_user(request, session_id: str, user_type: str):
    """Preview as different user type"""
    result = await editor_service.preview_as_user_type(
        session_id=session_id,
        user_type=user_type
    )
    return result


@router.post("/api/editor/publish")
async def publish_site(request, session_id: str):
    """Publish current draft"""
    result = await editor_service.publish(session_id=session_id)
    return result