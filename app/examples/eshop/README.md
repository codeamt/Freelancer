# E-Shop Example - One-Page Commerce Application

A complete, standalone e-commerce shop example demonstrating auth integration and modern web features.

## Features

- ✅ **Public Product Browsing** - Anyone can view products
- ✅ **Auth-Protected Cart** - Must login to add items
- ✅ **Secure Checkout** - Authentication required
- ✅ **Modern UI** - MonsterUI + Tailwind CSS
- ✅ **HTMX Integration** - Dynamic cart updates
- ✅ **Responsive Design** - Mobile-friendly
- ✅ **Ready to Customize** - Perfect template for clients

## Quick Start

### 1. Mount in app.py

```python
from examples.eshop import create_eshop_app

# Create the e-shop app
eshop_app = create_eshop_app()

# Mount at /eshop-example
app.mount("/eshop-example", eshop_app)
```

### 2. Access

Visit: **http://localhost:8000/eshop-example**

## User Flow

### Without Authentication:
1. Browse products ✓
2. Click "Add to Cart" → Prompted to sign in
3. Click "Sign In" → Redirected to login
4. After login → Redirected back to shop

### With Authentication:
1. Browse products ✓
2. Click "Add to Cart" → Item added to cart ✓
3. View cart with items and total ✓
4. Click "Proceed to Checkout" → Checkout process ✓

## Sample Products

The example includes 6 sample products:
- Python Mastery Course - $49.99
- Web Development Bootcamp - $79.99
- Data Science Fundamentals - $99.99
- Mobile App Development - $89.99
- UI/UX Design Masterclass - $69.99
- DevOps Engineering - $109.99

## Customization for Clients

### 1. Replace Products

Edit `PRODUCTS` in `app.py`:

```python
PRODUCTS = [
    {
        "id": 1,
        "name": "Your Product",
        "description": "Product description",
        "price": 99.99,
        "image": "https://your-image-url.com",
        "category": "Category"
    },
    # Add more products...
]
```

### 2. Add Real Payment Processing

Replace the mock checkout with Stripe:

```python
import stripe

@app.post("/checkout/process")
async def process_checkout(request: Request):
    user = await get_current_user(request)
    
    # Create Stripe payment intent
    intent = stripe.PaymentIntent.create(
        amount=int(cart_total * 100),  # Amount in cents
        currency="usd",
        customer=user.get("stripe_customer_id")
    )
    
    return {"client_secret": intent.client_secret}
```

### 3. Add Database Storage

Replace in-memory cart with database:

```python
# Instead of:
cart_storage = {}

# Use:
async def get_cart(user_id: str):
    return await db.find_many("cart_items", {"user_id": user_id})

async def add_to_cart(user_id: str, product_id: int):
    await db.insert_one("cart_items", {
        "user_id": user_id,
        "product_id": product_id,
        "added_at": datetime.utcnow()
    })
```

### 4. Add Product Categories

```python
@app.get("/category/{category}")
async def category_page(category: str):
    products = [p for p in PRODUCTS if p["category"] == category]
    # Render category page...
```

### 5. Add Search

```python
@app.get("/search")
async def search_products(q: str):
    results = [p for p in PRODUCTS if q.lower() in p["name"].lower()]
    # Render search results...
```

## Integration with Other Add-ons

### With LMS:
- After purchase → Enroll user in course
- Link products to courses
- Show "My Courses" after purchase

### With Auth:
- User accounts for orders
- Order history in profile
- Saved payment methods

### With Admin:
- Manage products
- View orders
- Customer management

## Tech Stack

- **FastHTML** - Python web framework
- **MonsterUI** - UI components
- **Tailwind CSS** - Styling
- **HTMX** - Dynamic updates
- **UIkit Icons** - Icons

## File Structure

```
examples/eshop/
├── __init__.py          # Package init
├── app.py               # Main application
└── README.md            # This file
```

## Deployment

### Development:
```bash
python -m app.app
# Visit http://localhost:8000/eshop-example
```

### Production:
```bash
gunicorn app.app:app --workers 4 --bind 0.0.0.0:8000
```

## Client Pricing Example

- **Base E-Shop**: $500
  - Product catalog
  - Shopping cart
  - Basic checkout
  
- **+ Payment Integration**: $300
  - Stripe integration
  - Order processing
  - Email receipts
  
- **+ Advanced Features**: $400
  - Product search
  - Categories/filters
  - Inventory management
  - Order history

**Total**: $1,200 for complete e-commerce solution

## Support

This is a template/example. Customize for your client's needs:
- Change branding/colors
- Add client's products
- Integrate payment processor
- Add shipping options
- Customize checkout flow

## License

Part of FastApp - Use freely for client projects

---

**Perfect for**: Freelance e-commerce projects, course sales, digital products, service bookings
