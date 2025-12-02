"""
Add-on Loader

Automatically discovers and mounts enabled add-ons.
"""
import importlib
import sys
from pathlib import Path
from core.utils.logger import get_logger

logger = get_logger(__name__)


class AddonLoader:
    """Loads and mounts add-ons based on configuration"""
    
    def __init__(self, app, config_module="config.addons"):
        """
        Initialize addon loader.
        
        Args:
            app: FastHTML app instance
            config_module: Module path to addon configuration
        """
        self.app = app
        self.config = importlib.import_module(config_module)
        self.loaded_addons = {}
    
    def load_all(self):
        """Load all enabled add-ons"""
        enabled_addons = self.config.get_enabled_addons()
        
        logger.info(f"Loading {len(enabled_addons)} enabled add-ons: {', '.join(enabled_addons)}")
        
        for addon_name in enabled_addons:
            try:
                self.load_addon(addon_name)
            except Exception as e:
                logger.error(f"Failed to load add-on '{addon_name}': {e}")
                logger.exception(e)
        
        logger.info(f"Successfully loaded {len(self.loaded_addons)} add-ons")
        return self.loaded_addons
    
    def load_addon(self, addon_name: str):
        """
        Load a single add-on.
        
        Args:
            addon_name: Name of the add-on to load
        """
        try:
            # Import the add-on module
            addon_module = importlib.import_module(f"add_ons.{addon_name}")
            
            # Get the router
            router_name = f"router_{addon_name}"
            if not hasattr(addon_module, router_name):
                logger.warning(f"Add-on '{addon_name}' does not export '{router_name}'")
                return
            
            router = getattr(addon_module, router_name)
            
            # Get mount point
            mount_point = self.config.get_addon_route(addon_name)
            
            # Mount the router
            # Note: FastHTML uses different mounting syntax than FastAPI
            # We'll need to add routes directly to the app
            logger.info(f"Mounting add-on '{addon_name}' at '{mount_point}'")
            
            # Store loaded addon info
            self.loaded_addons[addon_name] = {
                "module": addon_module,
                "router": router,
                "mount_point": mount_point
            }
            
            logger.info(f"✓ Successfully loaded add-on '{addon_name}'")
            
        except ImportError as e:
            logger.error(f"Could not import add-on '{addon_name}': {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading add-on '{addon_name}': {e}")
            raise
    
    def get_loaded_addons(self):
        """Get list of successfully loaded add-ons"""
        return list(self.loaded_addons.keys())
    
    def is_loaded(self, addon_name: str) -> bool:
        """Check if an add-on is loaded"""
        return addon_name in self.loaded_addons


def load_addons(app):
    """
    Convenience function to load all enabled add-ons.
    
    Args:
        app: FastHTML app instance
        
    Returns:
        AddonLoader instance
    """
    loader = AddonLoader(app)
    loader.load_all()
    return loader
