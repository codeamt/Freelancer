# app/core/addon_loader.py (enhanced)

from typing import List, Dict
from importlib import import_module
from core.services.auth.permissions import permission_registry
from core.ui.state.factory import component_library
from core.utils.logger import get_logger

# from add_ons.domains.lms.manifest import register_lms_addon

logger = get_logger(__name__)


class AddonLoader:
    """Enhanced add-on loader with permission integration"""
    
    def __init__(self):
        self.loaded_addons: Dict[str, Any] = {}
    
    def load_addon(self, domain: str):
        """
        Load an add-on domain.
        
        Args:
            domain: Domain name (e.g., "lms", "commerce")
        """
        try:
            # if domain == "lms":
            #    register_lms_addon()
            # Import manifest
            manifest_module = import_module(f"add_ons.domains.{domain}.manifest")
            manifest = getattr(manifest_module, f"{domain.upper()}_MANIFEST")
            
            # Register roles
            logger.info(f"Registering {len(manifest.roles)} roles for {domain}")
            for role in manifest.roles:
                permission_registry.register_role(role)
            
            # Register components
            if manifest.components:
                logger.info(f"Registering {len(manifest.components)} components for {domain}")
                for comp in manifest.components:
                    component_library.register_addon_component(comp)
            
            # Register theme extensions
            if manifest.theme_extensions:
                logger.info(f"Registering theme extensions for {domain}")
                # Extend theme system with add-on colors/styles
            
            # Load routes (handled separately by route loader)
            
            self.loaded_addons[domain] = manifest
            logger.info(f"✓ Loaded add-on: {manifest.name}")
            
        except Exception as e:
            logger.error(f"Failed to load add-on {domain}: {e}")
    
    def load_all_addons(self):
        """Load all available add-ons"""
        domains = ["lms", "commerce", "social", "stream"]
        for domain in domains:
            self.load_addon(domain)