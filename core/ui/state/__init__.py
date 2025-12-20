from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ComponentType(Enum):
    """Types of components available."""
    CTA = "cta"  # Call-to-action buttons/banners
    HEADER = "header"
    FOOTER = "footer"
    FORM = "form"
    HERO = "hero"
    FEATURES = "features"
    TESTIMONIALS = "testimonials"
    PRICING = "pricing"
    GALLERY = "gallery"
    CONTENT = "content"
    NAVIGATION = "navigation"
    CUSTOM = "custom"


class VisibilityCondition(Enum):
    """Visibility conditions for components."""
    ALWAYS = "always"
    AUTHENTICATED = "authenticated"
    NOT_AUTHENTICATED = "not_authenticated"
    HAS_ROLE = "has_role"
    NOT_MEMBER = "not_member"
    IS_MEMBER = "is_member"
    CUSTOM = "custom"


@dataclass
class ComponentConfig:
    """Configuration for a component."""
    id: str
    type: ComponentType
    name: str
    content: Dict[str, Any] = field(default_factory=dict)
    styles: Dict[str, Any] = field(default_factory=dict)
    visibility: VisibilityCondition = VisibilityCondition.ALWAYS
    visibility_params: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    order: int = 0
    
    def should_render(self, user: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if component should render for given user.
        
        Args:
            user: Current user context (None for anonymous)
            
        Returns:
            True if component should be rendered
        """
        if not self.enabled:
            return False
        
        if self.visibility == VisibilityCondition.ALWAYS:
            return True
        
        if self.visibility == VisibilityCondition.AUTHENTICATED:
            return user is not None
        
        if self.visibility == VisibilityCondition.NOT_AUTHENTICATED:
            return user is None
        
        if self.visibility == VisibilityCondition.IS_MEMBER:
            if not user:
                return False
            # Check if user is member of site
            site_id = self.visibility_params.get("site_id")
            user_sites = user.get("member_sites", [])
            return site_id in user_sites
        
        if self.visibility == VisibilityCondition.NOT_MEMBER:
            if not user:
                return True
            site_id = self.visibility_params.get("site_id")
            user_sites = user.get("member_sites", [])
            return site_id not in user_sites
        
        if self.visibility == VisibilityCondition.HAS_ROLE:
            if not user:
                return False
            required_role = self.visibility_params.get("role")
            user_roles = user.get("roles", [])
            return required_role in user_roles
        
        if self.visibility == VisibilityCondition.CUSTOM:
            # Custom logic via callback
            custom_func = self.visibility_params.get("condition_func")
            if custom_func:
                return custom_func(user, self)
            return True
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "content": self.content,
            "styles": self.styles,
            "visibility": self.visibility.value,
            "visibility_params": self.visibility_params,
            "enabled": self.enabled,
            "order": self.order
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComponentConfig":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            type=ComponentType(data["type"]),
            name=data["name"],
            content=data.get("content", {}),
            styles=data.get("styles", {}),
            visibility=VisibilityCondition(data.get("visibility", "always")),
            visibility_params=data.get("visibility_params", {}),
            enabled=data.get("enabled", True),
            order=data.get("order", 0)
        )