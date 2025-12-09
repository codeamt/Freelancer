"""
Admin workflow for site management.

This module creates pre-built workflows for common admin tasks.
"""

from core.state.builder import SiteStateBuilder
from core.state.actions import (
    InitializeSiteAction,
    AddSectionAction,
    RemoveSectionAction,
    ReorderSectionsAction,
    UpdateThemeAction,
    UpdateSettingsAction,
    PublishSiteAction,
    UnpublishSiteAction,
    ValidateSiteAction
)
from core.state.transitions import (
    on_success,
    on_failure,
    has_validation_errors,
    no_validation_errors,
    is_published,
    is_draft
)
from core.utils.logger import get_logger

logger = get_logger(__name__)


def create_site_creation_workflow():
    """
    Create a workflow for new site creation.
    
    Flow:
    1. Initialize site
    2. Add initial sections
    3. Set theme
    4. Configure settings
    5. Validate
    6. Publish (optional)
    
    Returns:
        StateMachineApplication instance
    """
    # Create actions
    initialize = InitializeSiteAction()
    add_section = AddSectionAction()
    update_theme = UpdateThemeAction()
    update_settings = UpdateSettingsAction()
    validate = ValidateSiteAction()
    publish = PublishSiteAction()
    
    # Build state machine
    app = (
        SiteStateBuilder()
        .with_actions(
            initialize,
            add_section,
            update_theme,
            update_settings,
            validate,
            publish
        )
        .with_transitions(
            ("initialize_site", "add_section", on_success),
            ("add_section", "update_theme", on_success),
            ("update_theme", "update_settings", on_success),
            ("update_settings", "validate", on_success),
        )
        .with_conditional_transitions(
            "validate",
            [
                (no_validation_errors, "publish")
            ],
            default="add_section"  # Go back if validation fails
        )
        .with_entrypoint("initialize_site")
        .build()
    )
    
    return app


def create_site_editing_workflow():
    """
    Create a workflow for editing existing sites.
    
    Flow:
    1. Load site (via initial state)
    2. Make changes (sections, theme, settings)
    3. Validate
    4. Save changes
    
    Returns:
        StateMachineApplication instance
    """
    add_section = AddSectionAction()
    remove_section = RemoveSectionAction()
    reorder = ReorderSectionsAction()
    update_theme = UpdateThemeAction()
    update_settings = UpdateSettingsAction()
    validate = ValidateSiteAction()
    
    app = (
        SiteStateBuilder()
        .with_actions(
            add_section,
            remove_section,
            reorder,
            update_theme,
            update_settings,
            validate
        )
        .with_transitions(
            # All editing actions can transition to validate
            ("add_section", "validate", on_success),
            ("remove_section", "validate", on_success),
            ("reorder_sections", "validate", on_success),
            ("update_theme", "validate", on_success),
            ("update_settings", "validate", on_success),
        )
        .with_entrypoint("add_section")
        .build()
    )
    
    return app


def create_publish_workflow():
    """
    Create a workflow for publishing/unpublishing sites.
    
    Flow:
    1. Validate site
    2. If valid, publish
    3. If invalid, show errors
    
    Returns:
        StateMachineApplication instance
    """
    validate = ValidateSiteAction()
    publish = PublishSiteAction()
    unpublish = UnpublishSiteAction()
    
    app = (
        SiteStateBuilder()
        .with_actions(validate, publish, unpublish)
        .with_conditional_transitions(
            "validate",
            [
                (no_validation_errors, "publish")
            ]
        )
        .with_conditional_transitions(
            "publish",
            [
                (on_success, "unpublish")  # Allow unpublishing after publish
            ]
        )
        .with_entrypoint("validate")
        .build()
    )
    
    return app


class SiteWorkflowManager:
    """
    Manager for site management workflows.
    
    Provides high-level API for common admin operations.
    """
    
    def __init__(self, db_service=None, persister=None):
        """
        Initialize workflow manager.
        
        Args:
            db_service: Database service for additional operations
            persister: State persister for saving/loading state
        """
        self.db = db_service
        self.persister = persister
    
    async def create_new_site(
        self,
        site_name: str,
        initial_sections: list = None,
        theme: dict = None,
        settings: dict = None,
        user_id: str = None
    ) -> dict:
        """
        Create a new site with workflow.
        
        Args:
            site_name: Name of the site
            initial_sections: Optional initial sections
            theme: Optional theme configuration
            settings: Optional settings
            user_id: ID of user creating the site
            
        Returns:
            Dictionary with site_id and final state
        """
        try:
            # Create workflow
            workflow = create_site_creation_workflow()
            
            # Initialize site
            action, result, state = await workflow.step(
                site_name=site_name
            )
            
            if not result.success:
                return {"success": False, "error": result.error}
            
            site_id = state.get("site_id")
            
            # Add initial sections if provided
            if initial_sections:
                for section in initial_sections:
                    action, result, state = await workflow.step(
                        section_id=section.get("id"),
                        section_type=section.get("type"),
                        section_data=section.get("data", {})
                    )
                    
                    if not result.success:
                        logger.warning(f"Failed to add section: {result.error}")
            
            # Update theme if provided
            if theme:
                action, result, state = await workflow.step(
                    theme_updates=theme
                )
            
            # Update settings if provided
            if settings:
                action, result, state = await workflow.step(
                    settings_updates=settings
                )
            
            # Validate
            action, result, state = await workflow.step()
            
            # Save state if persister available
            if self.persister:
                partition_key = f"user:{user_id}" if user_id else None
                await self.persister.save(site_id, state, partition_key)
            
            return {
                "success": True,
                "site_id": site_id,
                "state": state.get_all()
            }
            
        except Exception as e:
            logger.error(f"Error creating site: {e}")
            return {"success": False, "error": str(e)}
    
    async def load_site(
        self,
        site_id: str,
        user_id: str = None
    ) -> dict:
        """
        Load a site's state.
        
        Args:
            site_id: Site identifier
            user_id: Optional user ID for partition
            
        Returns:
            Dictionary with site state or error
        """
        try:
            if not self.persister:
                return {"success": False, "error": "No persister configured"}
            
            partition_key = f"user:{user_id}" if user_id else None
            state = await self.persister.load(site_id, partition_key)
            
            if not state:
                return {"success": False, "error": "Site not found"}
            
            return {
                "success": True,
                "site_id": site_id,
                "state": state.get_all()
            }
            
        except Exception as e:
            logger.error(f"Error loading site: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_site_sections(
        self,
        site_id: str,
        operations: list,
        user_id: str = None
    ) -> dict:
        """
        Update site sections with multiple operations.
        
        Args:
            site_id: Site identifier
            operations: List of operations {"action": "add/remove/reorder", "data": {...}}
            user_id: Optional user ID
            
        Returns:
            Dictionary with updated state or error
        """
        try:
            # Load current state
            site_data = await self.load_site(site_id, user_id)
            if not site_data["success"]:
                return site_data
            
            # Create editing workflow
            workflow = create_site_editing_workflow()
            
            # Apply initial state
            from core.state.state import State
            workflow.state_manager.update(State(site_data["state"]))
            
            # Apply operations
            for op in operations:
                action_name = op.get("action")
                data = op.get("data", {})
                
                if action_name == "add":
                    workflow.current_action = "add_section"
                    action, result, state = await workflow.step(**data)
                elif action_name == "remove":
                    workflow.current_action = "remove_section"
                    action, result, state = await workflow.step(**data)
                elif action_name == "reorder":
                    workflow.current_action = "reorder_sections"
                    action, result, state = await workflow.step(**data)
                
                if not result.success:
                    return {"success": False, "error": result.error}
            
            # Validate
            workflow.current_action = "validate"
            action, result, state = await workflow.step()
            
            # Save state
            if self.persister:
                partition_key = f"user:{user_id}" if user_id else None
                await self.persister.save(site_id, state, partition_key)
            
            return {
                "success": True,
                "site_id": site_id,
                "state": state.get_all()
            }
            
        except Exception as e:
            logger.error(f"Error updating site sections: {e}")
            return {"success": False, "error": str(e)}
    
    async def publish_site(
        self,
        site_id: str,
        user_id: str = None
    ) -> dict:
        """
        Publish a site.
        
        Args:
            site_id: Site identifier
            user_id: Optional user ID
            
        Returns:
            Dictionary with result
        """
        try:
            # Load current state
            site_data = await self.load_site(site_id, user_id)
            if not site_data["success"]:
                return site_data
            
            # Create publish workflow
            workflow = create_publish_workflow()
            
            # Apply initial state
            from core.state.state import State
            workflow.state_manager.update(State(site_data["state"]))
            
            # Run workflow (validate then publish)
            action, result, state = await workflow.run(halt_after=["publish"])
            
            if not result.success:
                return {
                    "success": False,
                    "error": result.error,
                    "validation_errors": state.get("validation_errors", [])
                }
            
            # Save state
            if self.persister:
                partition_key = f"user:{user_id}" if user_id else None
                await self.persister.save(site_id, state, partition_key)
            
            return {
                "success": True,
                "site_id": site_id,
                "status": state.get("status"),
                "published_at": state.get("published_at")
            }
            
        except Exception as e:
            logger.error(f"Error publishing site: {e}")
            return {"success": False, "error": str(e)}
    
    async def list_user_sites(
        self,
        user_id: str
    ) -> dict:
        """
        List all sites for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with list of sites
        """
        try:
            if not self.persister:
                return {"success": False, "error": "No persister configured"}
            
            partition_key = f"user:{user_id}"
            site_ids = await self.persister.list_app_ids(partition_key)
            
            # Load basic info for each site
            sites = []
            for site_id in site_ids:
                state = await self.persister.load(site_id, partition_key)
                if state:
                    sites.append({
                        "site_id": site_id,
                        "site_name": state.get("site_name"),
                        "status": state.get("status"),
                        "created_at": state.get("created_at"),
                        "section_count": len(state.get("site_graph", {}).get("sections", []))
                    })
            
            return {
                "success": True,
                "sites": sites
            }
            
        except Exception as e:
            logger.error(f"Error listing sites: {e}")
            return {"success": False, "error": str(e)}