"""
Workflow Management System - app/core/workflows/__init__.py

High-level workflow orchestration for site management operations.

This module provides:
- Admin workflows (site creation, editing)
- Preview and publishing workflows
- Site management utilities

Usage:
    from core.workflows import SiteWorkflowManager, PreviewPublishManager
    
    # Create and manage sites
    manager = SiteWorkflowManager(persister=persister)
    site = await manager.create_new_site("My Site", user_id="admin")
    
    # Preview and publish
    preview_mgr = PreviewPublishManager(persister=persister)
    await preview_mgr.publish_draft(site_id, user_id)
"""

from .admin import (
    SiteWorkflowManager,
    create_site_creation_workflow,
    create_site_editing_workflow,
    create_publish_workflow,
)

from .preview import (
    PreviewPublishManager,
    CreateDraftFromPublishedAction,
    PublishDraftAction,
    RollbackToVersionAction,
    CompareDraftToPublishedAction,
    GeneratePreviewAction,
    SiteVersion,
)

__all__ = [
    # Admin Workflows
    "SiteWorkflowManager",
    "create_site_creation_workflow",
    "create_site_editing_workflow",
    "create_publish_workflow",
    
    # Preview & Publishing
    "PreviewPublishManager",
    "CreateDraftFromPublishedAction",
    "PublishDraftAction",
    "RollbackToVersionAction",
    "CompareDraftToPublishedAction",
    "GeneratePreviewAction",
    "SiteVersion",
]

__doc__ += """

Submodules:
-----------

admin.py    - Site creation, editing, management workflows
preview.py  - Preview generation, publishing, version control

Workflow Types:
---------------

1. Site Creation Workflow
   Initialize → Add Sections → Set Theme → Configure → Validate → Publish

2. Site Editing Workflow
   Load → Edit (sections/theme/settings) → Validate → Save

3. Publishing Workflow
   Validate → Compare → Publish → Archive Previous Version

4. Rollback Workflow
   Load Version History → Select Version → Restore

Examples:
---------

1. Create a new site:
    >>> from core.workflows import SiteWorkflowManager
    >>> manager = SiteWorkflowManager(persister=persister)
    >>> result = await manager.create_new_site(
    ...     site_name="My Site",
    ...     initial_sections=[
    ...         {"id": "hero", "type": "hero"},
    ...         {"id": "about", "type": "about"}
    ...     ],
    ...     theme={"theme": "modern"},
    ...     user_id="user_123"
    ... )

2. Publish a site:
    >>> from core.workflows import PreviewPublishManager
    >>> preview_mgr = PreviewPublishManager(persister=persister)
    >>> 
    >>> # Preview first
    >>> preview = await preview_mgr.generate_preview(
    ...     site_id="site_123",
    ...     user_context=current_user,
    ...     user_id="user_123"
    ... )
    >>> 
    >>> # Then publish
    >>> result = await preview_mgr.publish_draft(
    ...     site_id="site_123",
    ...     user_id="user_123"
    ... )

3. Rollback to previous version:
    >>> rollback_result = await preview_mgr.rollback_to_version(
    ...     site_id="site_123",
    ...     version_number=1,
    ...     user_id="user_123"
    ... )

4. Compare draft vs published:
    >>> comparison = await preview_mgr.compare_versions(
    ...     site_id="site_123",
    ...     user_id="user_123"
    ... )
    >>> if comparison["comparison"]["has_changes"]:
    ...     print("Draft has unpublished changes")
"""