# Theme Utilities with Aesthetic Switch Support
from starlette.responses import JSONResponse, HTMLResponse

class ThemeUtils:
    @staticmethod
    def switch_theme_mode(theme_context):
        theme = theme_context.switch_mode()
        return JSONResponse({"active_mode": theme_context.mode, "colors": theme.get("color", {})})

    @staticmethod
    def switch_aesthetic_mode(theme_context, mode: str):
        aesthetic = theme_context.set_aesthetic(mode)
        return JSONResponse({"aesthetic_mode": mode, "properties": aesthetic})

    @staticmethod
    def get_css(theme_context):
        css = theme_context.export_css()
        html = f"<style>{css}</style>"
        return HTMLResponse(html, media_type="text/css")

    @staticmethod
    def preview_theme(theme_context):
        theme = theme_context.get()
        colors = theme.get("color", {})
        html = "".join([
            f'<div style="background:{c};padding:1rem;margin:4px;color:white">{name}: {c}</div>'
            for name, c in colors.items()
        ])
        return HTMLResponse(f"<div style='font-family:sans-serif;padding:2rem'>{html}</div>")