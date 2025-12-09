from .__init__ import ComponentConfig, ComponentType, VisibilityCondition

class ComponentLibrary:
    """Library of pre-defined component templates."""
    
    @staticmethod
    def create_signup_cta(component_id: str = "signup-cta") -> ComponentConfig:
        """Create a signup CTA component (hidden for members)."""
        return ComponentConfig(
            id=component_id,
            type=ComponentType.CTA,
            name="Sign Up CTA",
            content={
                "heading": "Join Our Community",
                "text": "Get started with a free account today!",
                "button_text": "Sign Up Now",
                "button_link": "/register",
                "style": "primary"
            },
            styles={
                "background": "gradient",
                "padding": "large",
                "alignment": "center"
            },
            visibility=VisibilityCondition.NOT_MEMBER,
            enabled=True
        )
    
    @staticmethod
    def create_member_dashboard_cta(component_id: str = "dashboard-cta") -> ComponentConfig:
        """Create a dashboard CTA (only for members)."""
        return ComponentConfig(
            id=component_id,
            type=ComponentType.CTA,
            name="Dashboard CTA",
            content={
                "heading": "Welcome Back!",
                "text": "Continue where you left off",
                "button_text": "Go to Dashboard",
                "button_link": "/dashboard",
                "style": "secondary"
            },
            visibility=VisibilityCondition.IS_MEMBER,
            enabled=True
        )
    
    @staticmethod
    def create_admin_only_nav(component_id: str = "admin-nav") -> ComponentConfig:
        """Create admin-only navigation component."""
        return ComponentConfig(
            id=component_id,
            type=ComponentType.NAVIGATION,
            name="Admin Navigation",
            content={
                "items": [
                    {"label": "Dashboard", "link": "/admin"},
                    {"label": "Users", "link": "/admin/users"},
                    {"label": "Sites", "link": "/admin/sites"},
                    {"label": "Settings", "link": "/admin/settings"}
                ]
            },
            visibility=VisibilityCondition.HAS_ROLE,
            visibility_params={"role": "admin"},
            enabled=True
        )
    
    @staticmethod
    def create_contact_form(component_id: str = "contact-form") -> ComponentConfig:
        """Create a contact form component."""
        return ComponentConfig(
            id=component_id,
            type=ComponentType.FORM,
            name="Contact Form",
            content={
                "heading": "Get in Touch",
                "fields": [
                    {"name": "name", "type": "text", "label": "Name", "required": True},
                    {"name": "email", "type": "email", "label": "Email", "required": True},
                    {"name": "message", "type": "textarea", "label": "Message", "required": True}
                ],
                "submit_text": "Send Message",
                "submit_endpoint": "/api/contact"
            },
            visibility=VisibilityCondition.ALWAYS,
            enabled=True
        )
    
    @staticmethod
    def create_hero_banner(component_id: str = "hero-banner") -> ComponentConfig:
        """Create a hero banner component."""
        return ComponentConfig(
            id=component_id,
            type=ComponentType.HERO,
            name="Hero Banner",
            content={
                "heading": "Welcome to Our Site",
                "subheading": "Building amazing experiences",
                "background_image": "/images/hero-bg.jpg",
                "cta_text": "Get Started",
                "cta_link": "/get-started"
            },
            styles={
                "height": "600px",
                "text_color": "white",
                "overlay": "dark"
            },
            visibility=VisibilityCondition.ALWAYS,
            enabled=True
        )