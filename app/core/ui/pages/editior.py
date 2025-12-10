from fasthtml.common import *
from monsterui.all import *


def EditorLayout(
    site_id: str,
    session_id: str,
    site_state: Dict,
    theme_state: Dict,
    component_templates: List,
    capabilities: Dict
):
    """Main editor layout with three panels"""
    return Html(
        Head(
            Title("Omniview Editor"),
            Link(rel="stylesheet", href="/static/editor.css"),
            Script(src="/static/editor.js")
        ),
        Body(
            # Top toolbar
            Div(
                # Left: Site name
                Div(
                    H1(site_state.get("site_name", "Untitled"), cls="text-xl font-bold"),
                    cls="flex items-center gap-4"
                ),
                
                # Center: View mode switcher
                Div(
                    ButtonGroup(
                        Button("Structure", id="view-structure", cls="btn-sm"),
                        Button("Theme", id="view-theme", cls="btn-sm"),
                        Button("Preview", id="view-preview", cls="btn-sm"),
                    ),
                    cls="flex-1 flex justify-center"
                ),
                
                # Right: Actions
                Div(
                    Button("Save", id="save-btn", cls="btn btn-sm btn-primary"),
                    Button("Publish", id="publish-btn", cls="btn btn-sm btn-success")
                        if capabilities["can_publish"] else None,
                    cls="flex items-center gap-2"
                ),
                
                cls="flex items-center justify-between p-4 border-b",
                id="editor-toolbar"
            ),
            
            # Main editor area
            Div(
                # Left panel: Structure or Theme
                Div(
                    # Structure panel
                    Div(
                        H2("Structure", cls="text-lg font-bold mb-4"),
                        
                        # Section list
                        Div(
                            *[
                                SectionCard(section)
                                for section in site_state.get("site_graph", {}).get("sections", [])
                            ],
                            id="section-list"
                        ),
                        
                        # Add section button
                        Button(
                            "+ Add Section",
                            cls="btn btn-primary w-full mt-4",
                            hx_post="/api/editor/sections/add",
                            hx_vals=f'{{"session_id": "{session_id}"}}',
                            hx_target="#section-list",
                            hx_swap="beforeend"
                        ) if capabilities["can_edit_structure"] else None,
                        
                        cls="panel",
                        id="structure-panel"
                    ),
                    
                    # Theme panel (hidden initially)
                    Div(
                        H2("Theme", cls="text-lg font-bold mb-4"),
                        
                        # Color pickers
                        Div(
                            H3("Colors", cls="font-bold mb-2"),
                            *[
                                Div(
                                    Label(color_name.replace("_", " ").title(), cls="text-sm"),
                                    Input(
                                        type="color",
                                        name=color_name,
                                        value=theme_state.get("colors", {}).get(color_name, "#000000"),
                                        cls="w-full h-10",
                                        hx_post="/api/editor/theme/colors",
                                        hx_vals=f'{{"session_id": "{session_id}"}}',
                                        hx_trigger="change",
                                        hx_target="#preview-frame"
                                    ),
                                    cls="mb-2"
                                )
                                for color_name in ["primary", "secondary", "accent"]
                            ],
                            cls="mb-6"
                        ),
                        
                        # Theme presets
                        Div(
                            H3("Presets", cls="font-bold mb-2"),
                            Div(
                                *[
                                    Button(
                                        preset.title(),
                                        cls="btn btn-sm btn-outline",
                                        hx_post="/api/editor/theme/preset",
                                        hx_vals=f'{{"session_id": "{session_id}", "preset": "{preset}"}}',
                                        hx_target="#preview-frame"
                                    )
                                    for preset in ["modern", "minimal", "bold", "dark"]
                                ],
                                cls="grid grid-cols-2 gap-2"
                            )
                        ),
                        
                        cls="panel hidden",
                        id="theme-panel"
                    ) if capabilities["can_edit_theme"] else None,
                    
                    cls="w-1/4 border-r p-4 overflow-y-auto"
                ),
                
                # Middle panel: Component library
                Div(
                    H2("Components", cls="text-lg font-bold mb-4"),
                    
                    # Component categories
                    *[
                        ComponentCategory(category, templates)
                        for category, templates in group_templates_by_category(component_templates)
                    ],
                    
                    cls="w-1/4 border-r p-4 overflow-y-auto"
                ),
                
                # Right panel: Preview
                Div(
                    # Preview toolbar
                    Div(
                        ButtonGroup(
                            Button("Anonymous", data_user_type="anonymous", cls="preview-switch btn-sm"),
                            Button("Member", data_user_type="member", cls="preview-switch btn-sm"),
                            Button("Admin", data_user_type="admin", cls="preview-switch btn-sm"),
                        ),
                        cls="mb-2"
                    ),
                    
                    # Preview iframe
                    Iframe(
                        id="preview-frame",
                        src=f"/api/editor/preview/anonymous?session_id={session_id}",
                        cls="w-full h-full border-0"
                    ),
                    
                    cls="flex-1 p-4"
                ),
                
                cls="flex h-[calc(100vh-64px)]"
            ),
            
            # Hidden data
            Script(f"""
                window.EDITOR_SESSION = '{session_id}';
                window.SITE_ID = '{site_id}';
            """),
            
            cls="h-screen overflow-hidden"
        )
    )


def SectionCard(section: Dict):
    """Section card in structure panel"""
    return Card(
        Div(
            H3(section["id"], cls="font-bold"),
            Badge(section["type"], cls="badge-primary"),
            
            # Component count
            P(f"{len(section.get('components', []))} components", cls="text-sm text-gray-600"),
            
            # Actions
            Div(
                Button("Edit", cls="btn-sm"),
                Button("Delete", cls="btn-sm btn-error"),
                cls="flex gap-2 mt-2"
            ),
            
            cls="p-3"
        ),
        cls="mb-2 cursor-pointer hover:shadow-lg",
        onclick=f"selectSection('{section['id']}')"
    )


def ComponentCategory(category: str, templates: List):
    """Component category with templates"""
    return Details(
        Summary(category.title(), cls="font-bold cursor-pointer"),
        Div(
            *[
                ComponentTemplate(template)
                for template in templates
            ],
            cls="grid grid-cols-1 gap-2 mt-2"
        ),
        cls="mb-4"
    )


def ComponentTemplate(template: Dict):
    """Component template card"""
    return Card(
        Div(
            H4(template["name"], cls="font-bold text-sm"),
            P(template.get("description", ""), cls="text-xs text-gray-600"),
            Button(
                "Add",
                cls="btn btn-xs btn-primary mt-2",
                draggable="true",
                data_template_id=template["id"]
            ),
            cls="p-2"
        ),
        cls="cursor-move"
    )