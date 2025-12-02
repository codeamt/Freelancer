"""
Add-on Configuration

Control which add-ons are enabled for this project.
Freelancers can easily enable/disable features per client.
"""

# Add-on Registry
# Set to True to enable, False to disable
ENABLED_ADDONS = {
    # Core authentication (recommended for most projects)
    "auth": True,
    
    # Learning Management System
    "lms": True,
    
    # E-commerce / Shop
    "commerce": True,
    
    # Admin dashboard (coming soon)
    "admin": False,
    
    # Media management (coming soon)
    "media": False,
    
    # Social features (coming soon)
    "social": False,
    
    # Analytics (coming soon)
    "analytics": False,
}

# Add-on Dependencies
# If an add-on requires another, it will be auto-enabled
ADDON_DEPENDENCIES = {
    "lms": ["auth"],        # LMS requires auth
    "commerce": ["auth"],   # Commerce requires auth
    "admin": ["auth"],      # Admin requires auth
    "social": ["auth"],     # Social requires auth
}

# Add-on Mount Points
# Where each add-on's routes will be mounted
ADDON_ROUTES = {
    "auth": "/auth",
    "lms": "/lms",
    "commerce": "/shop",
    "admin": "/admin",
    "media": "/media",
    "social": "/social",
    "analytics": "/analytics",
}


def get_enabled_addons():
    """
    Get list of enabled add-ons with dependencies resolved.
    
    Returns:
        List of enabled add-on names
    """
    enabled = set()
    
    # Add explicitly enabled add-ons
    for addon, is_enabled in ENABLED_ADDONS.items():
        if is_enabled:
            enabled.add(addon)
    
    # Resolve dependencies
    changed = True
    while changed:
        changed = False
        for addon in list(enabled):
            if addon in ADDON_DEPENDENCIES:
                for dep in ADDON_DEPENDENCIES[addon]:
                    if dep not in enabled:
                        enabled.add(dep)
                        changed = True
    
    return sorted(list(enabled))


def get_addon_route(addon: str) -> str:
    """Get the mount point for an add-on"""
    return ADDON_ROUTES.get(addon, f"/{addon}")


def is_addon_enabled(addon: str) -> bool:
    """Check if an add-on is enabled"""
    return addon in get_enabled_addons()
