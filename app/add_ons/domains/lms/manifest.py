"""
LMS (Learning Management System) Add-on Manifest

Registers:
- Roles (instructor, student, lms_admin)
- Settings (Zoom integration, course limits, etc.)
- Components (course listings, video player, etc.)
- Routes
"""

from dataclasses import dataclass
from typing import List, Dict, Any

from core.services.auth.permissions import Role, Permission
from core.services.settings import (
    SettingDefinition,
    SettingType,
    SettingSensitivity,
    SettingScope,
    register_addon_settings
)
from core.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# LMS Roles
# ============================================================================

LMS_ROLES = [
    Role(
        id="lms_admin",
        name="LMS Administrator",
        description="Full LMS management access",
        permissions=[
            Permission("lms", "*", "*"),           # All LMS operations
            Permission("course", "*", "*"),        # All courses
            Permission("lesson", "*", "*"),        # All lessons
            Permission("student", "*", "*"),       # Manage all students
            Permission("grade", "*", "*"),         # All grading
            Permission("integration", "write", "lms"),  # Configure integrations
        ],
        inherits_from=["admin"],  # Gets admin permissions too
        domain="lms"
    ),
    
    Role(
        id="instructor",
        name="Instructor",
        description="Create and manage courses",
        permissions=[
            Permission("lms", "read", "*"),       # Read LMS settings
            Permission("course", "*", "own"),     # Manage own courses
            Permission("lesson", "*", "own"),     # Manage own lessons
            Permission("student", "read", "*"),   # View all students
            Permission("enrollment", "read", "*"), # View enrollments
            Permission("grade", "*", "own"),      # Grade own courses
        ],
        inherits_from=["member"],
        domain="lms"
    ),
    
    Role(
        id="student",
        name="Student",
        description="Enroll in and take courses",
        permissions=[
            Permission("course", "read", "*"),        # View all courses
            Permission("lesson", "read", "*"),        # View lessons
            Permission("enrollment", "*", "own"),     # Manage own enrollments
            Permission("submission", "*", "own"),     # Submit assignments
            Permission("grade", "read", "own"),       # View own grades
        ],
        inherits_from=["member"],
        domain="lms"
    )
]


# ============================================================================
# LMS Settings
# ============================================================================

LMS_SETTINGS = [
    # Integration settings
    SettingDefinition(
        key="zoom.api_key",  # Will become "lms.zoom.api_key"
        name="Zoom API Key",
        description="API key for Zoom video conferencing integration",
        type=SettingType.ENCRYPTED,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.SECRET,
        category="lms",
        ui_component="password",
        read_permission=("lms", "admin"),
        write_permission=("lms", "admin"),
        placeholder="sk_live_...",
        help_text="Required for creating Zoom meetings from courses"
    ),
    
    SettingDefinition(
        key="zoom.api_secret",
        name="Zoom API Secret",
        description="API secret for Zoom integration",
        type=SettingType.ENCRYPTED,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.SECRET,
        category="lms",
        ui_component="password",
        read_permission=("lms", "admin"),
        write_permission=("lms", "admin"),
        help_text="Keep this secret!"
    ),
    
    SettingDefinition(
        key="zoom.enabled",
        name="Zoom Integration Enabled",
        description="Enable Zoom video conferencing",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=False,
        category="lms",
        read_permission=("lms", "read"),
        write_permission=("lms", "admin")
    ),
    
    # Course limits
    SettingDefinition(
        key="max_students_per_course",
        name="Max Students Per Course",
        description="Maximum number of students allowed per course",
        type=SettingType.INTEGER,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=50,
        category="lms",
        validation=lambda v: 1 <= int(v) <= 1000,
        read_permission=("lms", "read"),
        write_permission=("lms", "admin"),
        help_text="1-1000 students"
    ),
    
    SettingDefinition(
        key="max_courses_per_instructor",
        name="Max Courses Per Instructor",
        description="Maximum number of active courses per instructor",
        type=SettingType.INTEGER,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=10,
        category="lms",
        validation=lambda v: 1 <= int(v) <= 100,
        read_permission=("lms", "read"),
        write_permission=("lms", "admin")
    ),
    
    # Content settings
    SettingDefinition(
        key="video_upload_max_size_mb",
        name="Max Video Upload Size (MB)",
        description="Maximum size for video uploads",
        type=SettingType.INTEGER,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=500,
        category="lms",
        validation=lambda v: 10 <= int(v) <= 5000,
        read_permission=("lms", "read"),
        write_permission=("lms", "admin"),
        help_text="10-5000 MB"
    ),
    
    SettingDefinition(
        key="allowed_video_formats",
        name="Allowed Video Formats",
        description="Comma-separated list of allowed video formats",
        type=SettingType.STRING,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default="mp4,mov,avi,webm",
        category="lms",
        read_permission=("lms", "read"),
        write_permission=("lms", "admin"),
        placeholder="mp4,mov,avi"
    ),
    
    # Certificate settings
    SettingDefinition(
        key="certificates.enabled",
        name="Course Certificates Enabled",
        description="Enable certificate generation for completed courses",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="lms",
        read_permission=("lms", "read"),
        write_permission=("lms", "admin")
    ),
    
    SettingDefinition(
        key="certificates.signature_name",
        name="Certificate Signature Name",
        description="Name to appear on certificates",
        type=SettingType.STRING,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default="Platform Administrator",
        category="lms",
        read_permission=("lms", "read"),
        write_permission=("lms", "admin"),
        placeholder="John Doe, CEO"
    ),
    
    # Grading settings
    SettingDefinition(
        key="grading.passing_score",
        name="Default Passing Score (%)",
        description="Default passing score percentage for courses",
        type=SettingType.INTEGER,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=70,
        category="lms",
        validation=lambda v: 0 <= int(v) <= 100,
        read_permission=("lms", "read"),
        write_permission=("lms", "admin"),
        help_text="0-100%"
    ),
    
    SettingDefinition(
        key="grading.scale",
        name="Grading Scale",
        description="Grading scale type",
        type=SettingType.STRING,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default="percentage",
        category="lms",
        ui_component="select",
        options=["percentage", "letter", "pass_fail", "points"],
        read_permission=("lms", "read"),
        write_permission=("lms", "admin")
    ),
    
    # Notification settings
    SettingDefinition(
        key="notifications.new_enrollment",
        name="Notify on New Enrollment",
        description="Send email to instructor when student enrolls",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="lms",
        read_permission=("lms", "read"),
        write_permission=("lms", "admin")
    ),
    
    SettingDefinition(
        key="notifications.assignment_submitted",
        name="Notify on Assignment Submission",
        description="Send email to instructor when student submits assignment",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="lms",
        read_permission=("lms", "read"),
        write_permission=("lms", "admin")
    )
]


# ============================================================================
# LMS Components
# ============================================================================

LMS_COMPONENTS = [
    {
        "id": "course_listing",
        "name": "Course Listing",
        "type": "content",
        "description": "Display available courses",
        "factory": "lms.components.create_course_listing",
        "category": "lms"
    },
    {
        "id": "course_detail",
        "name": "Course Detail",
        "type": "content",
        "description": "Show course information and lessons",
        "factory": "lms.components.create_course_detail",
        "category": "lms"
    },
    {
        "id": "video_player",
        "name": "Video Player",
        "type": "content",
        "description": "Video lesson player with progress tracking",
        "factory": "lms.components.create_video_player",
        "category": "lms"
    },
    {
        "id": "enrollment_cta",
        "name": "Enrollment CTA",
        "type": "cta",
        "description": "Call-to-action for course enrollment",
        "factory": "lms.components.create_enrollment_cta",
        "category": "lms"
    }
]


# ============================================================================
# LMS Routes
# ============================================================================

LMS_ROUTES = [
    {
        "path": "/courses",
        "handler": "lms.routes.list_courses",
        "methods": ["GET"],
        "permission": ("course", "read")
    },
    {
        "path": "/courses/{course_id}",
        "handler": "lms.routes.get_course",
        "methods": ["GET"],
        "permission": ("course", "read")
    },
    {
        "path": "/courses/{course_id}/edit",
        "handler": "lms.routes.edit_course",
        "methods": ["GET", "POST"],
        "permission": ("course", "update")
    },
    {
        "path": "/courses/{course_id}/students",
        "handler": "lms.routes.course_students",
        "methods": ["GET"],
        "permission": ("student", "read")
    }
]


# ============================================================================
# Theme Extensions
# ============================================================================

LMS_THEME_EXTENSIONS = {
    "colors": {
        "course_primary": "#4f46e5",
        "course_secondary": "#7c3aed",
        "course_success": "#10b981",
        "course_warning": "#f59e0b"
    },
    "components": {
        "course_card": {
            "border_radius": "0.5rem",
            "shadow": "lg",
            "hover_shadow": "xl"
        }
    }
}


# ============================================================================
# Manifest
# ============================================================================

@dataclass
class AddonManifest:
    """Manifest for add-on registration"""
    id: str
    name: str
    version: str
    description: str
    domain: str
    roles: List[Role]
    settings: List[SettingDefinition]
    components: List[Dict[str, Any]]
    routes: List[Dict[str, Any]]
    theme_extensions: Dict[str, Any]


LMS_MANIFEST = AddonManifest(
    id="lms",
    name="Learning Management System",
    version="1.0.0",
    description="Complete LMS with courses, lessons, and grading",
    domain="lms",
    roles=LMS_ROLES,
    settings=LMS_SETTINGS,
    components=LMS_COMPONENTS,
    routes=LMS_ROUTES,
    theme_extensions=LMS_THEME_EXTENSIONS
)


# ============================================================================
# Registration Functions
# ============================================================================

def register_lms_roles():
    """Register LMS roles with permission system"""
    from core.services.auth.permissions import permission_registry
    
    for role in LMS_ROLES:
        permission_registry.register_role(role)
        logger.info(f"Registered LMS role: {role.id}")


def register_lms_settings():
    """Register LMS settings"""
    register_addon_settings("lms", LMS_SETTINGS)
    logger.info(f"Registered {len(LMS_SETTINGS)} LMS settings")


def register_lms_addon():
    """Complete LMS add-on registration"""
    register_lms_roles()
    register_lms_settings()
    # Components and routes would be registered by addon_loader
    logger.info("✓ LMS add-on registered successfully")


# Auto-register when imported
# Comment out if you want manual registration
# register_lms_addon()