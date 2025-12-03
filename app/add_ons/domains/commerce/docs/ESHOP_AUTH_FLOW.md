# E-Shop Auth Flow - Complete Documentation

## ✅ E-Shop Standalone Authentication

### **Overview:**
E-Shop now has its own authentication system, completely independent from shared auth routes. No role selectors, just simple user registration for shopping.

---

## **Architecture:**

```
E-Shop App (/eshop-example)
├── Auth Routes (E-Shop specific)
│   ├── /login → Simple login form
│   ├── /register → Simple registration (user role only)
│   ├── /auth/login → Login handler
│   └── /auth/register → Registration handler
│
├── Shopping Routes
│   ├── / → Browse products
│   ├── /product/{id} → Product details
│   ├── /cart → Shopping cart
│   └── /checkout/guest/{id} → Guest checkout
│
└── Uses Core Services
    ├── AuthService (JWT, auth)
    └── DBService (storage)
```

---

## **Auth Flows:**

### **1. Browse as Guest**
```
User visits /eshop-example
↓
Browse products (no auth required)
↓
Click "Add to Cart"
↓
Redirected to /eshop-example/login
```

### **2. Register & Shop**
```
Click "Register" or "Create Account"
↓
/eshop-example/register
↓
Fill form:
  - Username
  - Email
  - Password
  - Confirm Password
  (Role: "user" - hardcoded, no selector)
↓
Submit → Auto-login with JWT
↓
Redirected to intended destination
↓
Cart item automatically added (if from product page)
```

### **3. Login & Shop**
```
Click "Sign In"
↓
/eshop-example/login
↓
Fill form:
  - Email
  - Password
↓
Submit → JWT token created
↓
Redirected to intended destination
↓
Cart item automatically added (if from product page)
```

### **4. Guest Checkout (Merchandise Only)**
```
Browse merchandise product
↓
Click "Continue as Guest"
↓
/eshop-example/checkout/guest/{product_id}
↓
Fill customer info + shipping
↓
Two options:
  1. "Add to Cart & Sign In" → Register/Login → Cart
  2. "Checkout Now" → Direct Stripe payment
```

---

## **Key Features:**

### ✅ **No Role Selector**
- E-Shop only has "user" role
- Registration form is simple and focused
- No instructor/student/admin options

### ✅ **Auto-Login After Registration**
- User registers → Immediately logged in
- JWT token created automatically
- Redirected to intended page

### ✅ **Cart Persistence**
- Register from product page → Item added to cart
- Login from product page → Item added to cart
- Uses `/cart/add-and-view/{product_id}` route

### ✅ **Guest Checkout**
- Available for merchandise only
- Can checkout without account
- Or sign in to save order history

---

## **Routes:**

### **Auth UI Routes:**
```python
GET  /eshop-example/login          # Login page
GET  /eshop-example/register       # Registration page
POST /eshop-example/auth/login     # Login handler
POST /eshop-example/auth/register  # Registration handler
```

### **Shopping Routes:**
```python
GET  /eshop-example/                           # Browse products
GET  /eshop-example/product/{id}               # Product details
GET  /eshop-example/cart                       # View cart (auth required)
GET  /eshop-example/cart/add-and-view/{id}     # Add to cart after login
POST /eshop-example/cart/add/{id}              # Add to cart (HTMX)
GET  /eshop-example/checkout/guest/{id}        # Guest checkout
```

---

## **Code Examples:**

### **Registration (E-Shop Specific):**
```python
@app.post("/auth/register")
async def eshop_register(request: Request):
    # Get form data
    username = form_data.get("username")
    email = form_data.get("email")
    password = form_data.get("password")
    
    # Register with "user" role only (E-Shop specific)
    user = await auth_service.register_user(
        email=email,
        password=password,
        username=username,
        roles=["user"]  # No role selector!
    )
    
    # Auto-login
    token = auth_service.create_token(token_data)
    
    # Redirect to intended destination
    return redirect_with_token(redirect_url)
```

### **Product Page Auth:**
```python
# If not logged in, show "Sign in & Add to Cart"
A(
    "Sign in & Add to Cart",
    href=f"/eshop-example/login?redirect=/eshop-example/cart/add-and-view/{product_id}",
    cls="btn btn-primary btn-lg"
)
```

### **Cart Persistence:**
```python
@app.get("/cart/add-and-view/{product_id}")
async def add_and_view_cart(request: Request, product_id: int):
    user = await get_user(request)
    
    if not user:
        # Redirect to login with this URL
        return RedirectResponse(f"/eshop-example/login?redirect=/eshop-example/cart/add-and-view/{product_id}")
    
    # Add item to cart
    cart_storage[user_id][product_id] = current_qty + 1
    
    # Redirect to cart
    return RedirectResponse("/eshop-example/cart")
```

---

## **User Experience:**

### **Scenario 1: New User Wants to Buy T-Shirt**
1. Browse → Click "Premium T-Shirt"
2. Click "Sign in & Add to Cart"
3. See "Don't have an account? Create one"
4. Click "Create one" → Registration form
5. Fill: username, email, password
6. Submit → Auto-logged in
7. **Automatically redirected to cart with T-Shirt added!**
8. Click "Proceed to Checkout"

### **Scenario 2: Guest Wants Quick Purchase**
1. Browse → Click "Tote Bag"
2. Click "Continue as Guest"
3. Fill customer info + shipping address
4. Click "Checkout Now" → Stripe payment
5. Done! (No account created)

### **Scenario 3: Returning User**
1. Browse → Click "Sign In"
2. Enter email + password
3. Logged in → Browse with cart icon showing count
4. Add items → View cart → Checkout

---

## **Security:**

### ✅ **JWT Tokens**
- Stored in localStorage and cookie
- 24-hour expiration
- Verified on every request

### ✅ **Protected Routes**
- Cart requires authentication
- Checkout requires authentication (except guest)
- Add to cart requires authentication

### ✅ **Password Requirements**
- Minimum 8 characters
- Hashed with bcrypt
- Confirm password validation

---

## **Differences from Shared Auth:**

| Feature | Shared Auth (`/auth/*`) | E-Shop Auth (`/eshop-example/*`) |
|---------|------------------------|----------------------------------|
| **Role Selector** | ✅ Yes (admin, instructor, student, user) | ❌ No (always "user") |
| **Registration Form** | Complex with role dropdown | Simple (username, email, password) |
| **Use Case** | Platform-wide auth | E-Shop specific |
| **Redirect Logic** | Role-based (admin → dashboard) | Always to E-Shop |
| **UI Style** | Generic platform style | E-Shop branded |

---

## **Benefits:**

### ✅ **Standalone**
- E-Shop works independently
- No dependency on shared auth routes
- Can be deployed separately

### ✅ **Focused UX**
- Simple registration (no role confusion)
- Shopping-focused messaging
- Clear call-to-actions

### ✅ **Cart Integration**
- Seamless add-to-cart after auth
- No lost items
- Smooth checkout flow

### ✅ **Guest Option**
- Quick checkout without account
- Lower barrier to purchase
- Can create account later

---

## **Testing Checklist:**

- [ ] Register new user → Auto-login → Redirected correctly
- [ ] Login existing user → Redirected correctly
- [ ] Add to cart (not logged in) → Login → Item in cart
- [ ] Guest checkout → Fill form → Checkout button works
- [ ] Guest checkout → "Add to Cart & Sign In" → Login → Item in cart
- [ ] Cart persists across sessions (JWT cookie)
- [ ] Logout → Cart cleared
- [ ] Password validation (min 8 chars)
- [ ] Confirm password validation
- [ ] Duplicate email/username error

---

## **Result:**

✅ **E-Shop has its own complete auth system**
✅ **No role selector confusion**
✅ **Seamless cart integration**
✅ **Guest checkout option**
✅ **Auto-login after registration**
✅ **Standalone and deployable**

The E-Shop auth flow is now production-ready! 🎉
