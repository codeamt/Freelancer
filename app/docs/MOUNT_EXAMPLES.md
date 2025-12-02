# Mounting Example Apps

## E-Shop Example

The e-shop example is a complete standalone app that can be mounted at any endpoint.

### In app.py:

```python
from fasthtml.common import *
from monsterui.all import Theme
from core.routes.main import router_main
from examples.eshop import create_eshop_app

# Initialize main app
app, rt = fast_app(
    hdrs=[*Theme.slate.headers()],
)

# Mount core routes (landing pages)
router_main.to_app(app)

# Mount e-shop example at /eshop-example
eshop_app = create_eshop_app()
app.mount("/eshop-example", eshop_app)

# Mount auth routes (required for e-shop)
from add_ons.auth import router_auth
router_auth.to_app(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
```

### Access:
- **Main site**: http://localhost:8000/
- **E-Shop Example**: http://localhost:8000/eshop-example
- **Auth**: http://localhost:8000/auth/login

## Benefits of Separate Example Apps

### 1. Clean Separation
- Example doesn't pollute main codebase
- Easy to show/hide for demos
- Can be removed for production

### 2. Easy Demos
```python
# Show to client:
app.mount("/demo", create_eshop_app())

# Remove after demo:
# app.mount("/demo", create_eshop_app())  # Comment out
```

### 3. Multiple Examples
```python
from examples.eshop import create_eshop_app
from examples.blog import create_blog_app
from examples.portfolio import create_portfolio_app

# Mount multiple examples
app.mount("/eshop-example", create_eshop_app())
app.mount("/blog-example", create_blog_app())
app.mount("/portfolio-example", create_portfolio_app())
```

### 4. Client Customization
```python
# Create custom version for client
from examples.eshop import create_eshop_app

# Customize
eshop = create_eshop_app()
# ... customize products, branding, etc ...

# Mount at client's preferred URL
app.mount("/shop", eshop)  # or /store, /products, etc.
```

## Example App Structure

```
examples/
├── __init__.py
├── eshop/              # E-commerce example
│   ├── __init__.py
│   ├── app.py
│   └── README.md
├── blog/               # Blog example (future)
│   ├── __init__.py
│   ├── app.py
│   └── README.md
└── portfolio/          # Portfolio example (future)
    ├── __init__.py
    ├── app.py
    └── README.md
```

## Creating New Examples

### 1. Create directory:
```bash
mkdir -p app/examples/myexample
```

### 2. Create app.py:
```python
from fasthtml.common import *

def create_myexample_app():
    app = FastHTML()
    
    @app.get("/")
    def home():
        return Div(
            H1("My Example"),
            P("Example content here")
        )
    
    return app
```

### 3. Create __init__.py:
```python
from .app import create_myexample_app
__all__ = ["create_myexample_app"]
```

### 4. Mount in main app:
```python
from examples.myexample import create_myexample_app
app.mount("/myexample", create_myexample_app())
```

## Use Cases

### For Freelancers:
1. **Client Demos** - Show working examples
2. **Templates** - Start new projects from examples
3. **Portfolio** - Showcase capabilities
4. **Rapid Prototyping** - Quick mockups

### For Clients:
1. **See Before Buy** - Try features before committing
2. **Understand Features** - Interactive demos
3. **Customization Preview** - See possibilities
4. **Training** - Learn how to use features

## Navigation Integration

Add example links to your landing page:

```python
# In core/ui/pages/home.py
Div(
    H2("Live Examples", cls="text-2xl font-bold mb-4"),
    Div(
        A(
            Card(
                H3("🛍️ E-Shop Example", cls="font-semibold mb-2"),
                P("One-page commerce with auth", cls="text-sm text-gray-500"),
                cls="p-6 hover:shadow-lg transition-shadow"
            ),
            href="/eshop-example"
        ),
        # Add more example links...
        cls="grid grid-cols-1 md:grid-cols-3 gap-6"
    )
)
```

---

**Current Examples:**
- ✅ E-Shop (One-page commerce)
- ⏳ Blog (Coming soon)
- ⏳ Portfolio (Coming soon)
- ⏳ Dashboard (Coming soon)
