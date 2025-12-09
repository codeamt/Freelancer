"""
Site preview and publishing system.

Provides:
- Draft vs Published state management
- Preview generation from draft state
- Publishing workflow with version control
- Rollback capabilities
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from core.state.actions import Action, ActionResult
from core.state.state import State
from core.state.transitions import condition
from core.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# State Types
# ============================================================================

class SiteVersion:
    """Represents a version of the site."""
    
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# ============================================================================
# Version Management Actions
# ============================================================================

class CreateDraftFromPublishedAction(Action):
    """Create a draft copy from published version."""
    
    def __init__(self):
        super().__init__(
            name="create_draft_from_published",
            reads=["site_id", "published_version"],
            writes=["draft_version", "version_history"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Create draft from current published version."""
        published = state.get("published_version")
        
        if not published:
            return ActionResult(
                success=False,
                error="No published version to copy from"
            )
        
        # Create draft copy
        draft = {
            **published,
            "version_type": SiteVersion.DRAFT,
            "created_at": datetime.utcnow().isoformat(),
            "based_on_version": published.get("version_number", 0)
        }
        
        # Add to history
        history = state.get("version_history", [])
        history.append({
            "action": "draft_created",
            "timestamp": datetime.utcnow().isoformat(),
            "based_on": published.get("version_number", 0)
        })
        
        return ActionResult(
            success=True,
            message="Draft created from published version",
            data={
                "draft_version": draft,
                "version_history": history
            }
        )


class PublishDraftAction(Action):
    """Publish draft version (replaces published)."""
    
    def __init__(self):
        super().__init__(
            name="publish_draft",
            reads=["draft_version", "published_version"],
            writes=["published_version", "version_history", "publish_log"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Publish the draft version."""
        draft = state.get("draft_version")
        
        if not draft:
            return ActionResult(
                success=False,
                error="No draft version to publish"
            )
        
        # Archive current published version
        current_published = state.get("published_version")
        publish_log = state.get("publish_log", [])
        
        if current_published:
            publish_log.append({
                "version_number": current_published.get("version_number", 0),
                "archived_at": datetime.utcnow().isoformat(),
                "site_graph": current_published.get("site_graph"),
                "theme_state": current_published.get("theme_state")
            })
        
        # Increment version number
        new_version_number = (current_published.get("version_number", 0) if current_published else 0) + 1
        
        # Create new published version from draft
        published = {
            **draft,
            "version_type": SiteVersion.PUBLISHED,
            "version_number": new_version_number,
            "published_at": datetime.utcnow().isoformat(),
            "published_by": inputs.get("user_id")
        }
        
        # Update history
        history = state.get("version_history", [])
        history.append({
            "action": "published",
            "version_number": new_version_number,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": inputs.get("user_id")
        })
        
        return ActionResult(
            success=True,
            message=f"Published version {new_version_number}",
            data={
                "published_version": published,
                "version_history": history,
                "publish_log": publish_log
            }
        )


class RollbackToVersionAction(Action):
    """Rollback to a previous published version."""
    
    def __init__(self):
        super().__init__(
            name="rollback_to_version",
            reads=["publish_log"],
            writes=["published_version", "draft_version", "version_history"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Rollback to a specific version."""
        target_version = inputs.get("version_number")
        
        if target_version is None:
            return ActionResult(success=False, error="version_number required")
        
        publish_log = state.get("publish_log", [])
        
        # Find target version in log
        target_data = None
        for entry in publish_log:
            if entry["version_number"] == target_version:
                target_data = entry
                break
        
        if not target_data:
            return ActionResult(
                success=False,
                error=f"Version {target_version} not found in history"
            )
        
        # Create new published version from archived data
        published = {
            "site_graph": target_data["site_graph"],
            "theme_state": target_data["theme_state"],
            "version_type": SiteVersion.PUBLISHED,
            "version_number": state.get("published_version", {}).get("version_number", 0) + 1,
            "published_at": datetime.utcnow().isoformat(),
            "rolled_back_from": target_version
        }
        
        # Also update draft to match
        draft = {
            **published,
            "version_type": SiteVersion.DRAFT
        }
        
        # Update history
        history = state.get("version_history", [])
        history.append({
            "action": "rollback",
            "target_version": target_version,
            "new_version": published["version_number"],
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return ActionResult(
            success=True,
            message=f"Rolled back to version {target_version}",
            data={
                "published_version": published,
                "draft_version": draft,
                "version_history": history
            }
        )


class CompareDraftToPublishedAction(Action):
    """Compare draft version to published version."""
    
    def __init__(self):
        super().__init__(
            name="compare_versions",
            reads=["draft_version", "published_version"],
            writes=["comparison_result"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Compare draft and published versions."""
        draft = state.get("draft_version")
        published = state.get("published_version")
        
        if not draft or not published:
            return ActionResult(
                success=False,
                error="Both draft and published versions required"
            )
        
        # Compare sections
        draft_sections = set(s["id"] for s in draft.get("site_graph", {}).get("sections", []))
        published_sections = set(s["id"] for s in published.get("site_graph", {}).get("sections", []))
        
        added_sections = draft_sections - published_sections
        removed_sections = published_sections - draft_sections
        
        # Compare theme
        draft_theme = draft.get("theme_state", {}).get("name", "")
        published_theme = published.get("theme_state", {}).get("name", "")
        theme_changed = draft_theme != published_theme
        
        # Build comparison
        comparison = {
            "has_changes": len(added_sections) > 0 or len(removed_sections) > 0 or theme_changed,
            "sections": {
                "added": list(added_sections),
                "removed": list(removed_sections),
                "unchanged": list(draft_sections & published_sections)
            },
            "theme_changed": theme_changed,
            "draft_version_number": draft.get("based_on_version", 0),
            "published_version_number": published.get("version_number", 0)
        }
        
        return ActionResult(
            success=True,
            message="Comparison complete",
            data={"comparison_result": comparison}
        )


# ============================================================================
# Preview Generation
# ============================================================================

class GeneratePreviewAction(Action):
    """Generate preview HTML from draft state."""
    
    def __init__(self):
        super().__init__(
            name="generate_preview",
            reads=["draft_version"],
            writes=["preview_data"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Generate preview data."""
        draft = state.get("draft_version")
        
        if not draft:
            return ActionResult(success=False, error="No draft to preview")
        
        user_context = inputs.get("user_context")  # Current user for conditional rendering
        
        # Extract components
        site_graph = draft.get("site_graph", {})
        sections = site_graph.get("sections", [])
        theme_state = draft.get("theme_state", {})
        
        # Build preview data
        preview = {
            "site_name": draft.get("site_name", "Preview"),
            "sections": [],
            "theme": theme_state,
            "preview_mode": True,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Process each section for preview
        for section in sections:
            section_preview = {
                "id": section["id"],
                "type": section["type"],
                "order": section["order"],
                "components": []
            }
            
            # Filter components based on user context
            for component in section.get("components", []):
                # Check if component should be visible
                if self._should_render_component(component, user_context):
                    section_preview["components"].append(component)
            
            preview["sections"].append(section_preview)
        
        return ActionResult(
            success=True,
            message="Preview generated",
            data={"preview_data": preview}
        )
    
    def _should_render_component(
        self,
        component: Dict[str, Any],
        user_context: Optional[Dict[str, Any]]
    ) -> bool:
        """Check if component should be rendered for user."""
        if not component.get("enabled", True):
            return False
        
        visibility = component.get("visibility", "always")
        
        if visibility == "always":
            return True
        
        if visibility == "authenticated":
            return user_context is not None
        
        if visibility == "not_authenticated":
            return user_context is None
        
        if visibility == "is_member":
            if not user_context:
                return False
            site_id = component.get("visibility_params", {}).get("site_id")
            return site_id in user_context.get("member_sites", [])
        
        if visibility == "not_member":
            if not user_context:
                return True
            site_id = component.get("visibility_params", {}).get("site_id")
            return site_id not in user_context.get("member_sites", [])
        
        return True


# ============================================================================
# Preview and Publishing Manager
# ============================================================================

class PreviewPublishManager:
    """Manager for preview and publishing operations."""
    
    def __init__(self, persister=None):
        """Initialize manager."""
        self.persister = persister
    
    async def load_site_versions(
        self,
        site_id: str,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Load both draft and published versions.
        
        Returns:
            Dictionary with draft_version and published_version
        """
        if not self.persister:
            return {"success": False, "error": "No persister configured"}
        
        partition_key = f"user:{user_id}" if user_id else None
        
        # Load main state (contains both versions)
        state = await self.persister.load(site_id, partition_key)
        
        if not state:
            return {"success": False, "error": "Site not found"}
        
        return {
            "success": True,
            "draft_version": state.get("draft_version"),
            "published_version": state.get("published_version"),
            "version_history": state.get("version_history", [])
        }
    
    async def generate_preview(
        self,
        site_id: str,
        user_context: Optional[Dict[str, Any]] = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Generate preview from draft version.
        
        Args:
            site_id: Site identifier
            user_context: Current user context for conditional rendering
            user_id: Site owner user ID
            
        Returns:
            Dictionary with preview data
        """
        # Load versions
        versions = await self.load_site_versions(site_id, user_id)
        
        if not versions["success"]:
            return versions
        
        # Get draft
        draft = versions.get("draft_version")
        
        if not draft:
            # If no draft, use published as draft
            draft = versions.get("published_version")
        
        if not draft:
            return {"success": False, "error": "No content to preview"}
        
        # Create state with draft
        state = State({"draft_version": draft})
        
        # Generate preview
        action = GeneratePreviewAction()
        new_state, result = await action.execute(state, user_context=user_context)
        
        if result.success:
            return {
                "success": True,
                "preview_data": new_state.get("preview_data")
            }
        
        return {"success": False, "error": result.error}
    
    async def publish_draft(
        self,
        site_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Publish current draft version.
        
        Args:
            site_id: Site identifier
            user_id: User publishing the site
            
        Returns:
            Result of publishing operation
        """
        # Load current state
        partition_key = f"user:{user_id}"
        state = await self.persister.load(site_id, partition_key)
        
        if not state:
            return {"success": False, "error": "Site not found"}
        
        # Validate draft exists
        if not state.get("draft_version"):
            return {"success": False, "error": "No draft to publish"}
        
        # Publish
        action = PublishDraftAction()
        new_state, result = await action.execute(state, user_id=user_id)
        
        if result.success:
            # Save updated state
            await self.persister.save(site_id, new_state, partition_key)
            
            return {
                "success": True,
                "version_number": new_state.get("published_version", {}).get("version_number"),
                "published_at": new_state.get("published_version", {}).get("published_at")
            }
        
        return {"success": False, "error": result.error}
    
    async def create_draft_from_published(
        self,
        site_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Create a new draft from current published version.
        
        Args:
            site_id: Site identifier
            user_id: User creating the draft
            
        Returns:
            Result of draft creation
        """
        partition_key = f"user:{user_id}"
        state = await self.persister.load(site_id, partition_key)
        
        if not state:
            return {"success": False, "error": "Site not found"}
        
        action = CreateDraftFromPublishedAction()
        new_state, result = await action.execute(state)
        
        if result.success:
            await self.persister.save(site_id, new_state, partition_key)
            
            return {
                "success": True,
                "draft_version": new_state.get("draft_version")
            }
        
        return {"success": False, "error": result.error}
    
    async def compare_versions(
        self,
        site_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Compare draft and published versions.
        
        Args:
            site_id: Site identifier
            user_id: Site owner user ID
            
        Returns:
            Comparison result
        """
        partition_key = f"user:{user_id}"
        state = await self.persister.load(site_id, partition_key)
        
        if not state:
            return {"success": False, "error": "Site not found"}
        
        action = CompareDraftToPublishedAction()
        new_state, result = await action.execute(state)
        
        if result.success:
            return {
                "success": True,
                "comparison": new_state.get("comparison_result")
            }
        
        return {"success": False, "error": result.error}
    
    async def rollback_to_version(
        self,
        site_id: str,
        version_number: int,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Rollback to a previous version.
        
        Args:
            site_id: Site identifier
            version_number: Version to rollback to
            user_id: User performing rollback
            
        Returns:
            Result of rollback operation
        """
        partition_key = f"user:{user_id}"
        state = await self.persister.load(site_id, partition_key)
        
        if not state:
            return {"success": False, "error": "Site not found"}
        
        action = RollbackToVersionAction()
        new_state, result = await action.execute(state, version_number=version_number)
        
        if result.success:
            await self.persister.save(site_id, new_state, partition_key)
            
            return {
                "success": True,
                "new_version_number": new_state.get("published_version", {}).get("version_number")
            }
        
        return {"success": False, "error": result.error}
    
    async def get_version_history(
        self,
        site_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get version history for a site.
        
        Args:
            site_id: Site identifier
            user_id: Site owner user ID
            
        Returns:
            Version history
        """
        partition_key = f"user:{user_id}"
        state = await self.persister.load(site_id, partition_key)
        
        if not state:
            return {"success": False, "error": "Site not found"}
        
        return {
            "success": True,
            "history": state.get("version_history", []),
            "publish_log": state.get("publish_log", [])
        }


# ============================================================================
# Conditions for Preview/Publish Workflow
# ============================================================================

@condition
def draft_has_changes(state: State, result: Any) -> bool:
    """Check if draft has changes compared to published."""
    comparison = state.get("comparison_result", {})
    return comparison.get("has_changes", False)


@condition
def has_published_version(state: State, result: Any) -> bool:
    """Check if site has a published version."""
    return state.get("published_version") is not None


@condition
def has_draft_version(state: State, result: Any) -> bool:
    """Check if site has a draft version."""
    return state.get("draft_version") is not None