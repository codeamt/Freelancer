# Extended ThemeContext with Aesthetic Dialect System
import json


class ThemeContext:
    _instance = None
    _initialized = False
    
    def __new__(cls, theme_path: str = "app/core/ui/theme/tokens.json", mode: str = "light", aesthetic: str = "soft"):
        if cls._instance is None:
            cls._instance = super(ThemeContext, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, theme_path: str = "app/core/ui/theme/tokens.json", mode: str = "light", aesthetic: str = "soft"):
        if ThemeContext._initialized:
            return
        
        self.theme_path = theme_path
        self.mode = mode
        self.aesthetic_mode = aesthetic
        self.tokens = self.load_theme(mode)
        self.aesthetic = self.tokens.get("aesthetic", {}).get("options", {}).get(aesthetic, {})
        
        ThemeContext._initialized = True

    def load_theme(self, mode: str = "light"):
        with open(self.theme_path) as f:
            data = json.load(f)
            base = data["modes"].get(mode, data["modes"]["light"])
            base["aesthetic"] = data.get("aesthetic", {})
            return base

    def switch_mode(self):
        self.mode = "dark" if self.mode == "light" else "light"
        self.tokens = self.load_theme(self.mode)
        # Reapply the current aesthetic mode to the new theme
        aesthetics = self.tokens.get("aesthetic", {}).get("options", {})
        if self.aesthetic_mode in aesthetics:
            self.aesthetic = aesthetics[self.aesthetic_mode]
        return self.tokens

    def set_aesthetic(self, mode: str):
        aesthetics = self.tokens.get("aesthetic", {}).get("options", {})
        if mode in aesthetics:
            self.aesthetic_mode = mode
            self.aesthetic = aesthetics[mode]
        return self.aesthetic

    def get_aesthetic(self):
        return self.aesthetic

    def get(self):
        return self.tokens

    def export_css(self) -> str:
        colors = self.tokens.get("color", {})
        fonts = self.tokens.get("font", {})
        css_vars = [f"--color-{k}: {v};" for k, v in colors.items()]
        css_vars += [f"--font-family: {fonts.get('family')};", f"--font-size: {fonts.get('size')};"]
        css_vars += [
            f"--radius:{self.aesthetic.get('radius', '8px')};",
            f"--shadow:{self.aesthetic.get('shadow', 'none')};",
            f"--border:{self.aesthetic.get('border', 'none')};",
        ]
        if 'backdrop' in self.aesthetic:
            css_vars.append(f"--backdrop:{self.aesthetic['backdrop']};")
        return ":root {" + " ".join(css_vars) + "}"