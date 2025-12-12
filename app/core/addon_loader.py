"""
Add-on Loader - Consolidated configuration and loading system.

Manages add-on registration using manifest.py files from each domain.
Handles:
- Add-on configuration (enabled/disabled)
- Dependency resolution
- Manifest loading and registration
- Roles, settings, components, routes, and theme extensions
"""

from typing import List, Dict, Any, Optional, Set
from importlib import import_module
from dataclasses import dataclass
from core.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Add-on Configuration
# ============================================================================

# Add-on Registry - Set to True to enable, False to disable
ENABLED_ADDONS = {
    "lms": True,           # Learning Management System
    "commerce": True,      # E-commerce / Shop
    "social": False,       # Social networking (coming soon)
    "stream": False,       # Streaming platform (coming soon)
    "analytics": False,    # Analytics (coming soon)
    "media": False,        # Media management (coming soon)
}

# Add-on Dependencies - Auto-enable required add-ons
ADDON_DEPENDENCIES = {
    "lms": [],
    "commerce": [],
    "social": [],
    "stream": [],
}

# Add-on Mount Points - Where routes will be mounted
ADDON_ROUTES = {
    "lms": "/lms",
    "commerce": "/shop",
    "social": "/social",
    "stream": "/stream",
    "analytics": "/analytics",
    "media": "/media",
}


# ============================================================================
# Configuration Helpers
# ============================================================================

def get_enabled_addons() -> List[str]:
    """
    Get list of enabled add-ons with dependencies resolved.
    
    Returns:
        Sorted list of enabled add-on names
    """
    enabled: Set[str] = set()
    
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
                        logger.info(f"Auto-enabled dependency: {dep} (required by {addon})")
    
    return sorted(list(enabled))


def get_addon_route(addon: str) -> str:
    """Get the mount point for an add-on."""
    return ADDON_ROUTES.get(addon, f"/{addon}")


def is_addon_enabled(addon: str) -> bool:
    """Check if an add-on is enabled."""
    return addon in get_enabled_addons()


# ============================================================================
# Add-on Loader
# ============================================================================

class AddonLoader:
    """
    Enhanced add-on loader with manifest-based registration.
    
    Loads add-ons from add_ons/domains/{domain}/manifest.py and registers:
    - Roles and permissions
    - Settings
    - UI components
    - Routes
    - Theme extensions
    """
    
    def __init__(self):
        """Initialize addon loader."""
        self.loaded_addons: Dict[str, Any] = {}
        self._registered_roles: Set[str] = set()
        self._registered_components: Set[str] = set()
    
    def load_addon(self, domain: str) -> bool:
        """
        Load an add-on domain from its manifest.
        
        Args:
            domain: Domain name (e.g., "lms", "commerce")
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            logger.info(f"Loading add-on: {domain}")
            
            # Import manifest
            manifest_module = import_module(f"add_ons.domains.{domain}.manifest")
            manifest = getattr(manifest_module, f"{domain.upper()}_MANIFEST")
            
            # Register roles
            if manifest.roles:
                self._register_roles(domain, manifest.roles)
            
            # Register settings
            if manifest.settings:
                self._register_settings(domain, manifest.settings)
            
            # Register components
            if manifest.components:
                self._register_components(domain, manifest.components)
            
            # Register routes (handled by route loader)
            if manifest.routes:
                logger.info(f"  {len(manifest.routes)} routes available for {domain}")
            
            # Register theme extensions
            if manifest.theme_extensions:
                self._register_theme_extensions(domain, manifest.theme_extensions)
            
            # Store loaded manifest
            self.loaded_addons[domain] = manifest
            logger.info(f"✓ Successfully loaded add-on: {manifest.name} v{manifest.version}")
            return True
            
        except ImportError as e:
            logger.warning(f"Could not import manifest for {domain}: {e}")
            return False
        except AttributeError as e:
            logger.error(f"Manifest format error for {domain}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to load add-on {domain}: {e}", exc_info=True)
            return False
    
    def _register_roles(self, domain: str, roles: List[Any]):
        """Register roles with permission system."""
        try:
            from core.services.auth.permissions import permission_registry
            
            for role in roles:
                if role.id not in self._registered_roles:
                    permission_registry.register_role(role)
                    self._registered_roles.add(role.id)
                    logger.info(f"  Registered role: {role.id}")
            
            logger.info(f"  Registered {len(roles)} roles for {domain}")
        except Exception as e:
            logger.error(f"Failed to register roles for {domain}: {e}")
    
    def _register_settings(self, domain: str, settings: List[Any]):
        """Register settings with settings system."""
        try:
            from core.services.settings import register_addon_settings
            
            register_addon_settings(domain, settings)
            logger.info(f"  Registered {len(settings)} settings for {domain}")
        except Exception as e:
            logger.error(f"Failed to register settings for {domain}: {e}")
    
    def _register_components(self, domain: str, components: List[Dict[str, Any]]):
        """Register UI components with component library."""
        try:
            from core.ui.state.factory import component_library
            
            for comp in components:
                comp_id = comp.get("id")
                if comp_id and comp_id not in self._registered_components:
                    component_library.register_addon_component(comp)
                    self._registered_components.add(comp_id)
            
            logger.info(f"  Registered {len(components)} components for {domain}")
        except Exception as e:
            logger.error(f"Failed to register components for {domain}: {e}")
    
    def _register_theme_extensions(self, domain: str, theme_extensions: Dict[str, Any]):
        """Register theme extensions."""
        try:
            # TODO: Integrate with theme system
            # For now, just log that theme extensions are available
            if "colors" in theme_extensions:
                logger.info(f"  Theme colors available for {domain}")
            if "components" in theme_extensions:
                logger.info(f"  Theme component styles available for {domain}")
        except Exception as e:
            logger.error(f"Failed to register theme extensions for {domain}: {e}")
    
    def load_enabled_addons(self) -> Dict[str, bool]:
        """
        Load all enabled add-ons based on configuration.
        
        Returns:
            Dictionary of addon_name -> success status
        """
        enabled = get_enabled_addons()
        results = {}
        
        logger.info(f"Loading {len(enabled)} enabled add-ons: {', '.join(enabled)}")
        
        for addon in enabled:
            results[addon] = self.load_addon(addon)
        
        successful = sum(1 for success in results.values() if success)
        logger.info(f"\n{'='*60}")
        logger.info(f"Add-on loading complete: {successful}/{len(enabled)} successful")
        logger.info(f"{'='*60}\n")
        
        return results
    
    def get_loaded_addon(self, domain: str) -> Optional[Any]:
        """Get loaded manifest for a domain."""
        return self.loaded_addons.get(domain)
    
    def get_addon_routes(self, domain: str) -> List[Dict[str, Any]]:
        """Get routes for a loaded add-on."""
        manifest = self.get_loaded_addon(domain)
        return manifest.routes if manifest else []
    
    def get_all_routes(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all routes from all loaded add-ons."""
        return {
            domain: manifest.routes
            for domain, manifest in self.loaded_addons.items()
            if manifest.routes
        }


# ============================================================================
# Global Loader Instance
# ============================================================================

# Singleton instance
_addon_loader: Optional[AddonLoader] = None


def get_addon_loader() -> AddonLoader:
    """Get or create the global addon loader instance."""
    global _addon_loader
    if _addon_loader is None:
        _addon_loader = AddonLoader()
    return _addon_loader


def load_all_addons() -> Dict[str, bool]:
    """Convenience function to load all enabled add-ons."""
    loader = get_addon_loader()
    return loader.load_enabled_addons()