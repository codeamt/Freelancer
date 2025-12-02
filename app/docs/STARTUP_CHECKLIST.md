# Startup Checklist

## Before Running the App

### 1. Check Dependencies
```bash
# Make sure you're in the project directory
cd /Users/annmargarettutu/Documents/GitHub/Freelancer

# Install/update dependencies
pip install fasthtml monsterui python-fasthtml
```

### 2. Run the App
```bash
# From the project root
python -m app.app

# Or with uvicorn directly
uvicorn app.app:app --reload --host 0.0.0.0 --port 8000
```

### 3. Expected Startup Logs
You should see:
```
INFO: ✓ Auth add-on mounted at /auth
INFO: ✓ E-Shop example mounted at /eshop-example
INFO: FastApp started successfully
INFO: Available routes:
INFO:   - / (Home)
INFO:   - /docs (Documentation)
INFO:   - /auth/login (Login)
INFO:   - /auth/register (Register)
INFO:   - /eshop-example (E-Shop Demo)
```

### 4. Test Routes
- **Home**: http://localhost:8000/
- **E-Shop**: http://localhost:8000/eshop-example
- **Login**: http://localhost:8000/auth/login
- **Docs**: http://localhost:8000/docs

## Common Issues

### Issue: "No module named 'add_ons'"
**Solution**: Make sure you're running from the correct directory
```bash
cd /Users/annmargarettutu/Documents/GitHub/Freelancer
python -m app.app
```

### Issue: "No module named 'examples'"
**Solution**: Check that examples directory exists
```bash
ls app/examples/eshop/
# Should show: __init__.py, app.py, README.md
```

### Issue: Icons not showing
**Solution**: MonsterUI includes UIkit icons by default. If you want Lucide icons:
```python
# In app.py, add to headers:
Script(src="https://unpkg.com/lucide@latest")
```

### Issue: 404 on /eshop-example
**Solution**: Make sure the app is mounted correctly
```python
# In app.py, check this line exists:
eshop_app = create_eshop_app()
app.mount("/eshop-example", eshop_app)
```

### Issue: Auth routes not working
**Solution**: Make sure auth add-on is imported
```python
from add_ons.auth import router_auth
router_auth.to_app(app)
```

## Debugging

### Check what's mounted:
```python
# Add to app.py after mounting:
print("Mounted routes:")
for route in app.routes:
    print(f"  {route.path}")
```

### Check imports:
```python
# Test imports individually:
python -c "from examples.eshop import create_eshop_app; print('✓ E-shop OK')"
python -c "from add_ons.auth import router_auth; print('✓ Auth OK')"
python -c "from core.routes.main import router_main; print('✓ Core OK')"
```

## Quick Test

Run this to verify everything is set up:
```bash
cd /Users/annmargarettutu/Documents/GitHub/Freelancer
python -c "
from app.app import app
print('✓ App loaded successfully')
print('Available at: http://localhost:8000')
"
```

Then start the server:
```bash
python -m app.app
```

## What You Should See

When you visit http://localhost:8000/eshop-example:
1. Header: "🛍️ E-Shop Example"
2. User status (logged in or not)
3. 6 product cards with images
4. Shopping cart section
5. Features section at bottom

If you see a 404, check:
- Server is running
- URL is exactly `/eshop-example` (with hyphen)
- No errors in terminal logs
